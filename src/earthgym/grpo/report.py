"""Report of a GRPO run from the kernel's metrics.json (decision 0024).

uv run python -m earthgym.grpo.report <metrics.json> --name <name> --out reports/grpo/<file>.md
"""

import argparse
import datetime as dt
import json
import math
import statistics
from pathlib import Path

from earthgym import samples


def curve(log_history: list[dict]) -> list[dict]:
    """The trainer's per-step log entries: the ones that carry a reward."""
    return [x for x in log_history if "reward" in x]


def training(metrics: dict, window: int = 25) -> dict:
    """The train reward over the first and the last `window` steps, the steps whose 8
    completions all earned the same reward (no signal to learn from), the mean share of
    completions cut at the cap, and the median step time past the first step's warmup."""
    steps = curve(metrics["log_history"])
    rewards = [s["reward"] for s in steps]
    return {
        "steps": len(steps),
        "first": statistics.fmean(rewards[:window]),
        "last": statistics.fmean(rewards[-window:]),
        "no_signal": sum(s.get("frac_reward_zero_std") == 1.0 for s in steps),
        "clipped": statistics.fmean(s.get("completions/clipped_ratio", 0.0) for s in steps),
        "step_seconds": statistics.median(s["step_time"] for s in steps[1:]),
    }


def sign_test(up: int, down: int) -> float:
    """The exact two-sided sign test on the items that moved: the doubled smaller binomial
    tail at one half, capped at 1."""
    n = up + down
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(up, down) + 1)) / 2**n)


def compare(before: list[dict], after: list[dict]) -> dict:
    """One split sampled before and after training: each side's multi-sample summary
    (earthgym.samples), the items whose mean reward rose, fell or stayed, the sign test on
    them, and the replies cut at the cap after training."""
    a, b = samples.by_item(before), samples.by_item(after)
    if set(a) != set(b):
        raise ValueError("the two samplings are not of the same items")
    moved = [statistics.fmean(b[i]) - statistics.fmean(a[i]) for i in a]
    up, down = sum(m > 0 for m in moved), sum(m < 0 for m in moved)
    return {
        "items": len(a),
        "before": samples.summary(before),
        "after": samples.summary(after),
        "better": up,
        "worse": down,
        "same": len(moved) - up - down,
        "p": sign_test(up, down),
        "cut_before": sum(r["cut"] for r in before),
        "cut_after": sum(r["cut"] for r in after),
    }


def _event(metrics: dict, name: str) -> dict:
    return next((e for e in metrics["events"] if e["event"] == name), {})


def render(metrics: dict, name: str, date: str, window: int = 25) -> str:
    c, t = metrics["config"], training(metrics, window)
    k = c["eval_samples"]
    versions = ", ".join(f"{p} {v}" for p, v in metrics["versions"].items() if v)
    lines = [
        f"# GRPO on climaqa-v1 MCQ: {name}",
        "",
        f"Dated {date} (decision 0024). `{c['model']}` at {c['revision']} with a LoRA of rank "
        f"{c['lora_rank']}, trained for {c['steps']} steps of one train-split prompt and its "
        f"{c['num_generations']} completions, learning rate {c['learning_rate']:g}, at most "
        f"{c['max_completion_length']} completion tokens, sampled at temperature "
        f"{c['temperature']:g}, top_p {c['top_p']:g}, top_k {c['top_k']}, seed {c['seed']}.",
        "",
        f"- Packages: {versions}.",
        f"- GPU: {'; '.join(_event(metrics, 'installed').get('gpu', 'UNKNOWN').splitlines())}; "
        "peak memory in training "
        f"{_event(metrics, 'trained').get('peak_gib', 'UNKNOWN')} GiB.",
        f"- Wall time: {metrics['events'][-1]['seconds']:.0f} s from the start of the script to "
        f"its last record ({metrics['events'][-1]['event']}).",
        "",
        "## Train reward",
        "",
        f"Mean reward {t['first']:.3f} over the first {min(window, t['steps'])} steps and "
        f"{t['last']:.3f} over the last {min(window, t['steps'])}. {t['no_signal']} of "
        f"{t['steps']} steps had the same reward on all {c['num_generations']} completions, so "
        f"gave no signal; on average {t['clipped']:.3f} of the completions were cut at the cap. "
        f"Median step {t['step_seconds']:.1f} s after the first.",
        "",
    ]
    steps = curve(metrics["log_history"])
    block = 1 if len(steps) <= 30 else 10
    lines += [
        f"| step{'s' if block > 1 else ''} | reward | steps with no signal | cut share | seconds |",
        "|---|---|---|---|---|",
    ]
    for start in range(0, len(steps), block):
        part = steps[start : start + block]
        span = f"{part[0]['step']}" if block == 1 else f"{part[0]['step']}-{part[-1]['step']}"
        lines.append(
            f"| {span} | {statistics.fmean(s['reward'] for s in part):.3f} | "
            f"{sum(s.get('frac_reward_zero_std') == 1.0 for s in part)} | "
            f"{statistics.fmean(s.get('completions/clipped_ratio', 0.0) for s in part):.3f} | "
            f"{sum(s.get('step_time', 0.0) for s in part):.0f} |"
        )
    lines += [
        "",
        "## Before and after training",
        "",
        f"Each item sampled {k} times with the same settings, scored by the environment's own "
        "contract.",
        "",
        f"| split | items | when | mean reward | items whose reward varies | pass@1 | pass@{k} | "
        "replies cut |",
        "|---|---|---|---|---|---|---|---|",
    ]
    moves = []
    for split in metrics["eval"].get("before", {}):
        if split not in metrics["eval"].get("after", {}):
            continue
        cmp = compare(metrics["eval"]["before"][split], metrics["eval"]["after"][split])
        for when in ("before", "after"):
            s = cmp[when]
            lines.append(
                f"| {split} | {cmp['items']} | {when} | {s['mean_reward']:.3f} | "
                f"{s['varies']:.3f} | {s['pass@1']:.3f} | {s[f'pass@{k}']:.3f} | "
                f"{cmp[f'cut_{when}']} |"
            )
        moves.append(
            f"- {split}: {cmp['better']} items better, {cmp['worse']} worse, {cmp['same']} the "
            f"same (two-sided sign test p {cmp['p']:.3f})."
        )
    lines += ["", *moves]
    return "\n".join([*lines, ""])


def main() -> None:
    parser = argparse.ArgumentParser(description="Report a GRPO run from its metrics.json.")
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--window", type=int, default=25)
    args = parser.parse_args()
    metrics = json.loads(args.metrics.read_text("utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(metrics, args.name, args.date, args.window), "utf-8")
    print(f"report written to {args.out}")


if __name__ == "__main__":
    main()
