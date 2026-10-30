"""Dated markdown report from Inspect eval logs.

uv run python -m rlenv.climaqa.report <log dir> --out reports/climaqa/runs/<name>.md
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log
from inspect_ai.scorer import CORRECT


def summarize(log: EvalLog) -> dict:
    by_level: dict[str, list[bool]] = defaultdict(list)
    format_failures = 0
    for sample in log.samples or []:
        score = next(iter(sample.scores.values()))
        by_level[sample.metadata.get("complexity") or "none"].append(score.value == CORRECT)
        if sample.metadata.get("task") == "mcq" and not score.answer:
            format_failures += 1  # no clean 'ANSWER: X' line
    metrics = log.results.scores[0].metrics
    rev = log.eval.revision
    # eval-level settings override the model's own, as in Model._resolve_config
    config = log.eval.model_generate_config.merge(log.plan.config).model_dump(exclude_none=True)
    usage = log.stats.model_usage.values()
    return {
        "task": log.eval.task.split("/")[-1],
        "model": log.eval.model,
        "created": log.eval.created,
        "n": len(log.samples or []),
        "accuracy": metrics["accuracy"].value,
        "stderr": metrics["stderr"].value,
        "format_failures": format_failures,
        "by_complexity": {k: sum(v) / len(v) for k, v in sorted(by_level.items())},
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


def render(summaries: list[dict], set_sha256: str) -> str:
    lines = [
        "# ClimaQA baseline",
        "",
        f"Clean set v1, sha256 `{set_sha256}`, scored by climaqa_v1/contract.py.",
        "",
        "| task | model | n | accuracy | stderr | format failures |",
        "|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['task']} | {s['model']} | {s['n']} | {s['accuracy']:.3f} | "
            f"{s['stderr']:.3f} | {s['format_failures']} |"
        )
    lines += [
        "",
        "## Accuracy by complexity",
        "",
        "| task | complexity | accuracy |",
        "|---|---|---|",
    ]
    for s in summaries:
        lines += [f"| {s['task']} | {k} | {v:.3f} |" for k, v in s["by_complexity"].items()]
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
    runs = ", ".join(f"{s['task']} at {s['created']}" for s in summaries)
    lines += [
        "",
        f"Runs: {runs}. inspect_ai {summaries[0]['inspect_ai'] if summaries else ''}.",
        "",
    ]
    return "\n".join(lines)


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
    args.out.write_text(render(summaries, sha256), "utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(summaries, indent=1, default=str), "utf-8")
    print(f"{len(summaries)} runs written to {args.out}")


if __name__ == "__main__":
    main()
