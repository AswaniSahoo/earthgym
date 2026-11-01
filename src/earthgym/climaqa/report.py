"""Dated markdown report from Inspect eval logs.

uv run python -m earthgym.climaqa.report <log dir> --out reports/climaqa/runs/<name>.md
"""

import argparse
import json
import re
import statistics
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from climaqa_v1 import contract
from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log

from earthgym import results

OPTION = re.compile(r"^([A-D])\) (.*)$", re.MULTILINE)  # option lines of contract.mcq_prompt


def rows(log: EvalLog) -> list[dict]:
    """The run's per-item results (earthgym.results), with what the reports read from each
    sample: its complexity; for MCQ the key and whether it is the longest option; for cloze the
    reply's line count and whether its last line alone is right."""
    out = []
    for s in log.samples or []:
        r = results.row(s) | {"complexity": s.metadata.get("complexity") or "none"}
        if s.metadata.get("task") == "mcq":
            options = dict(OPTION.findall(str(s.input)))
            key = options.pop(s.target, "")
            longest = all(len(key) > len(text) for text in options.values())
            r |= {"key": s.target, "key_longest": longest}
        else:
            lines = s.output.completion.strip().splitlines()
            right = bool(lines) and contract.cloze_correct(lines[-1], s.target)
            r |= {"lines": len(lines), "last_line_right": right}
        out.append(r)
    return out


def summarize(log: EvalLog) -> dict:
    return from_results(results.header(log), rows(log))


def from_results(head: dict, rows: list[dict]) -> dict:
    """The summary of a run from its per-item results, read from a log or from the committed
    file (earthgym.results)."""
    by_level: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        by_level[r["complexity"]].append(r["reward"] == 1.0)
    mcq = [r for r in rows if "key" in r]
    rewards = [r["reward"] for r in rows]
    t, settings = head["tokens"], head["settings"]
    return {
        "task": head["task"],
        "model": head["model"],
        "created": head["created"],
        "started": head["started"],
        "completed": head["completed"],
        "n": len(rows),
        "accuracy": statistics.fmean(rewards),
        "stderr": statistics.stdev(rewards) / len(rewards) ** 0.5,
        "format_failures": sum(not r["answer"] for r in mcq) if mcq else None,
        "letters": {k: sum(r["key"] == k for r in mcq) for k in "ABCD"} if mcq else None,
        "key_longest": sum(r["key_longest"] for r in mcq) if mcq else None,
        "by_complexity": {
            k: {"n": len(v), "accuracy": sum(v) / len(v)} for k, v in sorted(by_level.items())
        },
        "inspect_ai": head["inspect_ai"],
        "commit": head["commit"],
        "generate_config": ", ".join(f"{k} {v}" for k, v in settings.items())
        or "provider defaults",
        "tokens": {k: t[k] for k in ("input", "output", "reasoning")},
        "log": head["log"],
    }


def render(
    summaries: list[dict], set_sha256: str, notes: Sequence[str] = (), log_dir: str = ""
) -> str:
    lines = [
        "# ClimaQA baseline",
        "",
        f"Clean set v1 (exact-overlap-filtered; 21 near matches of Silver unresolved), sha256 "
        f"`{set_sha256}`, scored by climaqa_v1/contract.py.",
        "",
        "| task | model | n | accuracy | stderr | format failures |",
        "|---|---|---|---|---|---|",
    ]
    for s in summaries:
        fails = "n/a" if s["format_failures"] is None else s["format_failures"]
        lines.append(
            f"| {s['task']} | {s['model']} | {s['n']} | {s['accuracy']:.3f} | "
            f"{s['stderr']:.3f} | {fails} |"
        )
    lines += [
        "",
        "## Accuracy by complexity",
        "",
        "| task | complexity | n | accuracy |",
        "|---|---|---|---|",
    ]
    for s in summaries:
        lines += [
            f"| {s['task']} | {k} | {v['n']} | {v['accuracy']:.3f} |"
            for k, v in s["by_complexity"].items()
        ]
    lines += [
        "",
        "## Run config",
        "",
        "Prompts and scoring rules: climaqa_v1/contract.py at the commit shown. "
        "Tokens out include reasoning tokens.",
        "",
        "| task | commit | generate config | tokens in | tokens out | reasoning | log |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        t = s["tokens"]
        lines.append(
            f"| {s['task']} | {s['commit']} | {s['generate_config']} | {t['input']} | "
            f"{t['output']} | {t['reasoning']} | {s['log']} |"
        )
    lines += ["", "## Limits", ""]
    if any(s["commit"].endswith("(dirty)") for s in summaries):
        lines.append("- The tree had uncommitted changes at run time; their contents are unknown.")
    if any(s["generate_config"] == "provider defaults" for s in summaries):
        lines.append(
            "- Sampling settings were the provider's defaults (no temperature, seed or max "
            "tokens set), so a rerun need not match."
        )
    lines.append(
        "- Clean set v1 keeps 21 Gold items that are near matches of Silver "
        "(leak.near_match in reports/climaqa/findings.json)."
    )
    if any(s["task"].endswith("cloze") for s in summaries):
        lines.append("- Cloze counts exact matches only, ignoring case, punctuation and articles.")
    for s in summaries:
        if s["letters"]:
            counts = ", ".join(f"{k} {v}" for k, v in s["letters"].items())
            lines.append(
                f"- {s['task']} keys: {counts}; the key is the strictly longest option in "
                f"{s['key_longest']} of {s['n']} items."
            )
    lines += [f"- Miss analysis: [{note}]({note})" for note in notes]
    runs = ", ".join(f"{s['task']} from {s['started']} to {s['completed']}" for s in summaries)
    lines += ["", f"Runs: {runs}. inspect_ai {summaries[0]['inspect_ai'] if summaries else ''}."]
    if log_dir:
        lines.append(f"Logs: `{log_dir}` (not in git).")
    return "\n".join([*lines, ""])


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a markdown report from eval logs.")
    parser.add_argument("log_dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--manifest", type=Path, default=Path("reports/climaqa/clean_v1_manifest.json")
    )
    args = parser.parse_args()
    logs = [read_eval_log(info) for info in list_eval_logs(str(args.log_dir))]
    summaries = sorted(
        (summarize(log) for log in logs if log.status == "success"), key=lambda s: s["task"]
    )
    sha256 = json.loads(args.manifest.read_text())["sha256"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    notes = sorted(p.name for p in args.out.parent.glob(f"{args.out.stem}-*misses.md"))
    args.out.write_text(render(summaries, sha256, notes, str(args.log_dir)), "utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(summaries, indent=1, default=str), "utf-8")
    print(f"{len(summaries)} runs written to {args.out}")


if __name__ == "__main__":
    main()
