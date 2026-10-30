from datetime import datetime, timedelta

import numpy as np

from rlenv.era5 import items

INIT = datetime(2020, 7, 1)
T2M = "2m_temperature"


def fields():
    """Synthetic fields whose values encode their indices: ERA5 step s at cell (i, j) holds
    1000 s + 10 i + j; 20 six-hourly steps from three days before the init."""
    steps = np.arange(20)[:, None, None]
    grid = 10 * np.arange(2)[None, :, None] + np.arange(3)[None, None, :]
    hres = {(T2M, 24): np.full((1, 2, 3), 7.0)}
    hres[(T2M, 24)][0, 1, 2] = 300.123
    clim = np.zeros((4, 366, 2, 3))
    clim[0, INIT.timetuple().tm_yday, 1, 2] = 288.456  # 00 UTC on the day after the init
    return {
        "inits": [INIT],
        "latitude": np.array([-45.0, 45.0]),
        "longitude": np.array([0.0, 120.0, 240.0]),
        "era5_times": [INIT - timedelta(hours=72) + timedelta(hours=6 * s) for s in range(20)],
        "era5": {T2M: (1000.0 * steps + grid).astype("f4")},
        "clim": {T2M: clim},
        "clim_hours": np.array([0, 6, 12, 18]),
        "clim_days": np.arange(1, 367),
        "hres": hres,
    }


def test_make_item_takes_history_truth_climatology_and_hres_at_its_cell():
    item = items.make_item(T2M, 24, 0, 1, 2, fields())
    assert item["history"] == [1000.0 * s + 12 for s in range(13)]  # 72 h up to the init
    assert item["history_times"][-1] == "2020-07-01T00"
    assert item["truth"] == 1000.0 * 16 + 12  # step 16 is 24 h after the init
    assert (item["climatology"], item["hres"]) == (288.46, 300.12)  # 2 decimals for kelvin
    assert (item["valid_time"], item["latitude"], item["longitude"]) == (
        "2020-07-02T00",
        45.0,
        240.0,
    )


def test_plan_is_seeded_and_balanced_over_variables_and_leads():
    first = items.plan(seed=7, per_group=5, inits=10, lats=4, lons=8)
    assert first == items.plan(seed=7, per_group=5, inits=10, lats=4, lons=8)
    groups = {(v, lead) for v, lead, *_ in first}
    assert len(first) == 30 and len(groups) == 6
