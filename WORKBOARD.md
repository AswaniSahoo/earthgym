# Workboard

Updated 2026-11-01. Publish after completion. Small commits, one-line messages.

## Definition of done (Aswani, 2026-11-01, relayed by lfx-prep-b7)

Aswani: "set goal and complete until all and everything is completed". Work through it
without waiting between steps.

1. [x] ERA5: the Sonnet 5.5 run (12-item probe, then all 720) and its report.
2. [x] ClimaQA clean v1 on Sonnet 5.5, plus a comparison report against the Gemini 3.8 Flash
       baseline: reports/climaqa/runs/2026-11-01-claude-sonnet-5-5.md and
       reports/climaqa/2026-11-01-sonnet-vs-gemini.md.
3. [x] Phase 4 complete: stage 2 environment (verifiers taskset and Inspect task, tests on
       mockllm), a Sonnet 5.5 baseline within the cap, a Fable review, and every fix landed.
4. [x] Phase 5 complete: heat-insurance basis-risk environment, in the same pattern. Scout
       radar first, a published number reproduced before the environment, then the
       environment, a baseline within the cap, a Fable review and the fixes.
5. [x] Final pass: README current, a blog-ready report per phase, a top-level SUMMARY.md of
       the findings with every number traced to a report, the spend ledger final, CI green.

## Rules for this goal

- Technical design choices are ours: Fable reviews them and each goes in a decision record.
  lfx-prep-b7 reviews the commits.
