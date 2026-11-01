# rlenv: what we found

Verifiable evals and RL environments for climate and earth science, built in five phases on
2026-10-30 and 2026-11-01. Every number here is traced to the report it comes from; the
blog-ready write-ups tell each phase's story.

## Phase 1: checking ClimaQA before trusting it

- 43 validated Gold test questions appear verbatim in Silver, the set the paper fine-tunes on
  (17 multiple choice, 9 cloze, 17 freeform), plus 6 more across tasks: train/test leaks for
  the paper's fine-tuned results (`reports/climaqa/SUMMARY.md`, Findings).
- The Gold multiple-choice file still holds the 47 items the experts rejected; every later
  ClimaQA score we checked uses that unfiltered file (`reports/climaqa/SUMMARY.md`, Inventory;
  `docs/radar.md`).
- The paper's statistics table matches the released files on all six rows we could compare.

Write-up: `reports/climaqa/2026-11-01-phase-1-writeup.md`.

## Phase 2: a clean ClimaQA, and two models on it

- Clean set v1 keeps 350 items, 222 multiple choice and 128 cloze
  (`reports/climaqa/clean_v1_manifest.json`).
- Multiple choice: Gemini 3.8 Flash and Claude Sonnet 5.5 both score 0.874 and tie item for
  item (6 items each that only one model got right, McNemar p 1.0). Cloze: 0.742 against
  0.508; on 18 of Sonnet's 63 misses the last line alone is the key, and crediting those
  still leaves 0.648 (`reports/climaqa/2026-11-01-sonnet-vs-gemini.md`).
- Both models give the same wrong answer on 18 multiple-choice and 11 cloze items: candidates
  for a wrong key, for the expert review (same report).

Write-up: `reports/climaqa/2026-11-01-phase-2-writeup.md`.

## Phase 3: forecasts graded the WeatherBench 2 way

- The grader reproduces WB2's published scores for IFS HRES mean sea level pressure at 72 h:
  RMSE 133.890547 Pa, ACC 0.981878, bias -0.406578 Pa
  (`reports/era5/2026-10-30-wb2-reproduction.md`).
- On 720 ERA5 point forecasts, Claude Sonnet 5.5 earns a mean reward of 0.116 against IFS
  HRES's 0.30 to 0.67 per variable and lead. It beats persistence in RMSE everywhere but trails
  climatology for pressure at 72 h, and it used no extended thinking
  (`reports/era5/2026-11-01-claude-sonnet-5-5.md`).

Write-up: `reports/era5/2026-11-01-phase-3-writeup.md`.

## Phase 4: counting hurricanes by NOAA's rules

- The counting code reproduces NCEI's North Atlantic anchors from the pinned IBTrACS file,
  among them 1933's ACE of 258.6 and 2024's 18 named storms, 11 hurricanes, 5 major, ACE 161.6
  and 2 category 5 hurricanes (`reports/ibtracs/2026-11-01-ncei-reproduction.md`).
- On 300 per-storm questions, Sonnet 5.5 scores 0.997 with the rules in the prompt and 0.703
  without them. ACE and peak category stay at 0.99 either way; hours at hurricane strength
  fall to 0.13, and 63 of the 87 misses follow a duration reading, a convention the question
  does not state (`reports/ibtracs/2026-11-01-rules-shown-vs-hidden.md`).
- Without a name or year in the prompt, 2 of 300 rules-shown replies and 4 of 300
  rules-hidden ones still name the storm or its season (same report).

Write-up: `reports/ibtracs/2026-11-01-phase-4-writeup.md`.

## Phase 5: a heat policy's payouts and its basis risk

- The counting code reproduces NWS Phoenix's published heat counts from the pinned GHCN-Daily
  file: 55 days at 110 F or more in 2023 and a 31-day run, 70 days in 2024 and a 113-day run at
  100 F, 145 days at 100 F in 2020 (`reports/heat/2026-11-01-nws-phoenix-reproduction.md`).
- The basis risk is in the data: with Scottsdale's airport as the index, the urban core at Sky
  Harbor has 7 to 42 days a season at 110 F that the index misses (decision 0013).
- On 300 policy questions, Sonnet 5.5 scores 0.987 with the rules in the prompt and 0.960 with
  the policy terms alone. Missed days drop from 0.96 to 0.89, and 6 of the 11 misses leave out
  days the index station had no value, the clarifying rule the terms-only prompt drops
  (`reports/heat/2026-11-01-rules-shown-vs-terms-only.md`).

## What it means for RL

- The exact-answer environments of Phases 4 and 5 are saturated for a model as strong as
  Sonnet 5.5: told the rules, it gets nearly every item right, so nearly every rollout earns the
  same reward and a policy this strong gets almost no signal. Not told them, it still applies
  NOAA's ACE convention, the Saffir-Simpson scale and the policy's thresholds; what remains is
  a matter of convention (hours at hurricane strength, a missing index value), which a policy
  would close as a constant offset. They serve as regression checks, and for weaker models.
- The forecasting environment of Phase 3 is far from saturated, with a mean reward of 0.116
  against HRES's 0.30 to 0.67: that is where a policy has room to learn.

## Spend

$9.1298 of the $20 cap on the Anthropic key over 12 runs, probes included, all through the
Batch API (`reports/spend.md`). The Gemini 3.8 Flash runs on Vertex AI are separate and stay as
recorded in their reports.

## Limits

- One run per model and condition, with no seed: the run-to-run spread is not measured, and
  one Phase 4 storm drew two different hours answers from the same model.
- One model on the Anthropic key; the Gemini numbers come from runs that cannot be repeated.
- Every review is in `reviews/`; the choices are in `docs/decisions/`.
