"""Pinned subset of the WeatherBench 2 stores for the Phase 3 reproduction (decision 0006).

uv run python -m rlenv.era5.data   # about 12 MB over anonymous HTTPS, writes data/era5/

IFS HRES 72 h forecasts of mean sea level pressure from the 732 inits of 2020 and the ERA5
values at their valid times, 64x32, as (init_time, latitude, longitude). ERA5 is CC BY 4.0
(Copernicus notice required) and HRES is CC BY 4.0 with the ECMWF credit (docs/radar.md).
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
METADATA_SHA256 = {  # .zmetadata of each store, read 2026-10-30
    ERA5: "2a8290ef10bc7bebaa895bc17f42e305cdd004bdf9a0d92e0adae2cf39ba970d",
    HRES: "62811c8101885386acc33e3fe49641af74936d87eb2409ecf47dc193a777db9a",
}
VARIABLE = "mean_sea_level_pressure"
FIRST_INIT, INITS, LEAD_HOURS = datetime(2020, 1, 1), 732, 72  # 2020, every 12 h
SUBSET = Path("data/era5/hres_era5_mslp_2020_72h.npz")
SUBSET_SHA256 = "866916061a708efd1192cd6f2ee506fdbf6fc99577fdd18b68b054a44e3334a2"  # 2026-10-30


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


def content_sha256(arrays: dict[str, np.ndarray]) -> str:
    """Hash of names, dtypes, shapes and values, independent of the file container."""
    digest = hashlib.sha256()
    for name in sorted(arrays):
        array = np.ascontiguousarray(arrays[name])
        digest.update(f"{name} {array.dtype.str} {array.shape}\n".encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def load(path: Path = SUBSET) -> dict[str, np.ndarray]:
    with np.load(path) as stored:
        arrays = {name: stored[name] for name in stored.files}
    if (got := content_sha256(arrays)) != SUBSET_SHA256:
        raise ValueError(f"{path} does not match the pinned subset (sha256 {got})")
    return arrays


def _open(store: str):
    import zarr  # build-time only
    from zarr.storage import FsspecStore

    url = f"{BASE}/{store}"
    with urllib.request.urlopen(f"{url}/.zmetadata", timeout=60) as response:
        got = hashlib.sha256(response.read()).hexdigest()
    if got != METADATA_SHA256[store]:
        raise ValueError(f"{store} metadata changed (sha256 {got})")
    store = FsspecStore.from_url(url, read_only=True)
    return zarr.open_group(store=store, mode="r", zarr_format=2, use_consolidated=True)


def build() -> dict[str, np.ndarray]:
    """Read the subset from the two stores; about 12 MB of chunks."""
    era5, hres = _open(ERA5), _open(HRES)
    inits = [FIRST_INIT + timedelta(hours=12 * k) for k in range(INITS)]
    lead = timedelta(hours=LEAD_HOURS)

    def hours(group, when):
        return [int((t - epoch(group["time"].attrs["units"])) / timedelta(hours=1)) for t in when]

    h = positions(hres["time"][:], hours(hres, inits))
    e = positions(era5["time"][:], hours(era5, [t + lead for t in inits]))
    k = positions(hres["prediction_timedelta"][:], [LEAD_HOURS])[0]
    if not (np.diff(h) == 1).all():
        raise ValueError("HRES inits are not consecutive in the store")
    forecast = hres[VARIABLE][h[0] : h[-1] + 1, k]  # (init, longitude, latitude)
    truth = era5[VARIABLE][e[0] : e[-1] + 1][e - e[0]]  # contiguous read, then the valid times
    latitude, longitude = hres["latitude"][:], hres["longitude"][:]
    same = np.array_equal(latitude, era5["latitude"][:]) and np.array_equal(
        longitude, era5["longitude"][:]
    )
    if not same or not (np.diff(latitude) > 0).all():
        raise ValueError("the stores disagree on the grid, or latitude does not increase")
    return {
        "forecast": np.transpose(forecast, (0, 2, 1)),
        "truth": np.transpose(truth, (0, 2, 1)),
        "latitude": latitude,
        "longitude": longitude,
        "init_time": np.array(inits, dtype="datetime64[h]"),
    }


def fetch(out: Path = SUBSET) -> Path:
    arrays = build()
    if (got := content_sha256(arrays)) != SUBSET_SHA256:
        raise ValueError(f"the stores no longer give the pinned subset (sha256 {got})")
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **arrays)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the pinned ERA5 and HRES subset.")
    parser.add_argument("--out", type=Path, default=SUBSET)
    print(f"wrote {fetch(parser.parse_args().out)}")


if __name__ == "__main__":
    main()
