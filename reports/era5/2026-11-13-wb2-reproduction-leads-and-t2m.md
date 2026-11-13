# Reproducing WeatherBench 2 scores: IFS HRES mean sea level pressure and 2 m temperature at 24, 48 and 72 h, 2020

Date: 2026-11-13. Code: `src/earthgym/era5/scores.py` (unchanged) and `src/earthgym/era5/data.py`
(one pinned subset per variable and lead, `SUBSETS`, lines 33 to 55), on top of be5a0d0. Test:
`tests/test_era5_reproduction.py`, `test_hres_scores_match_the_published_wb2_scores_at_full_precision`
(published values at lines 17 to 24). This extends `reports/era5/2026-10-30-wb2-reproduction.md`,
which checked one of the six variable and lead pairs the environment's items cover
(`src/earthgym/era5/items.py:23-24`), to all six.

## Result

All 18 published scores reproduce. Full precision; the difference is this repo minus published,
in Pa for MSLP and K for 2 m temperature.

| variable, lead | metric | this repo | published | difference | relative |
|---|---|---|---|---|---|
| MSLP, 24 h | RMSE | 52.904653304583164 | 52.904653145321724 | 1.6e-7 | 3.0e-9 |
| MSLP, 24 h | ACC | 0.9971886063010693 | 0.9971886058859669 | 4.2e-10 | 4.2e-10 |
| MSLP, 24 h | bias | -0.27125367866993083 | -0.2712536786699314 | 5.6e-16 | 2.0e-15 |
| MSLP, 48 h | RMSE | 85.66972762210261 | 85.66972751392348 | 1.1e-7 | 1.3e-9 |
| MSLP, 48 h | ACC | 0.9926069902550205 | 0.9926069900243055 | 2.3e-10 | 2.3e-10 |
| MSLP, 48 h | bias | -0.38762019078002535 | -0.38762019078002596 | 6.1e-16 | 1.6e-15 |
| MSLP, 72 h | RMSE | 133.8905468754412 | 133.89054684361142 | 3.2e-8 | 2.4e-10 |
| MSLP, 72 h | ACC | 0.9818776392430146 | 0.9818776389291946 | 3.1e-10 | 3.2e-10 |
| MSLP, 72 h | bias | -0.4065775577911383 | -0.40657755779113947 | 1.2e-15 | 2.9e-15 |
| 2 m temperature, 24 h | RMSE | 0.6946667366883361 | 0.6946667366617497 | 2.7e-11 | 3.8e-11 |
| 2 m temperature, 24 h | ACC | 0.9575042390612649 | 0.9575042386624045 | 4.0e-10 | 4.2e-10 |
| 2 m temperature, 24 h | bias | -0.06717664052860826 | -0.06717664052860838 | 1.1e-16 | 1.7e-15 |
| 2 m temperature, 48 h | RMSE | 0.7788217819771848 | 0.7788217820190104 | -4.2e-11 | 5.4e-11 |
| 2 m temperature, 48 h | ACC | 0.9464664028299383 | 0.9464664025292318 | 3.0e-10 | 3.2e-10 |
| 2 m temperature, 48 h | bias | -0.08124392191780527 | -0.08124392191780541 | 1.4e-16 | 1.7e-15 |
| 2 m temperature, 72 h | RMSE | 0.8810727604521207 | 0.881072760502094 | -5.0e-11 | 5.7e-11 |
| 2 m temperature, 72 h | ACC | 0.9313474155222135 | 0.9313474152151214 | 3.1e-10 | 3.3e-10 |
| 2 m temperature, 72 h | bias | -0.0912898710563734 | -0.09128987105637354 | 1.4e-16 | 1.5e-15 |

Finding: the largest relative difference is 3.0e-9 (MSLP RMSE at 24 h); every ACC agrees within
4.2e-10 and every bias within 1.2e-15 in its own unit. No rule in `scores.py` needed a change: the
area weights, the one pooled mean over init time and grid, and the pooled ACC of the 2026-10-30
report give the published number for both variables at every lead. The 72 h MSLP row is the
2026-10-30 result, recomputed today from the same subset.

Tolerance: the test asks for agreement to relative float32 machine epsilon, 1.19e-7, for every
metric. The fields are float32 (`<f4` in each
store's `.zmetadata`), so a recomputation can claim float32 precision and no more; the 72 h MSLP
case agreed within 2.4e-10 (RMSE), 3.2e-10 (ACC) and 2.9e-15 (bias) relative. Every row here is at
least 39 times inside the tolerance.

Not established: why the MSLP RMSE differences at 24 and 48 h (3.0e-9 and 1.3e-9 relative) are
larger than at 72 h (2.4e-10), and the 2 m temperature ones smaller (3.8e-11 to 5.7e-11). All are
far inside float32 precision. The cause is UNKNOWN.

The published values are `rmse.<variable>`, `acc.<variable>` and `bias.<variable>` at the root of
`https://storage.googleapis.com/weatherbench2/benchmark_results/hres_vs_era5_64x32_2020.nc`,
dimensions (region, lead_time): region index 0, which the `region` character array decodes to
`global`, and lead_time indices 4, 8 and 12, which hold 24, 48 and 72 (its `units` attribute is
`hours`). On 2026-11-13 the file is still 1,469,120 bytes with sha256
`eec4fab627a3eac87fbada045bcf3507970a41fb3017c3c8dce7882e37e44947`, as on 2026-10-30. It was read
with `scipy.io.netcdf_file` (scipy 1.18.1, numpy 2.5.4) in a throwaway `uv run --no-project
--with scipy` environment; scipy is not a project dependency. The 72 h MSLP values read today equal
those in the 2026-10-30 report digit for digit.

## Config

- Forecast: `https://storage.googleapis.com/weatherbench2/datasets/hres/2016-2022-0012-64x32_equiangular_conservative.zarr`,
  `.zmetadata` sha256 `62811c8101885386acc33e3fe49641af74936d87eb2409ecf47dc193a777db9a`.
- Truth: `https://storage.googleapis.com/weatherbench2/datasets/era5/1959-2023_01_10-6h-64x32_equiangular_conservative.zarr`,
  `.zmetadata` sha256 `2a8290ef10bc7bebaa895bc17f42e305cdd004bdf9a0d92e0adae2cf39ba970d`.
- Climatology: `https://storage.googleapis.com/weatherbench2/datasets/era5-hourly-climatology/1990-2019_6h_64x32_equiangular_conservative.zarr`,
  `.zmetadata` sha256 `f876a07f4c65d5375abad6bca5bb5af3eb115ff6aedc9c125dfeccc2e187c474`,
  taken at each valid time's day of year and hour (WeatherBench-X `metrics/base.py`,
  `PerVariableStatisticWithClimatology`).
