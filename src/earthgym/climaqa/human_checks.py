"""The two ClimaQA hand checks as sheets a person fills in, under docs/human-checks/: 30
validated Gold MCQ items (is the key right?) and 56 Gold and Silver pairs (is it the same
item?). Each sheet is written once and never overwritten, so a filled verdict is never lost.

uv run python -m earthgym.climaqa.human_checks
"""

import argparse
import csv
from pathlib import Path

from earthgym.climaqa.audit import write_once

SAMPLE_IN = Path("reports/climaqa/review_sample.csv")
LEAKS_IN = Path("reports/climaqa/leak_review.csv")
OUT = Path("docs/human-checks")
DIVIDER = "\n--------------------\n"  # between the options in review_sample.csv


def sample_sheet(rows: list[dict]) -> tuple[list[str], list[list[str]]]:
    """One row per item: the question, its options, the keyed option spelled out."""
    out = []
    for r in rows:
        options = r["options"].split(DIVIDER)
        key = next(o for o in options if o.startswith(f"{r['answer']})"))
        out.append([r["id"], r["question"], "\n".join(options), key, "", ""])
    return ["id", "question", "options", "gold_answer", "verdict", "note"], out


def leak_sheet(rows: list[dict]) -> tuple[list[str], list[list[str]]]:
    """One row per pair: the Gold item, and the Silver item it may copy."""
    header = ["id", "question", "gold_answer", "silver_id", "silver_question", "silver_answer"]
    out = [
        [r["gold"], r["gold_question"], r["gold_answer"], r["silver"], r["silver_question"]]
        + [r["silver_answer"], "", ""]
        for r in rows
    ]
    return [*header, "verdict", "note"], out


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    argparse.ArgumentParser(description="Write the ClimaQA hand-check sheets once.").parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    write_once(OUT / "climaqa-sample.csv", *sample_sheet(read(SAMPLE_IN)))
    write_once(OUT / "leak-pairs.csv", *leak_sheet(read(LEAKS_IN)))
    print(f"sheets in {OUT}")


if __name__ == "__main__":
    main()
