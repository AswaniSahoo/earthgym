# 0006: numpy for the WeatherBench 2 scores; zarr and numcodecs to read the stores

Date: 2026-10-30. Status: accepted.

Context: Phase 3 scores forecasts against ERA5 with the WeatherBench 2 rules and must reproduce
a number WB2 publishes (`docs/radar.md`, Phase 3 rows). The WB2 stores are Zarr v2 with blosc
lz4 chunks on anonymous HTTPS, and the standard library has no lz4 or blosc decoder. The
weatherbench2 package pulls in apache_beam and jax; WeatherBench-X, which produced the
published numbers, adds gcsfs, whose current release conflicts with the fsspec pin that
inspect-ai brings.

Decision: an `era5` dependency group with `numpy==2.5.4` for the scores and `zarr==3.4.2` and
`numcodecs==0.17.1` for build-time reads through fsspec's HTTP filesystem (fsspec and aiohttp
are already locked through inspect-ai). The rules are ported, not imported: area weights from
`weatherbench2/metrics.py` at 1f1ff39b95 (lines 40 to 61) and `weatherbenchX/weighting.py` at
164dee38b4 (lines 62 to 128), and the reduction over init time, latitude and longitude from
`public_benchmark/run_benchmark_evaluation.py` at 164dee38b4 (lines 371 to 380). No xarray,
gcsfs, weatherbench2 or weatherbenchX. numcodecs 0.17.1 is the release whose notes say
"`Pickle.decode` now refuses to unpickle data unless the process opts in".

Consequences: the scores and the build step need the group; the environment package should
not. CI installs it (`--all-groups`) and stays offline, because the reproduction test skips
when the pinned subset is not on disk.
