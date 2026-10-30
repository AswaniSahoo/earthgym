"""Clean evaluation set: validated Gold MCQ and cloze items without leaks or defects.

uv run python -m rlenv.climaqa.clean
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from rlenv.climaqa import audit, checks, data

TASKS = ("mcq", "cloze")  # freeform needs a judge, so it waits for a later phase
VERSION = "v0"


def clean(rows: dict, report: dict) -> tuple[list[dict], list[dict]]:
    """Keep validated Gold items with no defect finding; log each exclusion with its reasons."""
    defects: dict[tuple[str, str], set[str]] = {}
    for f in report["findings"]:
        if f["kind"] == "defect":
            defects.setdefault((f["split"], f["item"]), set()).add(f["check"])
    kept, excluded = [], []
    for task in TASKS:
        split = f"gold/{task}"
        for row in rows["gold", task]:
            reasons = set(defects.get((split, row["id"]), ()))
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
        rec["options"] = [text for _, text in checks.parse_options(row["Options"])]
        rec["answer"] = row["Answer"].strip().upper()  # Inspect keys choices by capital letter
    else:
        rec["answer"] = row["Answer"].strip().rstrip(".,;:")  # 12 Gold keys end in "," or "."
    return rec


def manifest(kept: list[dict], excluded: list[dict]) -> dict:
    reasons = Counter(reason for entry in excluded for reason in entry["reasons"])
    return {
        "dataset": data.REPO,
        "revision": data.REVISION,
        "version": VERSION,
        "kept": dict(sorted(Counter(r["task"] for r in kept).items())),
        "excluded_by_reason": dict(sorted(reasons.items())),
        "excluded": excluded,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the clean ClimaQA evaluation set.")
    parser.add_argument("--cache", type=Path, default=Path("data/climaqa"))
    parser.add_argument("--out", type=Path, default=Path("data/clean"))
    parser.add_argument("--reports", type=Path, default=Path("reports/climaqa"))
    args = parser.parse_args()
    rows = data.load_all(args.cache)
    kept, excluded = clean(rows, audit.audit(rows))
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / f"climaqa_{VERSION}.jsonl").open("w", encoding="utf-8") as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in kept)
    summary = json.dumps(manifest(kept, excluded), indent=1, ensure_ascii=False)
    (args.reports / f"clean_{VERSION}_manifest.json").write_text(summary, "utf-8")
    print(f"kept {len(kept)}, excluded {len(excluded)}")


if __name__ == "__main__":
    main()
