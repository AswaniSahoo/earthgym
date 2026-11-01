"""The bundled MSLP items against the pinned subset, an offline oracle (skipped without it)."""

import json
from datetime import datetime, timedelta

import pytest

from earthgym.era5 import data, items

pytestmark = pytest.mark.skipif(
    not data.SUBSET.exists(), reason="no pinned subset; run uv run python -m earthgym.era5.data"
)
FORMAT = "%Y-%m-%dT%H"


def test_mslp_items_match_the_pinned_subset_wherever_it_can_see_them():
    s = data.load()
    k_of = {str(t): k for k, t in enumerate(s["init_time"])}  # init k holds ERA5 at init + 72 h
    lat = {float(v): i for i, v in enumerate(s["latitude"])}
    lon = {float(v): j for j, v in enumerate(s["longitude"])}

    def init_72h_before(time):
        return k_of.get(f"{datetime.strptime(time, FORMAT) - timedelta(hours=72):{FORMAT}}")

    seen = {"truth": 0, "climatology": 0, "history": 0, "hres": 0}
    rows = [json.loads(line) for line in items.OUT.read_text("utf-8").splitlines()]
    for r in (r for r in rows if r["variable"] == data.VARIABLE):
        i, j = lat[r["latitude"]], lon[r["longitude"]]
        if (k := init_72h_before(r["valid_time"])) is not None:
            assert r["truth"] == round(float(s["truth"][k, i, j]), 1)
            assert r["climatology"] == round(float(s["climatology"][k, i, j]), 1)
            seen["truth"] += 1
            seen["climatology"] += 1
        for time, value in zip(r["history_times"], r["history"], strict=True):
            if (k := init_72h_before(time)) is not None:
                assert value == round(float(s["truth"][k, i, j]), 1)
                seen["history"] += 1
        if r["lead_hours"] == data.LEAD_HOURS:
            assert r["hres"] == round(float(s["forecast"][k_of[r["init_time"]], i, j]), 1)
            seen["hres"] += 1
    assert seen == {"truth": 360, "climatology": 360, "history": 2495, "hres": 120}
