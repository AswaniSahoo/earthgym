"""Which task the GRPO run trains on, by the rule decision 0024 set before the runs reported.

uv run python -m earthgym.grpo.pick

Of the tasks whose median reply fits the run's completion cap, the one whose train-split items
have the highest mean variance of their 8 rewards; a tie goes to the larger share of train items
whose reward varies. The numbers come from Qwen3.5-2B's committed per-item results.
"""

import statistics
from pathlib import Path

from earthgym import results, samples

CAP = 1024  # the run's max_completion_length (earthgym.grpo.kernel)


def stats(rows: list[dict], train: set[str]) -> dict:
    """One task's median reply length in output tokens over all its samples, and over its
    train items the mean population variance of their rewards and the share that vary."""
    by = samples.by_item([r for r in rows if r["id"] in train])
    return {
        "median_tokens": statistics.median(r["tokens"][3] for r in rows if "tokens" in r),
        "train_items": len(by),
        "mean_variance": statistics.fmean(statistics.pvariance(v) for v in by.values()),
        "varies": statistics.fmean(min(v) != max(v) for v in by.values()),
    }


def pick(tasks: dict[str, dict], cap: int = CAP) -> str:
    eligible = {name: s for name, s in tasks.items() if s["median_tokens"] <= cap}
    if not eligible:
        raise ValueError(f"no task has a median reply within {cap} tokens")
    return max(
        eligible, key=lambda name: (eligible[name]["mean_variance"], eligible[name]["varies"])
    )


def finished() -> dict[str, dict]:
    """The five candidate tasks' numbers from Qwen3.5-2B's results, on their train items;
    ERA5's come in two files, the second from a session stopped by its deadline."""
    from climaqa_v1.taskset import ClimaqaConfig, ClimaqaTaskset
    from era5_forecast_v1.taskset import ForecastConfig, ForecastTaskset
    from heat_basis_v1.taskset import HeatConfig, HeatTaskset
    from ibtracs_storm_v1.taskset import StormConfig, StormTaskset

    r = Path("reports")
    name = "2026-11-02-qwen3.5-2b-q8_0-8-samples"
    runs = {
        "climaqa mcq": (
            [r / f"climaqa/results/{name}-mcq.jsonl"],
            ClimaqaTaskset(ClimaqaConfig(kinds=["mcq"], split="train")),
        ),
        "climaqa cloze": (
            [r / f"climaqa/results/{name}-cloze.jsonl"],
            ClimaqaTaskset(ClimaqaConfig(kinds=["cloze"], split="train")),
        ),
        "ibtracs": (
            [r / f"ibtracs/results/{name}.jsonl"],
            StormTaskset(StormConfig(split="train")),
        ),
        "heat": ([r / f"heat/results/{name}.jsonl"], HeatTaskset(HeatConfig(split="train"))),
        "era5": (
            [r / f"era5/results/{name}-a.jsonl", r / f"era5/results/{name}-b.jsonl"],
            ForecastTaskset(ForecastConfig(split="train")),
        ),
    }
    out = {}
    for task, (paths, taskset) in runs.items():
        rows = [row for path in paths for row in samples.finished(*results.read(path))[0]]
        out[task] = stats(rows, {t.data.id for t in taskset.load()})
    return out


def main() -> None:
    tasks = finished()
    for name, s in tasks.items():
        print(
            f"{name}: median reply {s['median_tokens']:g} tokens, {s['train_items']} train items, "
            f"mean reward variance {s['mean_variance']:.4f}, varying share {s['varies']:.3f}"
        )
    print(f"pick: {pick(tasks)}")


if __name__ == "__main__":
    main()
