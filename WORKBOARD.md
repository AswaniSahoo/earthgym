# Workboard

Updated 2026-10-30. Publish after completion. Small commits, one-line messages.

## Now: Phase 3, ERA5 forecast-score environment graded against WeatherBench 2

Plan (2026-10-30, from the radar in docs/radar.md):

- Goal: an eval and RL environment whose answers are scored against ERA5 by the WeatherBench 2
  rules, with a grader shown to reproduce a number WB2 publishes.
- Stage 1, now: `rlenv.era5.scores` ports the WB2 rules (cell-area weights, MSE, RMSE with the
  root after the time mean, bias; ACC and CRPS after). A build step fetches a pinned subset
  over anonymous HTTPS (IFS HRES and ERA5 mean sea level pressure, 64x32, 2020 inits, 72 h
  lead, about 12 MB) and checks its sha256. The first test reproduces WB2's global MSLP RMSE
  at 72 h, 133.890547 Pa (`benchmark_results/hres_vs_era5_64x32_2020.nc`).
- Stage 2, proposed for Aswani: forecast-answer tasks. Each prompt gives a grid cell, a
  variable, a lead time, recent ERA5 history and climatology; the reply is a forecast; the
  reward is its skill against climatology under the WB2 rules, with HRES as the bar. The
  alternative is tasks that ask the model to compute the scores. Then a verifiers taskset
  and an Inspect task, tested on mockllm only.
- Out: pressure levels (one year of one level is over 100 MB), ARCO-ERA5, GraphCast and Pangu
  outputs (licence UNKNOWN), IFS ENS (research use only), any paid run.
- Tests: small inline arrays with hand-computed values; the reproduction test runs when the
  pinned subset is on disk and is skipped otherwise, so CI stays offline.

- [x] Radar check for Phase 3 (scout): 17 new entries in docs/radar.md
- [x] Decision 0006: numpy, zarr, numcodecs in an `era5` group; no xarray, gcsfs or
      weatherbench2 package
- [x] `rlenv.era5.scores`: area weights, MSE, RMSE, bias, in float64, test-first
- [x] Pinned subset (12.0 MB, content sha256 pinned) and the reproduction: 133.890547 Pa,
      equal to the published WB2 value; reports/era5/2026-10-30-wb2-reproduction.md
- [x] ACC against the 1990 to 2019 climatology: MSLP 0.981878, equal to the published value;
      pooled over inits as WeatherBench-X does (the WB2 paper's per-init mean gives 0.981470)
- [x] Decision 0007 accepted: forecast-answer tasks, reward clip((b - e) / max(b, floor), 0, 1)
      over the better of persistence and climatology
- [x] Stage 2 contract and reward (copying a baseline earns 0), prompt, 720 items from the
      pinned stores (about 55 MB read), baseline rows: reports/era5/items_v1_baselines.md
- [x] Stage 2: verifiers taskset (vf-validate 720 of 720) and Inspect task, tested on mockllm;
      environments/era5_forecast_v1/README.md
- [x] The 0005 review sheet: reports/climaqa/expert_review_v2.csv (83 rows, expert columns
      empty) and its instructions, expert_review_v2.md
- [x] Reward floors by rule, a technical choice: the 10th percentile of the better-baseline
      error per variable, 28.75 Pa and 0.069 K, each binding on 36 of 360 items
- [ ] Phase 3 review (Fable): reviews/phase-3-era5-forecast.md

## Waiting on Aswani

- [ ] reports/climaqa/leak_review.csv: 56 Gold and Silver pairs, same item or not
- [ ] reports/climaqa/review_sample.csv: 30 validated Gold MCQ items
- [ ] Name the domain expert for the 0005 review; the sheet is ready:
      reports/climaqa/expert_review_v2.csv

## Done

- [x] 2026-10-30 Phase 2 clean ClimaQA port: clean set v1 (350 items), one answer contract,
      Inspect tasks and verifiers taskset, Gemini 3.8 Flash baseline (MCQ 0.874, cloze 0.742),
      both miss sorts, two Fable reviews with every fix landed; reports/climaqa/runs/
- [x] 2026-10-30 Phase 1 ClimaQA audit; Fable review fixes landed test-first; CI green
- [x] 2026-10-30 CI runner pinned to ubuntu-24.04

## Later

- Two-model inspect_evals Register run: parked 2026-10-30; Gemini 3.8 Flash is the only
  baseline for now, and the second model needs Aswani's yes
- Phase 4 IBTrACS cyclone analytics environment
- Phase 5 heat-insurance basis-risk environment
- Before publishing: LICENSE, write-up, blog posts from reports/
