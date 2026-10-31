"""North Atlantic season statistics from IBTrACS, by NOAA's rules (docs/radar.md).

ACE (NOAA CPC): the sum of squared maximum sustained winds in knots, every six hours, while a
storm is at least tropical storm strength, in units of 1e4 kt^2. On IBTrACS: USA_WIND at 00,
06, 12 and 18 UTC while USA_STATUS is TS, HU or SS and the wind is 34 kt or more. A named
storm, hurricane or major hurricane has a row at 34 kt with that status, or 64 or 96 kt as HU.
Spur tracks are left out, and only rows inside the basin count.
"""

from collections import defaultdict

COLUMNS = ("SID", "SEASON", "BASIN", "ISO_TIME", "TRACK_TYPE", "USA_STATUS", "USA_WIND")
SYNOPTIC = ("00:00:00", "06:00:00", "12:00:00", "18:00:00")
NAMED = {"TS", "HU", "SS"}  # tropical storm, hurricane, subtropical storm


def wind(row: dict) -> int:
    return int(row["USA_WIND"]) if row["USA_WIND"] else 0


def storm(rows: list[dict]) -> dict:
    """One storm's flags and ACE, over the rows given."""

    def reaches(knots: int, statuses: set) -> bool:
        return any(wind(r) >= knots and r["USA_STATUS"] in statuses for r in rows)

    synoptic = [r for r in rows if r["ISO_TIME"][11:] in SYNOPTIC]
    ace = sum(wind(r) ** 2 for r in synoptic if wind(r) >= 34 and r["USA_STATUS"] in NAMED)
    return {
        "named": reaches(34, NAMED),
        "hurricane": reaches(64, {"HU"}),
        "major": reaches(96, {"HU"}),
        "ace": ace / 1e4,
    }


def season(rows: list[dict], year: int, basin: str = "NA") -> dict:
    """Counts and ACE for one season, from the basin's own rows of each non-spur storm."""
    tracks = defaultdict(list)
    for r in rows:
        if int(r["SEASON"]) == year:
            tracks[r["SID"]].append(r)
    totals = {"named": 0, "hurricanes": 0, "major": 0, "ace": 0.0}
    for track in tracks.values():
        if any("spur" in r["TRACK_TYPE"] for r in track):
            continue
        s = storm([r for r in track if r["BASIN"] == basin])
        totals["named"] += s["named"]
        totals["hurricanes"] += s["hurricane"]
        totals["major"] += s["major"]
        totals["ace"] += s["ace"]
    return totals