- The three `.zmetadata` hashes are the 2026-10-30 pins (`data.py`, `METADATA_SHA256`); every open
  checked them again on 2026-11-13 and they held.
- Variables `mean_sea_level_pressure` (Pa) and `2m_temperature` (K), units from each store's
  `.zattrs`. 732 inits, 2020-01-01T00 to 2020-12-31T12 every 12 h, the same for every lead; leads
  24, 48 and 72 h from `prediction_timedelta` (hours); truth at each init plus the lead. Grid 64
  longitudes by 32 latitudes, latitudes -87.1875 to 87.1875 increasing. No NaN in any field of the
  five new subsets.
- Subsets, not in git, each 17,997,770 bytes (18.0 MB), arrays `forecast`, `truth`, `climatology`
  (float32, 732 by 32 by 64), `latitude`, `longitude`, `init_time`:

  | file under `data/era5/` | content sha256 (pinned in `data.SUBSETS`) | file sha256 |
  |---|---|---|
  | `hres_era5_mslp_2020_24h.npz` | `be65437fa2787742cee94d089ceee4024995b7938db819209b74b757a0650d34` | `e5a49ce4fb810d598ddc484c464214bb1d5609ef94b9ae7d9e35e9415b8b9e2a` |
  | `hres_era5_mslp_2020_48h.npz` | `36f7aa5f7068de3166ce86b17a3a423ccb1862335ebd02a1bf67c50e05f97f75` | `1599b8d04b278ce08fab4932b8b35d50e47488e70e7fd40d7ae1ed8f41731aca` |
  | `hres_era5_mslp_2020_72h.npz` (2026-10-30) | `942c5f05a7c2471eecfa880db1b60bf9c19d6759b7b9f491dba9ccf40a51072e` | `1c3e9bc4cd4f3253a83d22a6c7daa07bf269edbb9c3defe443e7a6781775e189` |
  | `hres_era5_t2m_2020_24h.npz` | `3b9801f075bb7c1e8ac673858dbc65f9ebf49f20e7a733973d78a2b769de53d5` | `d2c2d6237ea90941e55db3e79b573c106f7380e9893d934cfb301aba5574f616` |
  | `hres_era5_t2m_2020_48h.npz` | `dcf7006369ced2c91596339bddb94f46eb84384ea41b6b986c9ee8d1acb6f80c` | `eb3da9d44f819dd8b9491681819fb282a64c6c1dec2f12caec08f2b08ad91402` |
  | `hres_era5_t2m_2020_72h.npz` | `9dacf0671c864c6642b2bf04305dd487317cc5f52a28ce8105d1957bea51c4e6` | `e1da51dc5892a51038288b167964b124f87ffacbde030902cc696f668b82863a` |

- Second build: `uv run python -m earthgym.era5.data --dir <scratch>` rebuilt all six from the
  stores on 2026-11-13 in 129 s. Each passed its content pin, equalled the first build array for
  array and had the same file sha256. The 72 h MSLP file built on 2026-10-30 has the same file
  sha256 as its rebuild today.
- Reads per subset, from the chunk shapes in `.zmetadata`: about 6 MB of HRES chunks (4 inits by 1
  lead by 64 by 32), 12 to 13 MB of ERA5 chunks (100 times by 64 by 32) and the 12 MB climatology
  chunk (4 hours by 366 days by 64 by 32), uncompressed. The stores compress with blosc lz4; the
  bytes on the wire were not measured cleanly (UNKNOWN).
- Rules: unchanged from decision 0006 and the 2026-10-30 report (cell-area weights, one
  area-weighted mean over init time, latitude and longitude, RMSE as its square root, pooled ACC,
  float64 throughout).
- Commands:

      uv sync --all-groups
      uv run python -m earthgym.era5.data      # six subsets, about 108 MB written, 129 s here
      uv run pytest -q -rs tests/test_era5_reproduction.py

## Limits

One year, two surface variables, three leads, the global region and the 64x32 grid. The regional
and land scores in the same file, other leads, pressure levels and the open question of where WB2
applies its below-ground mask are not covered. The cause of the spread in RMSE differences between
leads and variables is UNKNOWN (see Result).

## Attribution

Contains modified Copernicus Climate Change Service information 2026. Neither the European
Commission nor ECMWF is responsible for any use that may be made of the Copernicus information
or data it contains. ERA5 is CC BY 4.0. IFS HRES data: European Centre for Medium-Range Weather
Forecasts (ECMWF), CC BY 4.0, through WeatherBench 2 (`datasets/hres/LICENSE`).
