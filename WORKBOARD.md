# Workboard

Updated 2026-11-01. Publish after completion. Small commits, one-line messages.

## Now: Phase 4, IBTrACS cyclone analytics environment

- [ ] Radar check for Phase 4 (scout, running)
- [ ] A short plan here, from the radar
- [ ] Build test-first in small commits: public data only, pinned by hash, every download
      under 100 MB (a per-basin or per-season subset)

## Parked: Jev as a third reader of the ClimaQA misses (decision 0008)

Parked 2026-11-01 by Aswani: there is no TypeSafe key now. The code stays as it is; nothing
was called or spent.

- [x] `.env` ignored; decision 0008 (never in a reward, never trains a model, one item per
      request, `jev-1.14.0` pinned, raw responses under logs/, spend cap $0.10)
- [x] Client and study built test-first with the HTTP call mocked: request, Bearer call,
      key loading, budget, runner (5 calls per item), kappa, Brier, stability, cost, latency,
      report. A mocked dry run over the 83 sheet rows works end to end
- [x] Rotated option orders in the same run (each option first once per item), with
      first-position bias and rotation-averaged kappa in the report
- [ ] Real run, once the key exists: `uv run python -m rlenv.climaqa.third_reader run`, then
      `... report` (626 calls; about $0.01 at 400 input tokens a call, capped at $0.10)
- [ ] Blog-ready report under reports/climaqa/

## Waiting on Aswani

- [ ] reports/climaqa/leak_review.csv: 56 Gold and Silver pairs, same item or not
- [ ] reports/climaqa/review_sample.csv: 30 validated Gold MCQ items
- [ ] Name the domain expert for the 0005 review; the sheet is ready:
      reports/climaqa/expert_review_v2.csv
- [ ] A first real model run on era5-forecast-v1 (paid or local; Phase 2 run config)

## Done

- [x] 2026-10-31 Phase 3 ERA5 forecast-score environment: the grader reproduces WB2's
      published RMSE, ACC and bias; 720 forecast items rewarded by skill over the better of
      persistence and climatology; verifiers taskset and Inspect task; Fable review with every
      fix landed; the first model run waits for Aswani; reports/era5/
- [x] 2026-10-30 Phase 2 clean ClimaQA port: clean set v1 (350 items), one answer contract,
      Inspect tasks and verifiers taskset, Gemini 3.8 Flash baseline (MCQ 0.874, cloze 0.742),
      both miss sorts, two Fable reviews with every fix landed; reports/climaqa/runs/
- [x] 2026-10-30 Phase 1 ClimaQA audit; Fable review fixes landed test-first; CI green
- [x] 2026-10-30 CI runner pinned to ubuntu-24.04

## Later

- Two-model inspect_evals Register run: parked 2026-10-30; Gemini 3.8 Flash is the only
  baseline for now, and the second model needs Aswani's yes
- Phase 5 heat-insurance basis-risk environment
- Before publishing: LICENSE, write-up, blog posts from reports/
