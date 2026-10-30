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


def _mean(x: np.ndarray, latitude: np.ndarray) -> float:
    """Area-weighted mean over init time, latitude and longitude together."""
    weights = np.broadcast_to(area_weights(latitude)[:, None], x.shape)
    return float(np.average(x, weights=weights))


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
