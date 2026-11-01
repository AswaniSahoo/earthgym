"""Expert review sheet for clean set v2 (decision 0005): the flagged items, with the columns
only the expert fills. Model answers are Gemini 3.8 Flash's, from the 2026-10-30 miss notes;
every item not in a note was answered with its key.

uv run python -m rlenv.climaqa.expert_sheet   # writes reports/climaqa/expert_review_v2.csv once
"""

import argparse
import csv
import random
from pathlib import Path

from climaqa_v1 import contract
from climaqa_v1.taskset import records

NOTES = {
    "mcq": Path("reports/climaqa/runs/2026-10-30-gemini-3.8-flash-mcq-misses.md"),
    "cloze": Path("reports/climaqa/runs/2026-10-30-gemini-3.8-flash-cloze-misses.md"),
}
EXTRAS = {  # baseline review M4 (docs/reviews/phase-2-climaqa-port.md), kept items that were hits
    "gold/mcq/56": "tests the source document (baseline review M4)",
    "gold/mcq/215": "tests the source document (baseline review M4)",
}
VERBATIM = {  # logged replies a note writes with a hyphen, to keep its prose free of dashes
    "gold/cloze/37": "Aerosol\u2013cloud",
}
SHEET = Path("reports/climaqa/expert_review_v2.csv")
SEED, HITS = 20261030, 20  # only misses were read, so the expert also sees a sample of hits
COLUMNS = ["id", "task", "question", "options", "key", "model_answer", "flag", "our_note"]
COLUMNS += ["verdict", "accepted_answers", "expert_note"]


def note_rows(text: str, task: str) -> list[tuple[str, str, str, str]]:
    """(id, model answer, bucket, note) from the item table of a miss note."""
    out = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split(" | ")]
        if cells[0].isdigit():
            out.append((f"gold/{task}/{cells[0]}", cells[-3], cells[-2], cells[-1]))
    return out


def _shown(record: dict, letter: str) -> str:
    return f"{letter}) {record['options'][contract.LETTERS.index(letter)]}"


def _row(record: dict, answer: str | None, flag: str, note: str) -> dict:
    mcq = record["task"] == "mcq"
    key = _shown(record, record["answer"]) if mcq else record["answer"]
    if answer is None:
        answer = key  # not a miss, so the model gave the key
    elif mcq:
        answer = _shown(record, answer)
    options = "\n".join(_shown(record, letter) for letter in contract.LETTERS) if mcq else ""
    return {"id": record["id"], "task": record["task"], "question": record["question"]} | {
        "options": options,
        "key": key,
        "model_answer": answer,
        "flag": flag,
        "our_note": note,
        "verdict": "",
        "accepted_answers": "",
        "expert_note": "",
    }


def sheet(
    rows: list[dict], flags: list[tuple], extras: dict, hits: int = HITS, seed: int = SEED
) -> list[dict]:
    """The flagged items, then the extras, then a seeded sample of the other items."""
    by_id = {r["id"]: r for r in rows}
    entries = [(i, VERBATIM.get(i, answer), flag, note) for i, answer, flag, note in flags]
    entries += [(i, None, "kept, flagged by review", n) for i, n in extras.items()]
    flagged = {entry[0] for entry in entries}
    pool = [r["id"] for r in rows if r["id"] not in flagged]
    entries += [(i, None, "sampled hit", "") for i in random.Random(seed).sample(pool, hits)]
    return [_row(by_id[i], answer, flag, note) for i, answer, flag, note in entries]


def write_once(rows: list[dict], path: Path = SHEET) -> bool:
    """Write the sheet unless one exists: the expert's verdicts must never be overwritten."""
    if path.exists():
        return False
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return True


def main() -> None:
    argparse.ArgumentParser(description="Write the expert review sheet once.").parse_args()
    flags = [row for task, path in NOTES.items() for row in note_rows(path.read_text(), task)]
    out = sheet(records(), flags, EXTRAS)
    done = write_once(out)
    print(f"{len(out)} rows {'written to' if done else 'not written; kept the existing'} {SHEET}")


if __name__ == "__main__":
    main()
