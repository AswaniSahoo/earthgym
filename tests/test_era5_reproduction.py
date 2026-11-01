"""Reproduce a number WeatherBench 2 publishes, from the pinned subset (skipped without it)."""

import pytest

from earthgym.era5 import data, scores

pytestmark = pytest.mark.skipif(
    not data.SUBSET.exists(), reason="no pinned subset; run uv run python -m earthgym.era5.data"
)


def test_mslp_rmse_at_72_hours_matches_the_published_wb2_score():
    # gs://weatherbench2/benchmark_results/hres_vs_era5_64x32_2020.nc: rmse, global, 72 h
    subset = data.load()
    rmse = scores.rmse(subset["forecast"], subset["truth"], subset["latitude"])
    assert rmse == pytest.approx(133.890547, abs=5e-7)


def test_mslp_acc_at_72_hours_matches_the_published_wb2_score():
    # same file: acc, global, 72 h, against the ERA5 1990 to 2019 climatology
    s = data.load()
    acc = scores.acc(s["forecast"], s["truth"], s["climatology"], s["latitude"])
    assert acc == pytest.approx(0.981878, abs=5e-7)


def test_mslp_bias_at_72_hours_matches_the_published_wb2_score():
    # same file: bias, global, 72 h (-0.40657755779113947 Pa, read 2026-10-30)
    s = data.load()
    bias = scores.bias(s["forecast"], s["truth"], s["latitude"])
    assert bias == pytest.approx(-0.406578, abs=5e-7)
