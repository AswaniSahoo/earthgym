import math

import pytest

from rlenv.era5 import baselines


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
