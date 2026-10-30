"""WeatherBench 2 scoring rules, ported to numpy (decision 0006).

Arrays are (init_time, latitude, longitude) with latitudes increasing. Sources:
weatherbench2/metrics.py at 1f1ff39b95 and weatherbenchX at 164dee38b4.
"""

import numpy as np


def area_weights(latitude: np.ndarray) -> np.ndarray:
    """Cell-area weights for increasing latitudes in degrees, normalised to mean 1.

    Cell bounds sit halfway between latitudes and the outer bounds half a step out, capped
    at the poles, as in weatherbenchX/weighting.py `latitude_cell_bounds`."""
    lat = np.deg2rad(np.asarray(latitude, dtype=float))
    step = np.diff(lat)
    if not (step > 0).all():
        raise ValueError("latitudes must increase")
    lower = max(lat[0] - step[0] / 2, -np.pi / 2)
    upper = min(lat[-1] + step[-1] / 2, np.pi / 2)
    bounds = np.concatenate([[lower], (lat[:-1] + lat[1:]) / 2, [upper]])
    weights = np.sin(bounds[1:]) - np.sin(bounds[:-1])
    return weights / weights.mean()


def _average(x: np.ndarray, weights: np.ndarray) -> float:
    return float(np.average(x, weights=np.broadcast_to(weights, x.shape)))


def _mean(x: np.ndarray, latitude: np.ndarray) -> float:
    """Area-weighted mean over init time, latitude and longitude together."""
    return _average(x, area_weights(latitude)[:, None])


def _pooled_acc(f: np.ndarray, t: np.ndarray, mean) -> float:
    """Pooled anomaly covariance over the root of the two pooled anomaly variances."""
    return float(mean(f * t) / np.sqrt(mean(f * f) * mean(t * t)))


def _error(forecast: np.ndarray, truth: np.ndarray) -> np.ndarray:
    """Forecast minus truth in float64, so float32 fields square without rounding loss."""
    return np.asarray(forecast, dtype=float) - np.asarray(truth, dtype=float)


def mse(forecast: np.ndarray, truth: np.ndarray, latitude: np.ndarray) -> float:
    return _mean(_error(forecast, truth) ** 2, latitude)


def rmse(forecast: np.ndarray, truth: np.ndarray, latitude: np.ndarray) -> float:
    """The root comes after the mean over init times (WB2 paper, eq. 2)."""
    return float(np.sqrt(mse(forecast, truth, latitude)))


def bias(forecast: np.ndarray, truth: np.ndarray, latitude: np.ndarray) -> float:
    return _mean(_error(forecast, truth), latitude)


def acc(
    forecast: np.ndarray, truth: np.ndarray, climatology: np.ndarray, latitude: np.ndarray
) -> float:
    """Anomaly correlation as WeatherBench-X reports it: the area-weighted means of the anomaly
    products over init time and grid come first and the ratio last (metrics/deterministic.py,
    ACC), not the mean of per-init correlations in the WB2 paper (eq. 5). The climatology is
    already aligned to each valid time."""
    f, t = _error(forecast, climatology), _error(truth, climatology)
    return _pooled_acc(f, t, lambda x: _mean(x, latitude))


def item_rmse(forecast: np.ndarray, truth: np.ndarray, weights: np.ndarray) -> float:
    """RMSE over separate items, each weighted by its cell's area weight."""
    return float(np.sqrt(_average(_error(forecast, truth) ** 2, weights)))


def item_acc(
    forecast: np.ndarray, truth: np.ndarray, climatology: np.ndarray, weights: np.ndarray
) -> float:
    """ACC over separate items, pooled as in `acc`, each item weighted by its cell's area."""
    f, t = _error(forecast, climatology), _error(truth, climatology)
    return _pooled_acc(f, t, lambda x: _average(x, weights))
