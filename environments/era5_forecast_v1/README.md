# era5-forecast-v1

Forecast tasks scored against ERA5 (decision 0007). The reward is a custom clipped skill score over
persistence and climatology; the WeatherBench 2 rules give the area-weighted RMSE and ACC that the
reports show as reference metrics, not the reward. Each of the 648 items is one cell of the 64x32
grid, one variable (mean sea level pressure in Pa or 2 m temperature in K), one 2020 init and one
lead of 24, 48 or 72 h: 720 drawn, 120 per variable and lead, seed 20261030, of which 648 pass the
gold check (decision 0021). The prompt shows the cell's ERA5 values every 6 hours over the 72 h up
to the init and the ERA5 1990 to 2019 climatology at the valid time. The reply must end with a line
`ANSWER: <number>`.

Reward per item, from `era5_forecast_v1/contract.py`: with truth y, persistence p (the value at the
init), climatology c and forecast f, let b = min(|p - y|, |c - y|). The reward is clip((b - |f - y|)
/ max(b, floor), 0, 1). Each variable's floor is the 10th percentile of b over the 720 drawn items,
28.75 Pa and 0.069 K. A perfect forecast earns b / floor where the floor binds, so the 72 items
where it did (36 per variable, 3 of them unwinnable) failed the gold check and left the set; on the
648 that remain a perfect forecast earns 1. Copying either baseline from the prompt earns 0. The
baseline is picked with the truth known, so where one of the two is nearly exact little skill is
left to earn (Limits in `reports/era5/items_v1_baselines.md`). Baseline rows for these items, IFS
HRES included, are in `reports/era5/items_v1_baselines.md`.

A held-out split keeps each ISO week of init times on one side: `ForecastConfig(split="train")`
loads 546 items and `split="test"` 102 (decision 0017).

The grader behind the items reproduces two published WeatherBench 2 scores exactly
(`reports/era5/2026-10-30-wb2-reproduction.md`).

Rebuild the items from the repo root (about 55 MB over anonymous HTTPS; the store metadata is
pinned by sha256, and `reports/era5/items_v1_manifest.json` holds the file's sha256 and
`fields_sha256`, a hash of every array the builder reads, which a rebuild checks first):

    uv run python -m earthgym.era5.items

Checked offline on 2026-10-30, the gold check on 2026-11-02:

    uv run vf-validate era5-forecast-v1 --runtime.type subprocess   # gold and untouched, 648 valid
    uv run vf-eval era5-forecast-v1 --dry-run --no-push -m <served model name>
    uv run inspect eval src/earthgym/era5/tasks.py@era5_forecast --model mockllm/model --limit 3

Attribution: contains modified Copernicus Climate Change Service information 2026. Neither the
European Commission nor ECMWF is responsible for any use that may be made of the Copernicus
information or data it contains. ERA5 is CC BY 4.0. The hidden HRES values are IFS HRES data,
European Centre for Medium-Range Weather Forecasts (ECMWF), CC BY 4.0, through WeatherBench 2.
