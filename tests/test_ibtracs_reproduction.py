"""Reproduce NCEI's published North Atlantic numbers from the pinned IBTrACS file (skipped
without it). Sources: NCEI annual tropical cyclone reports 202413 and 202513 and NHC's 2024
summary, as listed in docs/radar.md."""

import hashlib

import pytest

from rlenv.ibtracs import data, stats

pytestmark = pytest.mark.skipif(
    not data.PATH.exists(), reason="no pinned file; run uv run python -m rlenv.ibtracs.data"
)


@pytest.fixture(scope="module")
def rows():
    assert hashlib.sha256(data.PATH.read_bytes()).hexdigest() == data.SHA256  # never fetch
    return data.read(columns=stats.COLUMNS)


def test_1933_ace_is_the_published_record(rows):
    assert stats.season(rows, 1933)["ace"] == pytest.approx(258.6, abs=0.05)


def test_2005_hurricane_counts(rows):
    s = stats.season(rows, 2005)
    assert (s["hurricanes"], s["major"]) == (15, 7)


def test_2020_named_storm_and_major_hurricane_counts(rows):
    s = stats.season(rows, 2020)
    assert (s["named"], s["major"]) == (30, 7)


def test_2024_season(rows):
    s = stats.season(rows, 2024)
    assert (s["named"], s["hurricanes"], s["major"]) == (18, 11, 5)
    assert s["ace"] == pytest.approx(161.6, abs=0.05)
