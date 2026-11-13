"""Reproduce numbers WeatherBench 2 publishes, from the pinned subsets (skipped without them)."""

from functools import cache

import numpy as np
import pytest

from earthgym.era5 import data, scores

pytestmark = pytest.mark.skipif(
    not data.SUBSET.exists(), reason="no pinned subset; run uv run python -m earthgym.era5.data"
)
# rmse.<variable>, acc.<variable> and bias.<variable> at region "global" and lead_time 24, 48
# and 72 hours in gs://weatherbench2/benchmark_results/hres_vs_era5_64x32_2020.nc, sha256
# eec4fab627a3eac87fbada045bcf3507970a41fb3017c3c8dce7882e37e44947, read at full precision on
# 2026-11-13
PUBLISHED = {  # (variable, lead hours): (rmse, acc, bias)
    ("mean_sea_level_pressure", 24): (52.904653145321724, 0.9971886058859669, -0.2712536786699314),
    ("mean_sea_level_pressure", 48): (85.66972751392348, 0.9926069900243055, -0.38762019078002596),
    ("mean_sea_level_pressure", 72): (133.89054684361142, 0.9818776389291946, -0.40657755779113947),
    ("2m_temperature", 24): (0.6946667366617497, 0.9575042386624045, -0.06717664052860838),
    ("2m_temperature", 48): (0.7788217820190104, 0.9464664025292318, -0.08124392191780541),
    ("2m_temperature", 72): (0.881072760502094, 0.9313474152151214, -0.09128987105637354),
}
# The fields are float32, so a recomputation can claim agreement to float32 precision and no
# further; the 72 h MSLP case agrees within 2.4e-10 (RMSE), 3.2e-10 (ACC) and 2.9e-15 (bias)
# relative (reports/era5/2026-11-13-wb2-reproduction-leads-and-t2m.md).
FLOAT32 = float(np.finfo(np.float32).eps)


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


@cache
def subset(variable: str, lead: int) -> dict:
    path, pin = data.SUBSETS[(variable, lead)]
    if not path.exists():
        pytest.skip(f"no {path}; run uv run python -m earthgym.era5.data")
    return data.load(path, pin)


@pytest.mark.parametrize("metric", ["rmse", "acc", "bias"])
@pytest.mark.parametrize(("variable", "lead"), list(PUBLISHED))
def test_hres_scores_match_the_published_wb2_scores_at_full_precision(variable, lead, metric):
    s = subset(variable, lead)
    if metric == "acc":
        got = scores.acc(s["forecast"], s["truth"], s["climatology"], s["latitude"])
    else:
        got = getattr(scores, metric)(s["forecast"], s["truth"], s["latitude"])
    published = PUBLISHED[(variable, lead)][["rmse", "acc", "bias"].index(metric)]
    assert got == pytest.approx(published, rel=FLOAT32)
