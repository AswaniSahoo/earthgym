"""Forecast items for the era5-forecast-v1 environment (decision 0007).

Each item is one grid cell, one variable, one 2020 init and one lead: the ERA5 history over
the 72 h up to the init and the climatology at the valid time go into the prompt; the ERA5
truth and the IFS HRES forecast stay hidden for the reward and the baseline rows.
"""

import random
from datetime import timedelta

from rlenv.era5 import data

VARIABLES = ["mean_sea_level_pressure", "2m_temperature"]
LEADS = [24, 48, 72]
DECIMALS = {"mean_sea_level_pressure": 1, "2m_temperature": 2}  # Pa and K as shown
HISTORY_STEPS = 13  # every 6 h over the 72 h up to and including the init


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
    }
