"""A parametric heat policy's rules over GHCN-Daily TMAX (decision 0013): the cover window,
trigger days, events of consecutive trigger days, and the days it misses at an insured site.

A trigger day reaches a whole-degree-F threshold, compared in GHCN-Daily's unit (`stats.tenths`).
A missing value is never a trigger day and ends a run.
"""

import datetime as dt

from rlenv.heat import stats


def window(year: int) -> list[str]:
    """The cover window, 1 May to 30 September, as GHCN-Daily dates."""
    day, end = dt.date(year, 5, 1), dt.date(year, 9, 30)
    out = []
    while day <= end:
        out.append(day.strftime("%Y%m%d"))
        day += dt.timedelta(days=1)
    return out


def _hot(series: dict[str, int], day: str, t: int) -> bool:
    value = series.get(day)
    return value is not None and value >= t


def trigger_days(index: dict[str, int], year: int, f: int) -> int:
    t = stats.tenths(f)
    return sum(_hot(index, d, t) for d in window(year))


def events(index: dict[str, int], year: int, f: int, k: int) -> int:
    """Runs of at least k consecutive trigger days in the window; each run pays once."""
    t, count, run = stats.tenths(f), 0, 0
    for d in window(year):
        run = run + 1 if _hot(index, d, t) else 0
        count += run == k
    return count


def missed_days(index: dict[str, int], site: dict[str, int], year: int, f: int) -> int:
    """Days in the window when the insured site reached the threshold and the index did not."""
    t = stats.tenths(f)
    return sum(_hot(site, d, t) and not _hot(index, d, t) for d in window(year))
