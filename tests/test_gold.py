"""The verifiers gold check: each item's reference answer, through the environment's own
parser and reward, scores 1.0 (decision 0021)."""

import asyncio

import pytest
from climaqa_v1 import taskset as climaqa_ts
from era5_forecast_v1 import contract as era5
from era5_forecast_v1 import taskset as era5_ts
from heat_basis_v1 import taskset as heat_ts
from ibtracs_storm_v1 import taskset as ibtracs_ts

TASKSETS = {
    "climaqa": climaqa_ts.ClimaqaTaskset(climaqa_ts.ClimaqaConfig()),
    "era5": era5_ts.ForecastTaskset(era5_ts.ForecastConfig()),
    "ibtracs": ibtracs_ts.StormTaskset(ibtracs_ts.StormConfig()),
    "heat": heat_ts.HeatTaskset(heat_ts.HeatConfig()),
}


@pytest.mark.parametrize("name", TASKSETS)
def test_every_bundled_item_passes_the_gold_check(name):
    tasks = TASKSETS[name].load()
    assert [t.data.id for t in tasks if asyncio.run(t.validate(None)) is not True] == []


def test_the_gold_check_fails_a_forecast_item_whose_floor_binds():
    row = era5_ts.records()[0]
    task = era5_ts.ForecastTask(era5_ts.to_data(row | {"floor": 1e9}), None)
    assert asyncio.run(task.validate(None)) is False  # a perfect forecast earns b / floor < 1


def test_every_bundled_forecast_item_leaves_its_whole_reward_to_earn():
    rows = era5_ts.records()
    better = [
        min(abs(r["history"][-1] - r["truth"]), abs(r["climatology"] - r["truth"])) for r in rows
    ]
    assert all(b >= r["floor"] for b, r in zip(better, rows, strict=True))
    assert (
        era5.reward(
            rows[0]["truth"],
            rows[0]["truth"],
            rows[0]["history"][-1],
            rows[0]["climatology"],
            rows[0]["floor"],
        )
        == 1.0
    )
