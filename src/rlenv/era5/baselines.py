"""Baseline rows for era5-forecast-v1 (decision 0007): persistence, climatology, an
always-climatology policy run through the answer parser and the reward, and IFS HRES.

uv run python -m rlenv.era5.baselines   # writes reports/era5/items_v1_baselines.md
"""

import json
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
}


def reward(item: dict, forecast: float | None) -> float:
    persistence, climatology = item["history"][-1], item["climatology"]
    return contract.reward(forecast, item["truth"], persistence, climatology, item["floor"])


def rows(records: list[dict]) -> list[dict]:
    """Per variable, lead and baseline: n, area-weighted RMSE and ACC, and the mean reward."""
    out = []
    for variable in items.VARIABLES:
        for lead in items.LEADS:
            group = [r for r in records if (r["variable"], r["lead_hours"]) == (variable, lead)]
            if not group:
                continue
            w = np.array([r["area_weight"] for r in group])
            y = np.array([r["truth"] for r in group])
            c = np.array([r["climatology"] for r in group])
            for name, forecast in BASELINES.items():
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


def render(table: list[dict], records: list[dict] | None = None) -> str:
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
    if records:
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
    return "\n".join([*lines, ""])


def main() -> None:
    records = [json.loads(line) for line in items.OUT.read_text("utf-8").splitlines()]
    REPORT.write_text(render(rows(records), records), "utf-8")
    print(f"{len(records)} items scored, written to {REPORT}")


if __name__ == "__main__":
    main()
