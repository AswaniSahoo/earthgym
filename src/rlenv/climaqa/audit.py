"""Run the ClimaQA checks and write findings.json, SUMMARY.md and two hand-check sheets.

uv run python -m rlenv.climaqa.audit --cache data/climaqa --out reports/climaqa
"""

import argparse
import csv
import json
import random
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from rlenv.climaqa import checks, data

TASKS = ("mcq", "cloze", "ffq")
SEED = 20261030
SAMPLE_PER_COMPLEXITY = 10

# arXiv 2410.16701v2, dataset statistics table: (inventory field, expected value) per split.
PAPER = {
    "gold/mcq": ("validated_complexity", {"BASE": 126, "REASONING": 72, "HYPOTHETICAL": 47}),
    "gold/ffq": ("validated_complexity", {"BASE": 54, "REASONING": 52, "HYPOTHETICAL": 55}),
    "gold/cloze": ("rows", 160),
    "silver/mcq": ("complexity", {"BASE": 501, "REASONING": 264, "HYPOTHETICAL": 235}),
    "silver/ffq": ("complexity", {"BASE": 507, "REASONING": 241, "HYPOTHETICAL": 252}),
    "silver/cloze": ("rows", 1000),
}


def audit(rows: dict[tuple[str, str], list[dict]]) -> dict:
    """All checks on loaded rows; no file or network access."""
    inventory, findings = {}, []
    for (config, task), items in rows.items():
        split = f"{config}/{task}"
        inventory[split] = checks.summarize(items, task)
        findings += checks.duplicates(items, split, compare_answers=task != "ffq")
        if task == "mcq":
            findings += checks.mcq(items, split)
        if task == "cloze":
            findings += checks.cloze(items, split)

    silver = {t: [r | {"split": f"silver/{t}"} for r in rows["silver", t]] for t in TASKS}
    every_silver = [r for t in TASKS for r in silver[t]]
    for task in TASKS:
        gold, split = rows["gold", task], f"gold/{task}"
        others = [r for t in TASKS if t != task for r in silver[t]]
        findings += checks.overlap(gold, silver[task], split)
        findings += checks.overlap(
            gold, others, split, check="leak.gold_in_other_silver_task", compare=False
        )
        findings += checks.near_overlap(gold, every_silver, split)

    rejected = {
        f"gold/{t}": {r["id"] for r in rows["gold", t] if r.get("Validation") == "False"}
        for t in TASKS
    }
    return {
        "dataset": data.REPO,
        "revision": data.REVISION,
        "inventory": inventory,
        "findings": [
            asdict(f)
            | {"kind": checks.kind(f.check), "rejected": f.item in rejected.get(f.split, ())}
            for f in findings
        ],
    }


def run(cache: Path, out: Path) -> dict:
    rows = {key: data.load(path) for key, path in data.fetch(cache).items()}
    report = audit(rows)
    out.mkdir(parents=True, exist_ok=True)
    (out / "findings.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), "utf-8")
    (out / "SUMMARY.md").write_text(render(report), "utf-8")
    write_once(out / "review_sample.csv", *sample_sheet(rows["gold", "mcq"]))
    write_once(out / "leak_review.csv", *leak_sheet(report, rows))
    return report


def render(report: dict) -> str:
    def fmt(value) -> str:
        return (
            ", ".join(f"{k} {v}" for k, v in sorted(value.items()))
            if isinstance(value, dict)
            else str(value)
        )

    lines = [
        "# ClimaQA audit",
        "",
        f"Dataset `{report['dataset']}` at revision `{report['revision']}`.",
        "",
        "## Inventory",
        "",
        "| split | rows | validation | complexity |",
        "|---|---|---|---|",
    ]
    for split, s in report["inventory"].items():
        validation, complexity = fmt(s.get("validation", "")), fmt(s.get("complexity", ""))
        lines.append(f"| {split} | {s['rows']} | {validation} | {complexity} |")
    lines += [
        "",
        "## Paper check",
        "",
        "| split | field | paper | released file | match |",
        "|---|---|---|---|---|",
    ]
    for split, (field, expected) in PAPER.items():
        got = report["inventory"].get(split, {}).get(field)
        lines.append(
            f"| {split} | {field} | {fmt(expected)} | {fmt(got or '')} | {got == expected} |"
        )

    totals = Counter((f["check"], f["kind"], f["split"]) for f in report["findings"])
    rejected = Counter((f["check"], f["split"]) for f in report["findings"] if f["rejected"])
    lines += [
        "",
        "## Findings",
        "",
        "| check | kind | split | items | of which Validation=False |",
        "|---|---|---|---|---|",
    ]
    for (check, kind, split), n in sorted(totals.items()):
        lines.append(f"| {check} | {kind} | {split} | {n} | {rejected[check, split]} |")
    lines += [
        "",
        "Leak counts are exact matches after case and whitespace folding, so they are a lower",
        "bound; reworded copies appear as leak.near_match flags for a human to judge.",
        "Item-level detail: findings.json. Hand-check sheets: review_sample.csv, leak_review.csv.",
        "",
    ]
    return "\n".join(lines)


def sample_sheet(rows: list[dict]) -> tuple[list[str], list[list[str]]]:
    """Stratified sample of validated Gold MCQ items for the human hand-check."""
    rng = random.Random(SEED)
    by_level: dict[str, list[dict]] = {}
    for row in rows:
        if row.get("Validation") == "True":
            by_level.setdefault(row["Complexity"], []).append(row)
    picked = [
        [r["id"], level, r["Question"], r["Options"], r["Answer"], "", ""]
        for level in sorted(by_level)
        for r in rng.sample(by_level[level], min(SAMPLE_PER_COMPLEXITY, len(by_level[level])))
    ]
    return ["id", "complexity", "question", "options", "answer", "verdict", "note"], picked


def leak_sheet(report: dict, rows: dict) -> tuple[list[str], list[list[str]]]:
    """Gold and Silver side by side for every leak a human must confirm."""
    by_ref = {f"{c}/{t}:{r['id']}": r for (c, t), items in rows.items() for r in items}
    picked = []
    for f in report["findings"]:
        needs_eyes = f["check"] in {"leak.near_match", "leak.gold_in_other_silver_task"}
        if not (needs_eyes or f["detail"] == "answer text differs"):
            continue
        gold = by_ref[f"{f['split']}:{f['item']}"]
        for ref in f["refs"]:
            other = by_ref[ref]
            picked.append(
                [
                    f["check"],
                    f"{f['split']}:{f['item']}",
                    gold["Question"],
                    checks.answer_text(gold),
                    ref,
                    other["Question"],
                    checks.answer_text(other),
                    "",
                    "",
                ]
            )
    header = [
        "check",
        "gold",
        "gold_question",
        "gold_answer",
        "silver",
        "silver_question",
        "silver_answer",
        "verdict",
        "note",
    ]
    return header, picked


def write_once(path: Path, header: list[str], rows: list[list[str]]) -> None:
    """Write a hand-check sheet unless one exists, so a re-run never erases human verdicts."""
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the pinned ClimaQA benchmark.")
    parser.add_argument("--cache", type=Path, default=Path("data/climaqa"))
    parser.add_argument("--out", type=Path, default=Path("reports/climaqa"))
    args = parser.parse_args()
    report = run(args.cache, args.out)
    print(f"{len(report['findings'])} findings written to {args.out}")


if __name__ == "__main__":
    main()
