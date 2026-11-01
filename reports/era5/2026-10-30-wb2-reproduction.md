# Reproducing a WeatherBench 2 score: IFS HRES mean sea level pressure, day 3, 2020

Date: 2026-10-30. Code: `src/earthgym/era5/scores.py` and `src/earthgym/era5/data.py`, first
reproduced at commit 2d97668; the code changed since (3b2a5a7, 3713c87) and the reproduction
tests still pass at 37e6636. Test: `tests/test_era5_reproduction.py`.

## Result

| quantity | this repo | published |
|---|---|---|
| global RMSE of IFS HRES MSLP against ERA5, 72 h lead, 2020 inits, 64x32 | 133.890547 Pa | 133.890547 Pa |
| global ACC against the ERA5 1990 to 2019 climatology, same setup | 0.981878 | 0.981878 |
| global bias, same setup | -0.406578 Pa | -0.406578 Pa |

Finding: the published ACC pools the anomaly statistics over all inits before the ratio
(WeatherBench-X `metrics/deterministic.py`, `ACC._values_from_mean_statistics_per_variable`, at
164dee38b4). The WB2 paper's eq. 5, the mean of per-init correlations, gives 0.981470 on the
same data, 0.0004 lower. A grader built from the paper alone would miss the published number in
the fourth decimal.

The published values are `rmse`, `acc` and `bias` for region global, lead 72 h, in
`https://storage.googleapis.com/weatherbench2/benchmark_results/hres_vs_era5_64x32_2020.nc`
(1,469,120 bytes, sha256 `eec4fab627a3eac87fbada045bcf3507970a41fb3017c3c8dce7882e37e44947`),
read at its root on 2026-10-30 with `scipy.io.netcdf_file` in a throwaway `uv run --with scipy`
environment; its metric set is WeatherBench-X `public_benchmark`. Full precision, published
against this repo's: RMSE 133.89054684361142 against 133.8905468754412 Pa (difference 3.2e-8), ACC
0.9818776389291946 against 0.9818776392430146 (3.1e-10), bias -0.40657755779113947 against
-0.4065775577911383 Pa (1.2e-15). The grader follows the WB2 rules on this grid to float32
accumulation error.

## Config

- Forecast: `https://storage.googleapis.com/weatherbench2/datasets/hres/2016-2022-0012-64x32_equiangular_conservative.zarr`,
  `.zmetadata` sha256 `62811c8101885386acc33e3fe49641af74936d87eb2409ecf47dc193a777db9a`.
- Truth: `https://storage.googleapis.com/weatherbench2/datasets/era5/1959-2023_01_10-6h-64x32_equiangular_conservative.zarr`,
  `.zmetadata` sha256 `2a8290ef10bc7bebaa895bc17f42e305cdd004bdf9a0d92e0adae2cf39ba970d`.
- Climatology: `https://storage.googleapis.com/weatherbench2/datasets/era5-hourly-climatology/1990-2019_6h_64x32_equiangular_conservative.zarr`,
  `.zmetadata` sha256 `f876a07f4c65d5375abad6bca5bb5af3eb115ff6aedc9c125dfeccc2e187c474`,
  taken at each valid time's day of year and hour (WeatherBench-X `metrics/base.py`,
  `PerVariableStatisticWithClimatology`).
- Variable `mean_sea_level_pressure` (Pa). 732 inits, 2020-01-01T00 to 2020-12-31T12 every
  12 h; lead 72 h; truth at each valid time. Grid 64 longitudes by 32 latitudes, latitudes
  -87.1875 to 87.1875 increasing. No NaN in any field.
- Subset: `data/era5/hres_era5_mslp_2020_72h.npz` (18.0 MB, not in git), content sha256
  `942c5f05a7c2471eecfa880db1b60bf9c19d6759b7b9f491dba9ccf40a51072e`. A second, fresh build
  passed the same hash and equalled the first array for array.
- Rules (decision 0006): cell-area weights, sine of the upper cell bound minus sine of the
  lower, normalised to mean 1 (`weatherbench2/metrics.py` at 1f1ff39b95, lines 40 to 61;
  `weatherbenchX/weighting.py` at 164dee38b4, lines 62 to 128); MSE as one area-weighted mean
  over init time, latitude and longitude (`public_benchmark/run_benchmark_evaluation.py` at
  164dee38b4, lines 371 to 380); RMSE as its square root; ACC as the pooled anomaly covariance
  over the root of the two pooled anomaly variances; float64 throughout.
- Commands:

      uv sync --all-groups
      uv run python -m earthgym.era5.data      # about 19 MB, anonymous HTTPS, about 35 s here
      uv run pytest tests/test_era5_reproduction.py

## Limits

One variable, one lead time, one year. Pressure levels (each year of one level is over
100 MB) and the open question of where WB2 applies its below-ground mask are not covered yet.

## Attribution

Contains modified Copernicus Climate Change Service information 2026. Neither the European
Commission nor ECMWF is responsible for any use that may be made of the Copernicus information
or data it contains. ERA5 is CC BY 4.0. IFS HRES data: European Centre for Medium-Range Weather
Forecasts (ECMWF), CC BY 4.0, through WeatherBench 2 (`datasets/hres/LICENSE`).
