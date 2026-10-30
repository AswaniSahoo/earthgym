"""Clean evaluation set: validated Gold MCQ and cloze items without leaks, defects or giveaways.

uv run python -m rlenv.climaqa.clean
"""

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from rlenv.climaqa import audit, checks, data

TASKS = ("mcq", "cloze")  # freeform needs a judge, so it waits for a later phase
VERSION = "v1"
SEED = 20261030
LETTERS = "ABCD"
BUNDLE = Path("environments/climaqa_v1/climaqa_v1")
# Flags that also exclude: the question gives the answer away, or "all/none of the above"
# loses its meaning once options are shuffled.
EXCLUDING_FLAGS = {"mcq.answer_in_question", "cloze.answer_in_question", "mcq.all_or_none_of_above"}


def clean(rows: dict, report: dict) -> tuple[list[dict], list[dict]]:
    """Keep validated Gold items with no excluding finding; log each exclusion with its reasons."""
    blocked: dict[tuple[str, str], set[str]] = {}
    for f in report["findings"]:
        if f["kind"] == "defect" or f["check"] in EXCLUDING_FLAGS:
            blocked.setdefault((f["split"], f["item"]), set()).add(f["check"])
    kept, excluded = [], []
    for task in TASKS:
        split = f"gold/{task}"
        for row in rows["gold", task]:
            reasons = set(blocked.get((split, row["id"]), ()))
            if row.get("Validation") == "False":
                reasons.add("rejected by experts")
            if reasons:
                excluded.append({"id": f"{split}/{row['id']}", "reasons": sorted(reasons)})
            else:
                kept.append(record(row, task))
    return kept, excluded


def record(row: dict, task: str) -> dict:
    rec = {
        "id": f"gold/{task}/{row['id']}",
        "task": task,
        "question": row["Question"],
        "complexity": row.get("Complexity", ""),
    }
    if task == "mcq":
        options = [text for _, text in checks.parse_options(row["Options"])]
        key_text = options["abcd".index(row["Answer"].strip().lower())]
        # Shuffled once here, seeded by the item id, so every harness shows the same order.
        random.Random(f"{SEED}:{rec['id']}").shuffle(options)
        rec["options"] = options
        rec["answer"] = LETTERS[options.index(key_text)]
    else:
        rec["answer"] = row["Answer"].strip().rstrip(".,;:")  # 12 Gold keys end in "," or "."
    return rec


def serialize(kept: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept)


def manifest(kept: list[dict], excluded: list[dict], text: str) -> dict:
    reasons = Counter(reason for entry in excluded for reason in entry["reasons"])
    return {
        "dataset": data.REPO,
        "revision": data.REVISION,
        "version": VERSION,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "kept": dict(sorted(Counter(r["task"] for r in kept).items())),
        "excluded_by_reason": dict(sorted(reasons.items())),
        "excluded": excluded,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the clean ClimaQA evaluation set.")
    parser.add_argument("--cache", type=Path, default=Path("data/climaqa"))
    parser.add_argument("--out", type=Path, default=BUNDLE)
    parser.add_argument("--reports", type=Path, default=Path("reports/climaqa"))
    args = parser.parse_args()
    rows = data.load_all(args.cache)
    kept, excluded = clean(rows, audit.audit(rows))
    text = serialize(kept)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"climaqa_clean_{VERSION}.jsonl").write_text(text, "utf-8")
    summary = json.dumps(manifest(kept, excluded, text), indent=1, ensure_ascii=False)
    (args.reports / f"clean_{VERSION}_manifest.json").write_text(summary, "utf-8")
    print(f"kept {len(kept)}, excluded {len(excluded)}")


if __name__ == "__main__":
    main()
