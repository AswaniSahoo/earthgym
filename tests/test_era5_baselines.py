import math

import pytest

from earthgym.era5 import baselines


def item(truth, persistence, climatology, hres):
    return {
        "variable": "2m_temperature",
        "lead_hours": 24,
        "truth": truth,
        "history": [0.0, persistence],
        "climatology": climatology,
        "hres": hres,
        "area_weight": 1.0,
        "floor": 0.5,
    }


# better-baseline errors are 1 and 1; HRES errs by 0.5 and 0
ITEMS = [item(290.0, 292.0, 289.0, 290.5), item(280.0, 279.0, 283.0, 280.0)]


def test_copying_a_baseline_earns_zero_and_hres_earns_its_skill():
    rows = {r["baseline"]: r for r in baselines.rows(ITEMS)}
    assert {name: r["reward"] for name, r in rows.items()} == {
        "persistence": 0.0,
        "climatology": 0.0,
        "always-climatology policy": 0.0,
        "IFS HRES": 0.75,
        "midpoint": 0.25,  # halfway errs by 0.5 and 1: rewards 0.5 and 0
    }
    assert rows["IFS HRES"]["rmse"] == pytest.approx(math.sqrt(0.125))
    assert rows["always-climatology policy"]["acc"] is None  # no anomaly, no correlation


def test_render_gives_one_table_row_per_baseline():
    text = baselines.render(baselines.rows(ITEMS))
    assert "| 2m_temperature | 24 | IFS HRES | 2 | 0.354 | " in text
    assert "| 2m_temperature | 24 | climatology | 2 | " in text and "n/a" in text


def test_render_reports_each_floor_and_how_often_it_binds():
    near = item(280.0, 280.2, 283.0, 280.0)  # better-baseline error 0.2, under the 0.5 floor
    text = baselines.render(baselines.rows([*ITEMS, near]), [*ITEMS, near])
    assert "| 2m_temperature | 0.500 | 1 of 3 |" in text


def test_limits_show_hres_reward_by_quarter_of_baseline_error_and_the_dead_items():
    # truth 0, climatology 5: better-baseline errors 0, 1, 2, 3; HRES errs 0, 0, 1, 3
    ranked = [item(0.0, b, 5.0, h) for b, h in ((0.0, 0.0), (1.0, 0.0), (2.0, 1.0), (3.0, 3.0))]
    text = baselines.render(baselines.rows(ranked), ranked)
    for line in [
        "| 2m_temperature | 1 | 1 | 0.000 | 0.000 | 1 |",  # b = 0: nothing can be won
        "| 2m_temperature | 2 | 1 | 1.000 | 1.000 | 0 |",
        "| 2m_temperature | 3 | 1 | 2.000 | 0.500 | 0 |",
        "| 2m_temperature | 4 | 1 | 3.000 | 0.000 | 1 |",
        "Items where a baseline is exact, so no reply can earn a reward: 2m_temperature 1.",
    ]:
        assert line in text


def mixed(truth_w, p, c, init):
    """An item whose truth is the mixture truth_w * p + (1 - truth_w) * c, issued at init."""
    r = item(truth_w * p + (1 - truth_w) * c, p, c, 0.0)
    return r | {"init_time": init}


def init_in(split):
    from datetime import datetime, timedelta

    from era5_forecast_v1 import contract

    day = datetime(2020, 1, 1)
    while contract.split({"init_time": f"{day:%Y-%m-%dT%H}"}) != split:
        day += timedelta(days=7)
    return f"{day:%Y-%m-%dT%H}"


def test_mixture_weight_maximizes_mean_reward_on_the_items_given():
    train = [mixed(0.3, 292.0, 289.0, "x"), mixed(0.3, 279.0, 283.0, "x")]
    assert baselines.mixture_weight(train) == pytest.approx(0.3)


def test_the_mixture_is_fitted_on_the_train_split_only():
    train = [mixed(0.3, 292.0, 289.0, init_in("train")), mixed(0.3, 279.0, 283.0, init_in("train"))]
    test = [mixed(0.9, 292.0, 289.0, init_in("test"))]
    names = [n for n in baselines.forecasters(train + test) if n.startswith("mixture")]
    assert names == ["mixture (w 0.30, fitted on the train split)"]


def test_held_out_rewards_are_on_the_test_split_and_render_in_their_own_table():
    records = [
        mixed(0.3, 292.0, 289.0, init_in("train")),
        mixed(0.5, 279.0, 283.0, init_in("test")),
    ]
    held = {r["forecast"]: r for r in baselines.held_out(records, baselines.BASELINES)}
    assert held["midpoint"]["n"] == 1 and held["midpoint"]["reward"] == pytest.approx(1.0)
    text = baselines.render(baselines.rows(records), records, held=list(held.values()))
    assert "## Held out" in text and "| midpoint | 1 | 1.000 |" in text


def test_all_items_rewards_cover_every_item_and_render_in_their_own_table():
    records = [
        ITEMS[0] | {"id": f"x{i}", "init_time": f"2020-0{1 + i % 9}-01T00"} for i in range(9)
    ]
    every = baselines.held_out(records, baselines.BASELINES, split=None)
    assert {r["n"] for r in every} == {9}
    text = baselines.render(baselines.rows(records), records, overall=every)
    assert "## All items" in text and "| midpoint | 9 |" in text
