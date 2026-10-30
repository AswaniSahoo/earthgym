import hashlib
import json
from datetime import datetime, timedelta

import numpy as np
import pytest

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
        "latitude": np.array([-60.0, 0.0]),  # cell areas 0.5 and 1, so weights 2/3 and 4/3
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
        0.0,
        240.0,
    )
    assert item["area_weight"] == pytest.approx(4 / 3)


def test_plan_is_seeded_and_balanced_over_variables_and_leads():
    first = items.plan(seed=7, per_group=5, inits=10, lats=4, lons=8)
    assert first == items.plan(seed=7, per_group=5, inits=10, lats=4, lons=8)
    groups = {(v, lead) for v, lead, *_ in first}
    assert len(first) == 30 and len(groups) == 6


def test_write_saves_items_as_jsonl_and_a_manifest_with_their_sha256(tmp_path):
    out, manifest = tmp_path / "items.jsonl", tmp_path / "manifest.json"
    items.write([{"id": "b", "x": 1}, {"id": "a", "x": 2}], out, manifest)
    assert [json.loads(line)["id"] for line in out.read_text().splitlines()] == ["b", "a"]
    meta = json.loads(manifest.read_text())
    assert meta["sha256"] == hashlib.sha256(out.read_bytes()).hexdigest() and meta["items"] == 2


def test_bundled_items_match_their_manifest():
    meta = json.loads(items.MANIFEST.read_text())
    assert hashlib.sha256(items.OUT.read_bytes()).hexdigest() == meta["sha256"]
    assert len(items.OUT.read_text().splitlines()) == meta["items"] == 720


def floor_row(variable, error):
    """An item whose better-baseline error is `error` (persistence), climatology far off."""
    return {"variable": variable, "truth": 0.0, "history": [0.0, error], "climatology": 99.0}


def test_floors_are_the_tenth_percentile_of_the_better_baseline_error():
    rows = [floor_row(T2M, 0.1 * k) for k in range(1, 11)]  # errors 0.1 to 1.0
    rows += [floor_row("mean_sea_level_pressure", e) for e in (10.0, 20.0, 30.0, 40.0, 50.0)]
    floors = items.floors(rows)  # numpy's linear percentile: 0.1 + 0.9 * 0.1, 10 + 0.4 * 10
    assert floors == pytest.approx({T2M: 0.19, "mean_sea_level_pressure": 14.0})
    assert {r["floor"] for r in items.with_floors(rows) if r["variable"] == T2M} == {floors[T2M]}


def test_floors_never_drop_below_the_smallest_shown_unit_and_are_stored_rounded():
    exact = [floor_row(T2M, 0.0)] * 5 + [floor_row(T2M, 1.0)] * 5  # 10th percentile is 0
    assert items.floors(exact) == {T2M: 0.01}  # 2 m temperature is shown to 0.01 K
    uneven = [floor_row(T2M, e) for e in (0.0123, 0.0456, 0.9, 0.9, 0.9)]
    assert items.floors(uneven) == {T2M: round(0.0123 + 0.4 * (0.0456 - 0.0123), 3)}


def test_bundled_floors_follow_the_rule_and_the_manifest_records_them():
    rows = [json.loads(line) for line in items.OUT.read_text().splitlines()]
    floors = items.floors(rows)
    assert all(r["floor"] == pytest.approx(floors[r["variable"]]) for r in rows)
    assert json.loads(items.MANIFEST.read_text())["floors"] == pytest.approx(floors)
