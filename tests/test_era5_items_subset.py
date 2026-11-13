"""The bundled items against the pinned subsets, an offline oracle (skipped without them)."""

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
    # the 324 MSLP items left after the gold check (0021), 110 of them at 72 h
    assert seen == {"truth": 324, "climatology": 324, "history": 2253, "hres": 110}


def subsets_of(variable: str) -> list[tuple[int, dict, dict]]:
    """Each pinned subset of a variable that is on disk: its lead, arrays and init index."""
    found = []
    for (v, lead), (path, pin) in data.SUBSETS.items():
        if v == variable and path.exists():
            s = data.load(path, pin)
            found.append((lead, s, {str(t): k for k, t in enumerate(s["init_time"])}))
    return found


@pytest.mark.parametrize("variable", ["mean_sea_level_pressure", "2m_temperature"])
def test_every_item_matches_the_subsets_of_its_variable(variable):
    subsets = subsets_of(variable)
    if len(subsets) < 3:
        pytest.skip(f"not all three {variable} subsets; run uv run python -m earthgym.era5.data")
    _, first, _ = subsets[0]
    lat = {float(v): i for i, v in enumerate(first["latitude"])}
    lon = {float(v): j for j, v in enumerate(first["longitude"])}

    def era5_at(time: str, i: int, j: int):
        """ERA5 and its climatology at a time, from any subset whose valid times hold it."""
        for lead, s, k_of in subsets:
            init = f"{datetime.strptime(time, FORMAT) - timedelta(hours=lead):{FORMAT}}"
            if (k := k_of.get(init)) is not None:
                return float(s["truth"][k, i, j]), float(s["climatology"][k, i, j])
        return None

    hres = {lead: (s, k_of) for lead, s, k_of in subsets}
    places = items.DECIMALS[variable]  # Pa and K as the prompt shows them
    seen = {"truth": 0, "history": 0, "hres": 0}
    rows = [json.loads(line) for line in items.OUT.read_text("utf-8").splitlines()]
    for r in (r for r in rows if r["variable"] == variable):
        i, j = lat[r["latitude"]], lon[r["longitude"]]
        truth, climatology = era5_at(r["valid_time"], i, j)
        assert (r["truth"], r["climatology"]) == (round(truth, places), round(climatology, places))
        seen["truth"] += 1
        for time, value in zip(r["history_times"], r["history"], strict=True):
            if (found := era5_at(time, i, j)) is not None:
                assert value == round(found[0], places)
                seen["history"] += 1
        s, k_of = hres[r["lead_hours"]]
        assert r["hres"] == round(float(s["forecast"][k_of[r["init_time"]], i, j]), places)
        seen["hres"] += 1
    # every item of the variable after the gold check (0021), with the history values the three
    # subsets' valid times hold
    assert seen == {"truth": 324, "history": 2257, "hres": 324}
