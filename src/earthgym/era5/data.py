"""Pinned subsets of the WeatherBench 2 stores for the Phase 3 reproduction (decision 0006).

uv run python -m earthgym.era5.data   # six subsets over anonymous HTTPS, writes data/era5/

IFS HRES forecasts of mean sea level pressure and 2 m temperature at 24, 48 and 72 h from the
732 inits of 2020, the ERA5 values at their valid times and the ERA5 1990 to 2019 climatology
aligned to them, 64x32, as (init_time, latitude, longitude), one subset per variable and lead.
ERA5 is CC BY 4.0 (Copernicus notice required) and HRES is CC BY 4.0 with the ECMWF credit
(docs/radar.md).
"""

import argparse
import hashlib
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

BASE = "https://storage.googleapis.com/weatherbench2/datasets"
ERA5 = "era5/1959-2023_01_10-6h-64x32_equiangular_conservative.zarr"
HRES = "hres/2016-2022-0012-64x32_equiangular_conservative.zarr"
CLIMATOLOGY = "era5-hourly-climatology/1990-2019_6h_64x32_equiangular_conservative.zarr"
METADATA_SHA256 = {  # .zmetadata of each store, read 2026-10-30
    ERA5: "2a8290ef10bc7bebaa895bc17f42e305cdd004bdf9a0d92e0adae2cf39ba970d",
    HRES: "62811c8101885386acc33e3fe49641af74936d87eb2409ecf47dc193a777db9a",
    CLIMATOLOGY: "f876a07f4c65d5375abad6bca5bb5af3eb115ff6aedc9c125dfeccc2e187c474",
}
VARIABLE = "mean_sea_level_pressure"
FIRST_INIT, INITS, LEAD_HOURS = datetime(2020, 1, 1), 732, 72  # 2020, every 12 h
SUBSET = Path("data/era5/hres_era5_mslp_2020_72h.npz")
SUBSET_SHA256 = "942c5f05a7c2471eecfa880db1b60bf9c19d6759b7b9f491dba9ccf40a51072e"  # 2026-10-30
SUBSETS = {  # (variable, lead hours): (path, content sha256); the one above, then 2026-11-13
    (VARIABLE, LEAD_HOURS): (SUBSET, SUBSET_SHA256),
    (VARIABLE, 24): (
        Path("data/era5/hres_era5_mslp_2020_24h.npz"),
        "be65437fa2787742cee94d089ceee4024995b7938db819209b74b757a0650d34",
    ),
    (VARIABLE, 48): (
        Path("data/era5/hres_era5_mslp_2020_48h.npz"),
        "36f7aa5f7068de3166ce86b17a3a423ccb1862335ebd02a1bf67c50e05f97f75",
    ),
    ("2m_temperature", 24): (
        Path("data/era5/hres_era5_t2m_2020_24h.npz"),
        "3b9801f075bb7c1e8ac673858dbc65f9ebf49f20e7a733973d78a2b769de53d5",
    ),
    ("2m_temperature", 48): (
        Path("data/era5/hres_era5_t2m_2020_48h.npz"),
        "dcf7006369ced2c91596339bddb94f46eb84384ea41b6b986c9ee8d1acb6f80c",
    ),
    ("2m_temperature", 72): (
        Path("data/era5/hres_era5_t2m_2020_72h.npz"),
        "9dacf0671c864c6642b2bf04305dd487317cc5f52a28ce8105d1957bea51c4e6",
    ),
}


def epoch(units: str) -> datetime:
    """The reference time of CF units such as 'hours since 1959-01-01'."""
    return datetime.fromisoformat(units.removeprefix("hours since ").strip())


def positions(times: np.ndarray, wanted: list[int]) -> np.ndarray:
    """Index of each wanted value in times; every one must be present."""
    index = {int(t): i for i, t in enumerate(times)}
    missing = [w for w in wanted if w not in index]
    if missing:
        raise ValueError(f"{len(missing)} times not in the store, first {missing[0]}")
    return np.array([index[w] for w in wanted])


def align(
    climatology: np.ndarray, hours: np.ndarray, days: np.ndarray, valid_times: list[datetime]
) -> np.ndarray:
    """The climatology (hour, dayofyear, ...) at each valid time's hour and day of year, as
    WeatherBench-X selects it (metrics/base.py, PerVariableStatisticWithClimatology)."""
    h = positions(hours, [t.hour for t in valid_times])
    d = positions(days, [t.timetuple().tm_yday for t in valid_times])
    return climatology[h, d]


