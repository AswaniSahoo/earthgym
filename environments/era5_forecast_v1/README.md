# era5-forecast-v1

Forecast tasks graded against ERA5 by the WeatherBench 2 rules (decision 0007). Each of the 720
items is one cell of the 64x32 grid, one variable (mean sea level pressure in Pa or 2 m
temperature in K), one 2020 init and one lead of 24, 48 or 72 h: 120 items per variable and
lead, seed 20261030. The prompt shows the cell's ERA5 values every 6 hours over the 72 h up to
the init and the ERA5 1990 to 2019 climatology at the valid time. The reply must end with a line
`ANSWER: <number>`.

Reward per item, from `era5_forecast_v1/contract.py`: with truth y, persistence p (the value at
the init), climatology c and forecast f, let b = min(|p - y|, |c - y|). The reward is
clip((b - |f - y|) / max(b, floor), 0, 1). Each variable's floor is the 10th percentile of b
over the items, 28.75 Pa and 0.069 K, and binds on 36 of 360 items each. Copying either
baseline from the prompt earns 0. Baseline rows for these items, IFS HRES included, are in
`reports/era5/items_v1_baselines.md`.

The grader behind the items reproduces two published WeatherBench 2 scores exactly
(`reports/era5/2026-10-30-wb2-reproduction.md`).

Rebuild the items from the repo root (about 55 MB over anonymous HTTPS; the store metadata is
pinned by sha256, and the file's sha256 is in `reports/era5/items_v1_manifest.json`):

    uv run python -m rlenv.era5.items

Checked offline on 2026-10-30:

    uv run vf-validate era5-forecast-v1 --only-noop --runtime.type subprocess   # 720 of 720 valid
    uv run vf-eval era5-forecast-v1 --dry-run --no-push -m <served model name>
    uv run inspect eval src/rlenv/era5/tasks.py@era5_forecast --model mockllm/model --limit 3

Attribution: contains modified Copernicus Climate Change Service information 2026. Neither the
European Commission nor ECMWF is responsible for any use that may be made of the Copernicus
information or data it contains. ERA5 is CC BY 4.0. The hidden HRES values are IFS HRES data,
European Centre for Medium-Range Weather Forecasts (ECMWF), CC BY 4.0, through WeatherBench 2.
