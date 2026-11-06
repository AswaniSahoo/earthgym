"""What several samples per item say about an environment's training signal (decision 0022):
the mean reward, the share of items whose reward varies across the samples (an item where every
sample earns the same reward gives a GRPO-style update nothing to compare), and pass@1 against
pass@k."""

import argparse
import statistics
from math import comb
from pathlib import Path

from climaqa_v1.taskset import near_matches

from earthgym import results


def pass_at_k(n: int, c: int, k: int) -> float:
    """The unbiased pass@k for one item: n samples, c of them passing (Chen et al. 2021)."""
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def by_item(rows: list[dict]) -> dict[str, list[float]]:
    """Each item's rewards, an errored sample counted as 0."""
    out: dict[str, list[float]] = {}
    for r in rows:
        out.setdefault(r["id"], []).append(0.0 if r.get("error") else r["reward"])
    return out


def summary(rows: list[dict], passed=lambda reward: reward == 1.0, k: int | None = None) -> dict:
    """Mean reward, share of items whose reward varies, pass@1 and pass@k (k: the samples per
    item); `passed` says when a sample counts as a pass."""
    items = by_item(rows)
    counts = {len(v) for v in items.values()}
    if len(counts) != 1:
        raise ValueError(f"every item needs the same number of samples, not {sorted(counts)}")
    n = counts.pop()
    k = n if k is None else k
    hits = [sum(map(passed, v)) for v in items.values()]
    return {
        "items": len(items),
        "samples": n,
        "mean_reward": statistics.fmean(r for v in items.values() for r in v),
        "varies": statistics.fmean(min(v) != max(v) for v in items.values()),
        "pass@1": statistics.fmean(pass_at_k(n, c, 1) for c in hits),
        f"pass@{k}": statistics.fmean(pass_at_k(n, c, k) for c in hits),
    }


def finished(head: dict, rows: list[dict]) -> tuple[list[dict], int]:
    """A run's rows and how many items were left out: a run that stopped early (a status in its
    header) never finished its errored samples, so they say nothing of the model."""
    if not head.get("status"):
        return rows, 0
    cut = {r["id"] for r in rows if r.get("error")}
    return [r for r in rows if r["id"] not in cut], len(cut)


def passes(env: str):
    """When a sample counts as a pass: ERA5's reward is continuous, so a forecast passes when it
    beats the better of persistence and climatology; elsewhere the answer must be right."""
    return (lambda reward: reward > 0) if env == "era5" else (lambda reward: reward == 1.0)


def group(item_id: str) -> str:
    """The question (IBTrACS, heat), the variable (ERA5) or the task (ClimaQA) of an item."""
    parts = item_id.split("/")
    return parts[1] if parts[0] in ("gold", "silver") else parts[0]


def _row(cells: list) -> str:
    return "| " + " | ".join(f"{c:.3f}" if isinstance(c, float) else str(c) for c in cells) + " |"


def render(
    env: str, runs: list[tuple[dict, list[dict]]], date: str, strict: set | None = None
) -> str:
    """One environment's multi-sample runs side by side, then per question; for ClimaQA,
    `strict` holds the near matches of Silver that the strict variant leaves out."""
    passed = passes(env)
    rule = "a reward above 0" if env == "era5" else "reward 1"
    stats = [(head, summary(rows, passed)) for head, rows in runs]
    k = stats[0][1]["samples"]
    cols = (
        f"| model | items | samples | mean reward | items whose reward varies | pass@1 | pass@{k} |"
    )
    lines = [
        f"# {env}: small open models, {k} samples per item",
        "",
        f"Dated {date}. Each item answered {k} times by each model; a sample passes at {rule}. An",
        "item whose reward varies across its samples is one a GRPO-style update can learn from",
        "(decision 0022).",
        "",
        "Drawn with llama.cpp on Kaggle's T4 GPUs (decisions 0022 and 0025).",
        "",
        cols,
        "|---|---|---|---|---|---|---|",
    ]
    for head, s in stats:
        cells = [head["model"], s["items"], s["samples"], s["mean_reward"], s["varies"]]
        lines.append(_row([*cells, s["pass@1"], s[f"pass@{k}"]]))
    if strict:
        lines += ["", "## Strict variant: the near matches of Silver left out", "", cols]
        lines.append("|---|---|---|---|---|---|---|")
        for head, rows in runs:
            s = summary([r for r in rows if r["id"] not in strict], passed)
            cells = [head["model"], s["items"], s["samples"], s["mean_reward"], s["varies"]]
            lines.append(_row([*cells, s["pass@1"], s[f"pass@{k}"]]))
    lines += ["", "## Per question", "", cols.replace("| model |", "| model | question |")]
    lines.append("|---|---|---|---|---|---|---|---|")
    for head, rows in runs:
        for g in sorted({group(r["id"]) for r in rows}):
            s = summary([r for r in rows if group(r["id"]) == g], passed)
            cells = [head["model"], g, s["items"], s["samples"], s["mean_reward"], s["varies"]]
            lines.append(_row([*cells, s["pass@1"], s[f"pass@{k}"]]))
    lines += ["", "## Settings and cost", ""]
    for head, rows in runs:
        settings = ", ".join(f"{a} {b}" for a, b in head.get("settings", {}).items()) or "none"
        out = sum(r["tokens"][3] for r in rows if "tokens" in r)
        cap = head.get("settings", {}).get("max_tokens")
        capped = sum(r["tokens"][3] >= cap for r in rows if cap and "tokens" in r)
        cut = f" {capped} of {len(rows)} replies stopped at the {cap}-token cap;" if cap else ""
        lines.append(
            f"- {head['model']}: {settings}; {len(rows)} samples, {out} output tokens, from "
            f"{head.get('started')} to {head.get('completed')} (UTC).{cut} "
            f"{sum(not r.get('answer') for r in rows)} had no parseable answer and score 0."
            + (
                f" {head['left_out']} items left out: a session's deadline stopped a sample of "
                "each before it finished."
                if head.get("left_out")
                else ""
            )
        )
    return "\n".join([*lines, ""])


def main() -> None:
    parser = argparse.ArgumentParser(description="Report multi-sample runs of one environment.")
    parser.add_argument("env")
    parser.add_argument("results", nargs="+", help="per-item results files, any number per model")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    runs: dict[str, tuple[dict, list[dict]]] = {}
    for path in args.results:
        head, rows = results.read(Path(path))
        merged, kept = runs.setdefault(head["model"], (dict(head), []))
        rows, unfinished = finished(head, rows)
        if unfinished:
            merged["left_out"] = merged.get("left_out", 0) + unfinished
        merged["started"] = min(merged["started"], head["started"])
        merged["completed"] = max(merged["completed"], head["completed"])
        kept.extend(rows)
    strict = None
    if args.env == "climaqa":
        strict = near_matches()
    date = next(iter(runs.values()))[0]["started"][:10]
    text = render(args.env, list(runs.values()), date, strict)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, "utf-8")
    print(f"{len(runs)} models, written to {args.out}")


if __name__ == "__main__":
    main()
