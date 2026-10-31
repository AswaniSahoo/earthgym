# Workboard

Updated 2026-11-01. Publish after completion. Small commits, one-line messages.

## Now: Phase 4, IBTrACS cyclone analytics environment

Plan (2026-11-01, from the radar in docs/radar.md):

- Goal: an analytics environment whose answers are computed exactly from IBTrACS by a
  reference implementation shown to reproduce NCEI's published North Atlantic numbers.
- Stage 1, now: fetch `ibtracs.NA.list.v04r01.csv` (57.6 MB, anonymous HTTPS). NCEI publishes
  no checksum and overwrites files in place, so we pin our own sha256 with the size and
  Last-Modified at first fetch, keep the copy under data/, and fail on any mismatch. A stdlib
  reader (names row, units row, single-space blanks) and season statistics: ACE by the NOAA
  CPC rule (USA_WIND squared at 00, 06, 12 and 18 UTC while USA_STATUS is TS, HU or SS and
  the wind is at least 34 kt, times 1e-4), and counts of named storms, hurricanes and major
  hurricanes. First tests reproduce NCEI's anchors: 1933 ACE 258.6; 2005 15 hurricanes and 7
  major; 2020 30 named storms and 7 major; 2024 18 named, 11 hurricanes, 5 major, ACE 161.6.
- Stage 2, proposed for Aswani: per-storm analytics tasks with the storm's 6-hourly track in
  the prompt (ACE, peak category, hours at hurricane strength, rapid intensification), exact
  answers from the reference code; a verifiers taskset and an Inspect task, mockllm only.
- Out: other basins (agencies average wind over 1 to 10 minutes, never to be pooled), the
  netCDF files (they need an HDF5 reader), provisional seasons, any paid run.
- Tests: inline CSV rows with hand-computed values; the reproduction tests run when the pinned
  file is on disk and are skipped otherwise, so CI stays offline.

- [x] Radar check for Phase 4 (scout): 12 new entries in docs/radar.md
- [x] Stage 1: pinned NA file (sha256 666681be), stdlib reader, season counts and ACE; all
      NCEI anchors reproduced; reports/ibtracs/2026-11-01-ncei-reproduction.md
- [ ] Stage 2 task design, after Aswani's choice on decision 0009 (proposed: per-storm
      analytics with exact answers)

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
- [ ] ERA5 full run (approved 2026-11-01), stopped at the spend guard: the 10-item probe
      projects 1,731,960 tokens for 720 items, over the 1.5 million guard (about $5.44 at
      the Vertex introductory price). Approve the full run, a smaller set, or a stratified
      probe first

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
