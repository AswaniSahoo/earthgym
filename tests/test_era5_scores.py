import math

import numpy as np
import pytest

from earthgym.era5 import scores

LAT = np.array([-60.0, 0.0, 60.0])


def test_area_weights_are_cell_areas_normalised_to_mean_one():
    # bounds -90, -30, 30, 90 give sine differences 0.5, 1, 0.5
    np.testing.assert_allclose(scores.area_weights(LAT), [0.75, 1.5, 0.75])


def test_area_weights_give_polar_points_their_cell_area():
    # bounds -90, -45, 45, 90; cosine weights would give the poles 0
    np.testing.assert_allclose(
        scores.area_weights(np.array([-90.0, 0.0, 90.0])), [0.43934, 2.12132, 0.43934], rtol=1e-5
    )


def test_area_weights_on_a_grid_without_poles_follow_cosine_latitude():
    lat = np.linspace(-87.1875, 87.1875, 32)  # the WB2 64x32 grid
    cos = np.cos(np.deg2rad(lat))
    np.testing.assert_allclose(scores.area_weights(lat), cos / cos.mean())


def test_area_weights_refuse_latitudes_that_do_not_increase():
    with pytest.raises(ValueError):
        scores.area_weights(LAT[::-1])


def test_rmse_takes_the_root_after_the_mean_over_init_times():
    truth = np.zeros((2, 3, 1))  # init time, latitude, longitude
    forecast = truth.copy()
    forecast[0, 0, 0], forecast[1, 1, 0] = 1.0, 2.0  # per-init MSE 0.25 and 2.0
    assert scores.mse(forecast, truth, LAT) == pytest.approx(1.125)
    assert scores.rmse(forecast, truth, LAT) == pytest.approx(math.sqrt(1.125))


def test_bias_is_the_area_weighted_mean_of_forecast_minus_truth():
    truth = np.zeros((2, 3, 1))
    forecast = truth.copy()
    forecast[0, 0, 0], forecast[1, 1, 0] = 1.0, -2.0
    assert scores.bias(forecast, truth, LAT) == pytest.approx(-0.375)


def test_scores_compute_in_float64_whatever_the_input_dtype():
    rng = np.random.default_rng(0)
    forecast, truth = (1e5 + rng.normal(0, 100, (2, 3, 4, 5))).astype("f4")  # pressures in Pa
    lat = np.array([-60.0, -20.0, 20.0, 60.0])
    wide = scores.mse(forecast.astype("f8"), truth.astype("f8"), lat)
    assert scores.mse(forecast, truth, lat) == wide


def test_acc_is_one_when_forecast_anomalies_scale_the_truth_anomalies():
    clim = np.full((2, 3, 1), 10.0)
    truth = clim + np.array([1.0, -2.0, 0.5])[None, :, None]
    forecast = clim + 3 * (truth - clim)
    assert scores.acc(forecast, truth, clim, LAT) == pytest.approx(1.0)


def test_acc_pools_anomaly_statistics_over_init_times_before_the_ratio():
    # WeatherBench-X: per-init correlations here are 1 and -1 (mean 0), pooled gives -0.6
    clim = np.zeros((2, 3, 1))
    truth = np.stack([np.full((3, 1), 1.0), np.full((3, 1), 2.0)])
    forecast = np.stack([np.full((3, 1), 1.0), np.full((3, 1), -2.0)])
    assert scores.acc(forecast, truth, clim, LAT) == pytest.approx(-0.6)


def test_item_scores_weight_each_item_by_its_cell_area():
    w = np.array([3.0, 1.0])
    assert scores.item_rmse(np.array([1.0, 3.0]), np.zeros(2), w) == pytest.approx(math.sqrt(3))
    # anomalies f' = (1, -1), t' = (1, 1): covariance 0.5, both variances 1
    acc = scores.item_acc(np.array([1.0, -1.0]), np.ones(2), np.zeros(2), w)
    assert acc == pytest.approx(0.5)
