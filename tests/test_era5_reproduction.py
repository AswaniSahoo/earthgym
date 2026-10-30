"""Reproduce a number WeatherBench 2 publishes, from the pinned subset (skipped without it)."""

import pytest

from rlenv.era5 import data, scores

pytestmark = pytest.mark.skipif(
    not data.SUBSET.exists(), reason="no pinned subset; run uv run python -m rlenv.era5.data"
)


def test_mslp_rmse_at_72_hours_matches_the_published_wb2_score():
    # gs://weatherbench2/benchmark_results/hres_vs_era5_64x32_2020.nc: rmse, global, 72 h
    subset = data.load()
    rmse = scores.rmse(subset["forecast"], subset["truth"], subset["latitude"])
    assert rmse == pytest.approx(133.890547, abs=5e-7)
