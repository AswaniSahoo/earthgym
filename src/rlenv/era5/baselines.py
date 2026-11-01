"""Baseline rows for era5-forecast-v1 (decision 0007): persistence, climatology, an
always-climatology policy run through the answer parser and the reward, and IFS HRES.

uv run python -m rlenv.era5.baselines   # writes reports/era5/items_v1_baselines.md
"""

import json
import statistics
from pathlib import Path

import numpy as np
from era5_forecast_v1 import contract

from rlenv.era5 import items, scores

REPORT = Path("reports/era5/items_v1_baselines.md")
BASELINES = {
    "persistence": lambda item: item["history"][-1],
    "climatology": lambda item: item["climatology"],
    "always-climatology policy": lambda item: contract.answer(f"ANSWER: {item['climatology']}"),
    "IFS HRES": lambda item: item["hres"],
    "midpoint": lambda item: (item["history"][-1] + item["climatology"]) / 2,
}


def reward(item: dict, forecast: float | None) -> float:
    persistence, climatology = item["history"][-1], item["climatology"]
    return contract.reward(forecast, item["truth"], persistence, climatology, item["floor"])


def rows(records: list[dict], forecasts: dict = BASELINES) -> list[dict]:
    """Per variable, lead and forecast (the baselines unless given): n, area-weighted RMSE and
    ACC, and the mean reward."""
    out = []
    for variable in items.VARIABLES:
        for lead in items.LEADS:
            group = [r for r in records if (r["variable"], r["lead_hours"]) == (variable, lead)]
            if not group:
                continue
            w = np.array([r["area_weight"] for r in group])
            y = np.array([r["truth"] for r in group])
            c = np.array([r["climatology"] for r in group])
            for name, forecast in forecasts.items():
                f = np.array([forecast(r) for r in group])
                acc = scores.item_acc(f, y, c, w) if np.any(f != c) else None
                paid = [reward(r, value) for r, value in zip(group, f, strict=True)]
                out.append(
                    {"variable": variable, "lead": lead, "baseline": name, "n": len(group)}
                    | {
                        "rmse": scores.item_rmse(f, y, w),
                        "acc": acc,
                        "reward": float(np.mean(paid)),
                    }
                )
    return out


def mixture_weight(train: list[dict]) -> float:
    """The weight w in w * persistence + (1 - w) * climatology, on a grid of 0.01, that earns
    the most mean reward on the items given; the smallest of any tie."""

    def paid(w: float) -> float:
        p = [reward(r, w * r["history"][-1] + (1 - w) * r["climatology"]) for r in train]
        return statistics.fmean(p)

    return max((k / 100 for k in range(101)), key=paid)


def forecasters(records: list[dict]) -> dict:
    """The baselines and the convex mixture of persistence and climatology, its weight fitted
    on the train split only, so the test split can score it out of sample."""
    w = mixture_weight([r for r in records if contract.split(r) == "train"])

    def mixture(item: dict) -> float:
        return w * item["history"][-1] + (1 - w) * item["climatology"]

    return BASELINES | {f"mixture (w {w:.2f}, fitted on the train split)": mixture}


def held_out(records: list[dict], forecasts: dict) -> list[dict]:
    """Mean reward per forecast on the test split."""
    test = [r for r in records if contract.split(r) == "test"]
    return [
        {"forecast": name, "n": len(test)}
        | {"reward": statistics.fmean(reward(r, f(r)) for r in test)}
        for name, f in forecasts.items()
    ]


def quarters(records: list[dict]) -> list[dict]:
    """Per variable, the items ranked by their better-baseline error b and split into four
    equal parts, with what IFS HRES earns in each."""
    out = []
    for variable in items.VARIABLES:
        group = [r for r in records if r["variable"] == variable]
        group.sort(key=lambda r: (items.better_baseline_error(r), r.get("id", "")))
        for quarter, part in enumerate(np.array_split(np.arange(len(group)), 4), start=1):
            chosen = [group[k] for k in part]
            if not chosen:
                continue
            paid = [reward(r, r["hres"]) for r in chosen]
            errors = [items.better_baseline_error(r) for r in chosen]
            out.append(
                {"variable": variable, "quarter": quarter, "n": len(chosen)}
                | {"median_b": float(np.median(errors)), "hres_reward": float(np.mean(paid))}
                | {"hres_zero": sum(p == 0 for p in paid)}
            )
    return out


def render(
    table: list[dict], records: list[dict] | None = None, held: list[dict] | None = None
) -> str:
    lines = [
        "# era5-forecast-v1 baseline rows",
        "",
        "Area-weighted RMSE and ACC over the items (WB2 rules), mean reward per item (0007).",
        "",
        "| variable | lead h | baseline | n | RMSE | ACC | mean reward |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in table:
        acc = "n/a" if r["acc"] is None else f"{r['acc']:.3f}"
        lines.append(
            f"| {r['variable']} | {r['lead']} | {r['baseline']} | {r['n']} | "
            f"{r['rmse']:.3f} | {acc} | {r['reward']:.3f} |"
        )
    if held:
        lines += [
            "",
            "## Held out",
            "",
            f"Mean reward on the test split ({held[0]['n']} items, one init week in five by a hash "
            "of the week; era5_forecast_v1/contract.py), where the mixture's weight was not "
            "fitted:",
            "",
            "| forecast | n | mean reward |",
            "|---|---|---|",
        ]
        lines += [f"| {r['forecast']} | {r['n']} | {r['reward']:.3f} |" for r in held]
    if not records:
        return "\n".join([*lines, ""])
    lines += [
        "",
        "Reward floor per variable: the 10th percentile of the better-baseline error (0007);",
        "it binds where that error is below the floor.",
        "",
        "| variable | floor | binds |",
        "|---|---|---|",
    ]
    for variable in items.VARIABLES:
        group = [r for r in records if r["variable"] == variable]
        if group:
            binds = sum(items.better_baseline_error(r) < r["floor"] for r in group)
            lines.append(f"| {variable} | {group[0]['floor']:.3f} | {binds} of {len(group)} |")
    lines += [
        "",
        "## Limits",
        "",
        "The baseline is the better of persistence and climatology for each item, picked with the",
        "truth known, so where one of them is nearly exact little skill is left to earn. Items",
        "ranked by that error b and split into quarters:",
        "",
        "| variable | quarter | n | median b | IFS HRES mean reward | HRES earns 0 |",
        "|---|---|---|---|---|---|",
    ]
    for r in quarters(records):
        lines.append(
            f"| {r['variable']} | {r['quarter']} | {r['n']} | {r['median_b']:.3f} | "
            f"{r['hres_reward']:.3f} | {r['hres_zero']} |"
        )
    exact = {
        v: sum(items.better_baseline_error(r) == 0 for r in records if r["variable"] == v)
        for v in items.VARIABLES
        if any(r["variable"] == v for r in records)
    }
    named = ", ".join(f"{v} {n}" for v, n in exact.items())
    lines += ["", f"Items where a baseline is exact, so no reply can earn a reward: {named}."]
    return "\n".join([*lines, ""])


def main() -> None:
    records = [json.loads(line) for line in items.OUT.read_text("utf-8").splitlines()]
    fs = forecasters(records)
    REPORT.write_text(render(rows(records, fs), records, held_out(records, fs)), "utf-8")
    print(f"{len(records)} items scored, written to {REPORT}")


if __name__ == "__main__":
    main()
