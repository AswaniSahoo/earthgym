"""Heat counts from GHCN-Daily TMAX by NWS Phoenix's whole-degree rules (decision 0012).

GHCN-Daily stores a US station's whole-degree-F reading in tenths of a degree C, so a
threshold goes the same way: a day reaches 110 F when its value is at least tenths(110), 433.
"""

import datetime as dt


def tenths(f: int) -> int:
    """A whole degree F as GHCN-Daily stores it, in tenths of a degree C."""
    return round((f - 32) * 50 / 9)


def fahrenheit(t: int) -> int:
    """Tenths of a degree C back to the whole degree F they were converted from."""
    return round(t * 9 / 50 + 32)


def days_at_or_above(series: dict[str, int], year: int, f: int) -> int:
    t, prefix = tenths(f), str(year)
    return sum(v >= t for d, v in series.items() if d.startswith(prefix))


def longest_run(series: dict[str, int], year: int, f: int) -> tuple[int, str | None, str | None]:
    """The first longest run of consecutive days at or above f; a missing day breaks a run."""
    t, best, run, end = tenths(f), 0, 0, None
    day = dt.date(year, 1, 1)
    while day.year == year:
        value = series.get(day.strftime("%Y%m%d"))
        run = run + 1 if value is not None and value >= t else 0
        if run > best:
            best, end = run, day
        day += dt.timedelta(days=1)
    if end is None:
        return 0, None, None
    return best, (end - dt.timedelta(days=best - 1)).isoformat(), end.isoformat()


def highest(series: dict[str, int], year: int) -> tuple[int, str]:
    """The year's highest TMAX in whole degrees F and the first date it was reached."""
    days = sorted((d, v) for d, v in series.items() if d.startswith(str(year)))
    top = max(v for _, v in days)
    first = next(d for d, v in days if v == top)
    return fahrenheit(top), f"{first[:4]}-{first[4:6]}-{first[6:]}"
