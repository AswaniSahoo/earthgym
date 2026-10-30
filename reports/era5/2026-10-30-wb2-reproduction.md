# Reproducing a WeatherBench 2 score: IFS HRES mean sea level pressure, day 3, 2020

Date: 2026-10-30. Code: `src/rlenv/era5/scores.py` and `src/rlenv/era5/data.py` at commit
9d0d473. Test: `tests/test_era5_reproduction.py`.

## Result

| quantity | ours | published |
|---|---|---|
| global RMSE of IFS HRES MSLP against ERA5, 72 h lead, 2020 inits, 64x32 | 133.890547 Pa | 133.890547 Pa |
| global bias, same setup | -0.406578 Pa | not checked (UNKNOWN) |

The published value is `rmse` for region global, lead 72 h, in
`gs://weatherbench2/benchmark_results/hres_vs_era5_64x32_2020.nc`, as read by the Phase 3 radar
check (`docs/radar.md`); its metric set is WeatherBench-X `public_benchmark`. This session did not
open that file itself. A match to all six published decimals is the check that the grader
follows the WB2 rules on this grid.

## Config

- Forecast: `https://storage.googleapis.com/weatherbench2/datasets/hres/2016-2022-0012-64x32_equiangular_conservative.zarr`,
  `.zmetadata` sha256 `62811c8101885386acc33e3fe49641af74936d87eb2409ecf47dc193a777db9a`.
- Truth: `https://storage.googleapis.com/weatherbench2/datasets/era5/1959-2023_01_10-6h-64x32_equiangular_conservative.zarr`,
  `.zmetadata` sha256 `2a8290ef10bc7bebaa895bc17f42e305cdd004bdf9a0d92e0adae2cf39ba970d`.
- Variable `mean_sea_level_pressure` (Pa). 732 inits, 2020-01-01T00 to 2020-12-31T12 every
  12 h; lead 72 h; truth at each valid time. Grid 64 longitudes by 32 latitudes, latitudes
  -87.1875 to 87.1875 increasing. No NaN in either field.
- Subset: `data/era5/hres_era5_mslp_2020_72h.npz` (12.0 MB, not in git), content sha256
  `866916061a708efd1192cd6f2ee506fdbf6fc99577fdd18b68b054a44e3334a2`. A second, fresh build
  passed the same hash and equalled the first array for array.
- Rules (decision 0006): cell-area weights, sine of the upper cell bound minus sine of the
  lower, normalised to mean 1 (`weatherbench2/metrics.py` at 1f1ff39b95, lines 40 to 61;
  `weatherbenchX/weighting.py` at 164dee38b4, lines 62 to 128); MSE as one area-weighted mean
  over init time, latitude and longitude (`public_benchmark/run_benchmark_evaluation.py` at
  164dee38b4, lines 371 to 380); RMSE as its square root; float64 throughout.
- Commands:

      uv sync --all-groups
      uv run python -m rlenv.era5.data      # about 12 MB, anonymous HTTPS, 42 s here
      uv run pytest tests/test_era5_reproduction.py

## Limits

One variable, one lead time, one year. ACC, pressure levels (each year of one level is over
100 MB) and the open question of where WB2 applies its below-ground mask are not covered yet.

## Attribution

Contains modified Copernicus Climate Change Service information 2026. Neither the European
Commission nor ECMWF is responsible for any use that may be made of the Copernicus information
or data it contains. ERA5 is CC BY 4.0. IFS HRES data: European Centre for Medium-Range Weather
Forecasts (ECMWF), CC BY 4.0, through WeatherBench 2 (`datasets/hres/LICENSE`).