def content_sha256(arrays: dict[str, np.ndarray]) -> str:
    """Hash of names, dtypes, shapes and values, independent of the file container."""
    digest = hashlib.sha256()
    for name in sorted(arrays):
        array = np.ascontiguousarray(arrays[name])
        digest.update(f"{name} {array.dtype.str} {array.shape}\n".encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def load(path: Path = SUBSET, sha256: str | None = None) -> dict[str, np.ndarray]:
    """A subset's arrays, checked against its pin (by default the 72 h MSLP one)."""
    with np.load(path) as stored:
        arrays = {name: stored[name] for name in stored.files}
    if (got := content_sha256(arrays)) != (SUBSET_SHA256 if sha256 is None else sha256):
        raise ValueError(f"{path} does not match the pinned subset (sha256 {got})")
    return arrays


def open_store(store: str):
    """A read-only zarr group for one pinned store, after checking its metadata hash."""
    import zarr  # build-time only
    from zarr.storage import FsspecStore

    url = f"{BASE}/{store}"
    with urllib.request.urlopen(f"{url}/.zmetadata", timeout=60) as response:
        got = hashlib.sha256(response.read()).hexdigest()
    if got != METADATA_SHA256[store]:
        raise ValueError(f"{store} metadata changed (sha256 {got})")
    store = FsspecStore.from_url(url, read_only=True)
    return zarr.open_group(store=store, mode="r", zarr_format=2, use_consolidated=True)


def store_hours(group, when: list[datetime]) -> list[int]:
    """Times as the store's own 'hours since' integers."""
    origin = epoch(group["time"].attrs["units"])
    return [int((t - origin) / timedelta(hours=1)) for t in when]


def grid(*groups) -> tuple[np.ndarray, np.ndarray]:
    """The latitude and longitude every group shares; latitude must increase."""
    latitude, longitude = groups[0]["latitude"][:], groups[0]["longitude"][:]
    same = all(
        np.array_equal(latitude, g["latitude"][:]) and np.array_equal(longitude, g["longitude"][:])
        for g in groups[1:]
    )
    if not same or not (np.diff(latitude) > 0).all():
        raise ValueError("the stores disagree on the grid, or latitude does not increase")
    return latitude, longitude


def build(variable: str = VARIABLE, lead_hours: int = LEAD_HOURS) -> dict[str, np.ndarray]:
    """Read one subset from the three stores."""
    era5, hres, clim = open_store(ERA5), open_store(HRES), open_store(CLIMATOLOGY)
    inits = [FIRST_INIT + timedelta(hours=12 * k) for k in range(INITS)]
    valid = [t + timedelta(hours=lead_hours) for t in inits]
    h = positions(hres["time"][:], store_hours(hres, inits))
    e = positions(era5["time"][:], store_hours(era5, valid))
    k = positions(hres["prediction_timedelta"][:], [lead_hours])[0]
    if not (np.diff(h) == 1).all():
        raise ValueError("HRES inits are not consecutive in the store")
    forecast = hres[variable][h[0] : h[-1] + 1, k]  # (init, longitude, latitude)
    truth = era5[variable][e[0] : e[-1] + 1][e - e[0]]  # contiguous read, then the valid times
    normals = align(clim[variable][:], clim["hour"][:], clim["dayofyear"][:], valid)
    latitude, longitude = grid(hres, era5, clim)
    return {
        "forecast": np.transpose(forecast, (0, 2, 1)),
        "truth": np.transpose(truth, (0, 2, 1)),
        "climatology": np.transpose(normals, (0, 2, 1)),
        "latitude": latitude,
        "longitude": longitude,
        "init_time": np.array(inits, dtype="datetime64[h]"),
    }


def fetch(variable: str = VARIABLE, lead_hours: int = LEAD_HOURS, out: Path | None = None) -> Path:
    path, pin = SUBSETS[(variable, lead_hours)]
    arrays = build(variable, lead_hours)
    if (got := content_sha256(arrays)) != pin:
        raise ValueError(f"the stores no longer give the pinned {path.name} (sha256 {got})")
    out = out or path
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **arrays)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the pinned ERA5 and HRES subsets.")
    parser.add_argument("--dir", type=Path, default=SUBSET.parent)
    folder = parser.parse_args().dir
    for (variable, lead), (path, _) in SUBSETS.items():
        print(f"wrote {fetch(variable, lead, folder / path.name)}")


if __name__ == "__main__":
    main()