- Stop and tell lfx-prep-b7 only for: spend that would pass the $20 Anthropic cap; a download
  over 100 MB; any account, key or sign-up; publishing, repo visibility or a LICENSE choice
  (those are Aswani's); a hard blocker.
- Every model run is Claude Sonnet 5.5 on the Anthropic key (`anthropic/claude-sonnet-5-5`),
  $20 hard cap in total, ledger in reports/spend.md, cost projected from a probe before each
  run, never a run that would pass the cap. Order: ERA5, ClimaQA, Phase 4, Phase 5.
- No Vertex AI or Gemini calls of any kind, probes and smoke tests included (Aswani,
  2026-11-01: "never use my gemini further ... from now no more vertex ai call"). Gemini
  logs, reports and numbers stay as they are; comparisons may read those logs.
- Test-first, small one-line commits, pushes as approved, every number checked against its
  source. Every turn ends with done, next, blocked and the remaining budget.

## ERA5 on Claude Sonnet 5.5 (decision 0010): done

- [x] `anthropic==2.3.0` pinned in the eval group (Inspect 0.3.286 needs 2.0.0 or newer)
- [x] Balanced probe ids: `uv run python -m rlenv.era5.tasks` (2 per variable and lead)
- [x] Spend ledger and its checks: reports/spend.md, `src/rlenv/spend.py`
- [x] Decision 0010: the model switch, the cap, the ledger, the settings
- [x] Probe: 12 items, Batch API, 12 parsed, 0 errors, mean reward 0.282, $0.0259 in the
      ledger; full run projected at $1.55 ($1.64 with two standard errors)
- [x] Full run: 720 items, Batch API, from bbafe0e: 720 parsed, 0 errors, mean reward 0.116
      (stderr 0.009), $1.6126; ledger total $1.6385
- [x] Report: reports/era5/2026-11-01-claude-sonnet-5-5.md (baseline rows match
      items_v1_baselines.md); blog-ready write-up still to do

The Gemini full run is dropped; its 10-item probe log (logs/2026-11-01-era5-probe/) is kept
as a record.

## Phase 4, IBTrACS cyclone analytics environment

Plan (2026-11-01, from the radar in docs/radar.md):

- Goal: an analytics environment whose answers are computed exactly from IBTrACS by a
  reference implementation shown to reproduce NCEI's published North Atlantic numbers.
- Stage 1: fetch `ibtracs.NA.list.v04r01.csv` (57.6 MB, anonymous HTTPS). NCEI publishes
  no checksum and overwrites files in place, so we pin our own sha256 with the size and
  Last-Modified at first fetch, keep the copy under data/, and fail on any mismatch. A stdlib
  reader (names row, units row, single-space blanks) and season statistics: ACE by the NOAA
  CPC rule (USA_WIND squared at 00, 06, 12 and 18 UTC while USA_STATUS is TS, HU or SS and
  the wind is at least 34 kt, times 1e-4), and counts of named storms, hurricanes and major
  hurricanes. First tests reproduce NCEI's anchors: 1933 ACE 258.6; 2005 15 hurricanes and 7
  major; 2020 30 named storms and 7 major; 2024 18 named, 11 hurricanes, 5 major, ACE 161.6.
- Stage 2 (0009 decided 2026-11-01: option 1): per-storm analytics with exact answers from
  the reference code. The counting rules go in the prompt: synoptic 00/06/12/18 UTC rows
  only, which statuses count, units, ACE as the sum of v^2/10^4 in knots over qualifying
  rows, rounding to one decimal with a tested tolerance. "Rules hidden" is a later ablation.
  A verifiers taskset and an Inspect task, tested on mockllm, then a Sonnet 5.5 baseline.
- Out: other basins (agencies average wind over 1 to 10 minutes, never to be pooled), the
  netCDF files (they need an HDF5 reader), provisional seasons.
- Tests: inline CSV rows with hand-computed values; the reproduction tests run when the pinned
  file is on disk and are skipped otherwise, so CI stays offline.

- [x] Radar check for Phase 4 (scout): 12 new entries in docs/radar.md
- [x] Stage 1: pinned NA file (sha256 666681be), stdlib reader, season counts and ACE; all
      NCEI anchors reproduced; reports/ibtracs/2026-11-01-ncei-reproduction.md
- [x] 0009 accepted; 0011 records the stage 2 design (300 items, seed 2026, tolerance 0.05)
- [x] stats.category, stats.hurricane_hours; NCEI's 2024 count of 2 category 5 reproduced
- [x] Stage 2 environment: 300 items (sha256 75fe4ff2), contract, verifiers taskset, Inspect
      task; CI runs vf-validate (300 of 300 valid), a mockllm eval and the wheel build
- [x] Report module with best-constant and careless-reading baselines; trap rates in 0011
- [x] Rules-shown control on Sonnet 5.5: probe 6 of 6, then 299 of 300 (0.997), $1.3626;
      reports/ibtracs/2026-11-01-claude-sonnet-5-5.md. Saturated with the rules in the prompt
- [x] Rules-hidden ablation (lfx-prep-b7): 0.703; ACE and peak 0.99 either way, hours a
      convention test; reports/ibtracs/2026-11-01-rules-shown-vs-hidden.md
- [x] Fable review of Phase 4 (reviews/phase-4-ibtracs-storms.md): M1 to M5 and L1 to L6
      landed; L7 (publish the pinned CSV as a release asset) and the LICENSE wait for Aswani

## Phase 5, heat-insurance basis risk (decisions 0012, 0013)

- [x] Scout radar: 21 rows added, 6 moved to hold (docs/radar.md)
- [x] Stage 1: GHCN-Daily Phoenix pinned; NWS Phoenix's 2020, 2023 and 2024 counts reproduced
      exactly (reports/heat/2026-11-01-nws-phoenix-reproduction.md)
- [x] Stage 2: heat-basis-v1, 300 items over 2 airport index stations and 2 city-core
      sites (sha256 9d72cd64); contract, taskset, Inspect task, report, CI
- [x] Rules-shown control: probe 6 of 6, then 296 of 300 (0.987), $1.8801
- [x] Terms-only ablation (`-T rules=false`): probe 5 of 6, then 0.960, $1.9036;
      reports/heat/2026-11-01-rules-shown-vs-terms-only.md
- [x] Fable review of Phase 5 (reviews/phase-5-heat-basis.md): M1 to M5 and L1 to L4 landed;
      L5 (release asset) and L6 (LICENSE) wait for Aswani

## Final pass

- [x] Blog-ready write-ups: phases 1, 2 and 3 (reports/climaqa/, reports/era5/)
- [x] Write-ups for phases 4 and 5; SUMMARY.md; README current; ledger final ($9.1298 of
      $20, 12 runs); CI green at 71ab6a8

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
- [ ] LICENSE for the repo and the environment packages (Fable reviews of phases 2 to 4)
- [ ] Publish the pinned IBTrACS CSV and GHCN-Daily files as release assets, so others can
      rebuild the items (Phase 4 review L7)
- [ ] inspect_evals Register submission (publishing is Aswani's call): both model runs on
      clean ClimaQA v1 now exist, Gemini 3.8 Flash and Claude Sonnet 5.5

## Done

- [x] 2026-10-31 Phase 3 ERA5 forecast-score environment: the grader reproduces WB2's
      published RMSE, ACC and bias; 720 forecast items rewarded by skill over the better of
      persistence and climatology; verifiers taskset and Inspect task; Fable review with every
      fix landed; reports/era5/
- [x] 2026-10-30 Phase 2 clean ClimaQA port: clean set v1 (350 items), one answer contract,
      Inspect tasks and verifiers taskset, Gemini 3.8 Flash baseline (MCQ 0.874, cloze 0.742),
      both miss sorts, two Fable reviews with every fix landed; reports/climaqa/runs/
- [x] 2026-10-30 Phase 1 ClimaQA audit; Fable review fixes landed test-first; CI green
- [x] 2026-10-30 CI runner pinned to ubuntu-24.04

## Later

- "Rules hidden" ablation for the Phase 4 tasks
- Before publishing: LICENSE, write-up, blog posts from reports/ (Aswani's calls)
