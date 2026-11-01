"""Forecast items for the era5-forecast-v1 environment (decision 0007).

Each item is one grid cell, one variable, one 2020 init and one lead: the ERA5 history over
the 72 h up to the init and the climatology at the valid time go into the prompt; the ERA5
truth and the IFS HRES forecast stay hidden for the reward and the baseline rows.
"""

import argparse
import hashlib
import json
import random
from datetime import timedelta
from pathlib import Path

import numpy as np

from earthgym.era5 import data, scores

SEED, PER_GROUP = 20261030, 120  # 2 variables x 3 leads x 120 = 720 items
OUT = Path("environments/era5_forecast_v1/era5_forecast_v1/era5_forecast_v1.jsonl")
MANIFEST = Path("reports/era5/items_v1_manifest.json")
VARIABLES = ["mean_sea_level_pressure", "2m_temperature"]
LEADS = [24, 48, 72]
DECIMALS = {"mean_sea_level_pressure": 1, "2m_temperature": 2}  # Pa and K as shown
HISTORY_STEPS = 13  # every 6 h over the 72 h up to and including the init
FLOOR_PERCENTILE = 10  # the floor only guards a near-zero baseline error, so it binds rarely


def better_baseline_error(row: dict) -> float:
    """|truth - b| for the better of persistence (the value at the init) and climatology."""
    truth = row["truth"]
    return min(abs(row["history"][-1] - truth), abs(row["climatology"] - truth))


def floors(rows: list[dict]) -> dict[str, float]:
    """Each variable's reward floor: the 10th percentile (numpy's linear rule) of the
    better-baseline error over the items, never below the smallest shown unit, stored to one
    decimal more than shown. Baseline data only, no model information."""
    out = {}
    for v in VARIABLES:
        errors = [better_baseline_error(r) for r in rows if r["variable"] == v]
        if errors:
            floor = max(float(np.percentile(errors, FLOOR_PERCENTILE)), 10.0 ** -DECIMALS[v])
            out[v] = round(floor, DECIMALS[v] + 1)
    return out


def with_floors(rows: list[dict]) -> list[dict]:
    """The rows with their variable's floor, so each item carries what its reward needs."""
    floor = floors(rows)
    return [row | {"floor": floor[row["variable"]]} for row in rows]


def floor_binds(rows: list[dict]) -> dict[str, int]:
    """How many items per variable have a better-baseline error below their floor."""
    return {
        v: sum(better_baseline_error(r) < r["floor"] for r in rows if r["variable"] == v)
        for v in VARIABLES
    }


def plan(seed: int, per_group: int, inits: int, lats: int, lons: int) -> list[tuple]:
    """(variable, lead, init index, latitude index, longitude index) for per_group distinct
    cells and inits in each variable and lead, drawn with a seeded stdlib generator."""
    rng, cells = random.Random(seed), lats * lons
    picks = []
    for variable in VARIABLES:
        for lead in LEADS:
            for flat in rng.sample(range(inits * cells), per_group):
                k, rest = divmod(flat, cells)
                picks.append((variable, lead, k, *divmod(rest, lons)))
    return picks


def make_item(variable: str, lead: int, k: int, i: int, j: int, fields: dict) -> dict:
    init = fields["inits"][k]
    valid = init + timedelta(hours=lead)
    when = [init - timedelta(hours=6 * s) for s in reversed(range(HISTORY_STEPS))]
    step = {t: s for s, t in enumerate(fields["era5_times"])}
    era5, places = fields["era5"][variable], DECIMALS[variable]

    def at(time):
        return round(float(era5[step[time], i, j]), places)

    clim = fields["clim"][variable]
    normal = data.align(clim, fields["clim_hours"], fields["clim_days"], [valid])[0, i, j]
    return {
        "id": f"{variable}/{init:%Y-%m-%dT%H}/{lead}h/{i}-{j}",
        "variable": variable,
        "latitude": float(fields["latitude"][i]),
        "longitude": float(fields["longitude"][j]),
        "init_time": f"{init:%Y-%m-%dT%H}",
        "valid_time": f"{valid:%Y-%m-%dT%H}",
        "lead_hours": lead,
        "history_times": [f"{t:%Y-%m-%dT%H}" for t in when],
        "history": [at(t) for t in when],
        "climatology": round(float(normal), places),
        "truth": at(valid),
        "hres": round(float(fields["hres"][(variable, lead)][k, i, j]), places),
        "area_weight": float(scores.area_weights(fields["latitude"])[i]),
    }


