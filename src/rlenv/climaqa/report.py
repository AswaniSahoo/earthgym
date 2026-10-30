"""Dated markdown report from Inspect eval logs.

uv run python -m rlenv.climaqa.report <log dir> --out reports/climaqa/runs/<name>.md
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path

from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log
from inspect_ai.scorer import CORRECT

OPTION = re.compile(r"^([A-D])\) (.*)$", re.MULTILINE)  # option lines of contract.mcq_prompt


def summarize(log: EvalLog) -> dict:
    by_level: dict[str, list[bool]] = defaultdict(list)
    format_failures, key_longest, mcq = 0, 0, False
    letters: Counter[str] = Counter()
    for sample in log.samples or []:
        score = next(iter(sample.scores.values()))
        by_level[sample.metadata.get("complexity") or "none"].append(score.value == CORRECT)
        if sample.metadata.get("task") == "mcq":
            mcq = True
            format_failures += not score.answer  # no clean 'ANSWER: X' line
            letters[sample.target] += 1
            options = dict(OPTION.findall(str(sample.input)))
            key = options.pop(sample.target, "")
            key_longest += all(len(key) > len(text) for text in options.values())
    metrics = log.results.scores[0].metrics
    rev = log.eval.revision
    # eval-level settings override the model's own, as in Model._resolve_config
    config = log.eval.model_generate_config.merge(log.plan.config).model_dump(exclude_none=True)
    usage = log.stats.model_usage.values()
    return {
        "task": log.eval.task.split("/")[-1],
        "model": log.eval.model,
        "created": log.eval.created,
        "started": log.stats.started_at,
        "completed": log.stats.completed_at,
        "n": len(log.samples or []),
        "accuracy": metrics["accuracy"].value,
        "stderr": metrics["stderr"].value,
        "format_failures": format_failures if mcq else None,  # only MCQ has an answer format
        "letters": {k: letters[k] for k in "ABCD"} if mcq else None,
        "key_longest": key_longest if mcq else None,
        "by_complexity": {
            k: {"n": len(v), "accuracy": sum(v) / len(v)} for k, v in sorted(by_level.items())
        },
        "inspect_ai": log.eval.packages.get("inspect_ai", ""),
        "commit": f"{rev.commit}{' (dirty)' if rev.dirty else ''}" if rev else "unknown",
        "generate_config": ", ".join(f"{k} {v}" for k, v in config.items()) or "provider defaults",
        "tokens": {
            "input": sum(u.input_tokens for u in usage),
            "output": sum(u.output_tokens for u in usage),
            "reasoning": sum(u.reasoning_tokens or 0 for u in usage),
        },
        "log": Path(log.location).name,
    }


def render(
    summaries: list[dict], set_sha256: str, notes: Sequence[str] = (), log_dir: str = ""
) -> str:
    lines = [
        "# ClimaQA baseline",
        "",
        f"Clean set v1, sha256 `{set_sha256}`, scored by climaqa_v1/contract.py.",
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
    summaries = [summarize(log) for log in logs if log.status == "success"]
    sha256 = json.loads(args.manifest.read_text())["sha256"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    notes = sorted(p.name for p in args.out.parent.glob(f"{args.out.stem}-*misses.md"))
    args.out.write_text(render(summaries, sha256, notes, str(args.log_dir)), "utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(summaries, indent=1, default=str), "utf-8")
    print(f"{len(summaries)} runs written to {args.out}")


if __name__ == "__main__":
    main()
