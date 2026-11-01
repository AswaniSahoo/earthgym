"""Reproduce NWS Phoenix's published heat counts from the pinned GHCN-Daily file (skipped
without it). Sources, checked on the live pages on 2026-11-01: weather.gov/psr/yearinreview2023
and the Phoenix column of weather.gov/psr/ExtremeTemps (decision 0012)."""

import hashlib

import pytest

from earthgym.heat import data, stats

PATH = data.ROOT / "USW00023183.csv.gz"
pytestmark = pytest.mark.skipif(
    not PATH.exists(), reason="no pinned file; run uv run python -m earthgym.heat.data"
)


@pytest.fixture(scope="module")
def tmax():
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == data.STATIONS["USW00023183"][0]
    return data.read(PATH)


def test_2023_climate_summary(tmax):
    # "DAYS MAX >= 110 55", "DAYS MAX >= 100 133", "DAYS MAX >= 90 185", "HIGHEST 119 07/19"
    # (the page also lists 07/20 and 07/25; `highest` returns the first date)
    assert [stats.days_at_or_above(tmax, 2023, f) for f in (110, 100, 90)] == [55, 133, 185]
    assert stats.highest(tmax, 2023) == (119, "2023-07-19")


def test_2023_longest_stretch_of_110_degree_days(tmax):
    # "Longest stretch of 110°F or greater days 31 (30 Jun 2023 - 30 Jul 2023)"
    assert stats.longest_run(tmax, 2023, 110) == (31, "2023-06-30", "2023-07-30")


def test_2024_records(tmax):
    # "Greatest number of 110° F or greater days 70 (2024)" and "Longest stretch of 100° F or
    # greater days 113 (27 May 2024 - 16 Sep 2024)"
    assert stats.days_at_or_above(tmax, 2024, 110) == 70
    assert stats.longest_run(tmax, 2024, 100) == (113, "2024-05-27", "2024-09-16")


def test_2020_record_count_of_100_degree_days(tmax):
    # "Greatest number of 100° F or greater days 145 (2020)"
    assert stats.days_at_or_above(tmax, 2020, 100) == 145