def read_fields() -> dict:
    """ERA5, climatology and HRES (24, 48, 72 h) for both variables from the pinned stores;
    about 56 MB of chunks."""
    era5, hres = data.open_store(data.ERA5), data.open_store(data.HRES)
    clim = data.open_store(data.CLIMATOLOGY)
    inits = [data.FIRST_INIT + timedelta(hours=12 * k) for k in range(data.INITS)]
    first = inits[0] - timedelta(hours=6 * (HISTORY_STEPS - 1))
    steps = (inits[-1] + timedelta(hours=max(LEADS)) - first) // timedelta(hours=6) + 1
    era5_times = [first + timedelta(hours=6 * s) for s in range(steps)]
    e = data.positions(era5["time"][:], data.store_hours(era5, era5_times))
    h = data.positions(hres["time"][:], data.store_hours(hres, inits))
    if not ((np.diff(e) == 1).all() and (np.diff(h) == 1).all()):
        raise ValueError("ERA5 steps or HRES inits are not consecutive in the store")
    leads = data.positions(hres["prediction_timedelta"][:], LEADS)
    latitude, longitude = data.grid(hres, era5, clim)
    fields = {"inits": inits, "latitude": latitude, "longitude": longitude}
    fields |= {"era5_times": era5_times, "era5": {}, "clim": {}, "hres": {}}
    fields |= {"clim_hours": clim["hour"][:], "clim_days": clim["dayofyear"][:]}
    for v in VARIABLES:  # stores hold (..., longitude, latitude); items want latitude first
        fields["era5"][v] = np.swapaxes(era5[v][e[0] : e[-1] + 1], -1, -2)
        fields["clim"][v] = np.swapaxes(clim[v][:], -1, -2)
        for lead, k in zip(LEADS, leads, strict=True):
            fields["hres"][(v, lead)] = np.swapaxes(hres[v][h[0] : h[-1] + 1, k], -1, -2)
    return fields


def fields_sha256(fields: dict) -> str:
    """Content hash of every array the builder reads from the stores, so a rebuild can tell a
    store that serves other values under the same pinned metadata."""
    arrays = {k: fields[k] for k in ("latitude", "longitude", "clim_hours", "clim_days")}
    arrays |= {f"era5/{v}": a for v, a in fields["era5"].items()}
    arrays |= {f"clim/{v}": a for v, a in fields["clim"].items()}
    arrays |= {f"hres/{v}/{lead}": a for (v, lead), a in fields["hres"].items()}
    return data.content_sha256(arrays)


def check_fields(fields: dict, manifest: Path = MANIFEST) -> str:
    """The fields' hash, after checking it against the one the manifest records, if any."""
    digest = fields_sha256(fields)
    pinned = json.loads(manifest.read_text("utf-8")).get("fields_sha256")
    if pinned not in (None, digest):
        raise ValueError(f"the stores serve other values: fields sha256 {digest}, pinned {pinned}")
    return digest


def write(rows: list[dict], out: Path = OUT, manifest: Path = MANIFEST, **extra) -> str:
    """One JSON object per line, and a manifest with the file's sha256, how it was made and
    any extra fields."""
    text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, "utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    meta = {"version": "v1", "items": len(rows), "sha256": digest, "seed": SEED}
    meta |= {"per_group": PER_GROUP, "variables": VARIABLES, "leads": LEADS}
    meta |= {"history_steps": HISTORY_STEPS, "stores": data.METADATA_SHA256} | extra
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(meta, indent=1) + "\n", "utf-8")
    return digest


def main() -> None:
    argparse.ArgumentParser(description="Build the era5-forecast-v1 items.").parse_args()
    fields = read_fields()
    checked = check_fields(fields)
    shape = (data.INITS, len(fields["latitude"]), len(fields["longitude"]))
    rows = with_floors([make_item(*pick, fields) for pick in plan(SEED, PER_GROUP, *shape)])
    extra = {"floors": floors(rows), "floor_binds": floor_binds(rows), "fields_sha256": checked}
    digest = write(rows, **extra)
    print(f"{len(rows)} items, sha256 {digest}")


if __name__ == "__main__":
    main()
