# earthgym: what I found

Verifiable evals and RL environments for climate and earth science, built in six phases from
2026-10-30 to 2026-11-02. Every number here is traced to the report it comes from; the
blog-ready write-ups tell each phase's story.

## Phase 1: checking ClimaQA before trusting it

- 43 validated Gold test questions appear verbatim in Silver, the set the paper fine-tunes on
  (17 multiple choice, 9 cloze, 17 freeform), plus 6 more across tasks: train/test leaks for
  the paper's fine-tuned results (`reports/climaqa/SUMMARY.md`, Findings).
- The Gold multiple-choice file still holds the 47 items the experts rejected; the later
  ClimaQA scores I checked, OpenCompass's and SciEvalKit's, use that unfiltered file
  (`reports/climaqa/SUMMARY.md`, Inventory; `docs/radar.md`).
- The paper's statistics table matches the released files on all six rows I could compare.

Write-up: `reports/climaqa/2026-11-01-phase-1-writeup.md`.

## Phase 2: a filtered ClimaQA, and two models on it

- Clean set v1 keeps 350 items, 222 multiple choice and 128 cloze, after removing exact overlaps
  with Silver; 21 near matches stay in, unresolved (`reports/climaqa/clean_v1_manifest.json`).
  On the strict variant without them, 329 items, the scores barely move: multiple choice 0.871
  for both models, cloze 0.739 against 0.513 (`reports/climaqa/2026-11-01-sonnet-vs-gemini.md`).
- Multiple choice: Gemini 3.8 Flash and Claude Sonnet 5.5 both score 0.874 and tie item for
  item (6 items each that only one model got right, McNemar p 1.0). Cloze: 0.742 against
  0.508; on 18 of Sonnet's 63 misses the last line alone is the key, and crediting those
  still leaves 0.648 (`reports/climaqa/2026-11-01-sonnet-vs-gemini.md`).
- Both models give the same wrong answer on 18 multiple-choice and 11 cloze items: candidates
  for a wrong key, for the expert review (same report).

Write-up: `reports/climaqa/2026-11-01-phase-2-writeup.md`.

## Phase 3: forecasts rewarded by skill, checked with WeatherBench 2 metrics

- The grader reproduces WB2's published scores for IFS HRES mean sea level pressure at 72 h:
  RMSE 133.890547 Pa, ACC 0.981878, bias -0.406578 Pa
  (`reports/era5/2026-10-30-wb2-reproduction.md`).
- On the 648 ERA5 point forecasts that pass the gold check (720 drawn; decision 0021), Claude
  Sonnet 5.5 earns a mean reward of 0.1277; the midpoint of persistence and climatology, a
  trivial statistical forecast, earns 0.1175. Item by item the model is ahead by +0.0102 (SE
  0.0085), which is not significant: on this task the model shows no measurable skill over a
  trivial statistical forecast. IFS HRES earns 0.34 to 0.71 per variable and lead, so the
  environment has headroom. The model used no extended thinking
  (`reports/era5/2026-11-01-claude-sonnet-5-5.md`; baselines, with a mixture fitted on a train
  split, in `reports/era5/items_v1_baselines.md`).

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
  the policy terms alone. Missed days drop from 0.96 to 0.89: on 7 of the 8 items where a
  missing index value decides the key, all at Deer Valley in 2019, the model took the other
  reading of that missing value, which the terms leave open
  (`reports/heat/2026-11-01-rules-shown-vs-terms-only.md`).

Write-up: `reports/heat/2026-11-01-phase-5-writeup.md`.

## Phase 6: the storm's rows behind a query tool

- The same 300 IBTrACS items, with the rule left out and each storm's rows behind one read-only
  SQL tool instead of in the prompt (decision 0023). Sonnet 5.5 scores 0.747, against 0.703
  with the rows in the prompt: ACE and peak category stay at 0.99 and 1.00, and hours at
  hurricane strength rise from 0.13 to 0.25, with 16 items right only with the tool and 4 only
  with the rows in the prompt, an exact McNemar p of 0.012
  (`reports/ibtracs/2026-11-02-rows-in-prompt-vs-tool.md`).
- 63 of the 75 hours misses with the tool still follow a careless reading of the rule, so the
  tool does not close the convention gap (same report). The model made 645 queries, a median of
  2 an item, with no query error and no item at the 30-message limit
  (`reports/ibtracs/2026-11-02-claude-sonnet-5-5-tools.md`).

Write-up: `reports/ibtracs/2026-11-02-phase-6-writeup.md`.

## What it means for RL

- The exact-answer environments of Phases 4 and 5 are saturated for a model as strong as Sonnet 5.5:
  told the rules, it gets nearly every item right, so nearly every rollout earns the same reward and
  a policy this strong gets almost no signal. Not told them, it still applies NOAA's ACE convention,
  the Saffir-Simpson scale and the policy's thresholds. What remains is convention: hours at
  hurricane strength, short by a constant 3 or 6 hours, and a missing index value, which matters
  only at Deer Valley in 2019. My untested guess is that a policy would take either from the reward
  in a few steps; no training run has checked it. I keep them as the controls for the ablations and
  for small-model curricula.
- Tools mode adds no headroom for Sonnet 5.5 on ACE or peak category. What it adds is a
  multi-turn rollout whose transcript records how the model read the data, on the same items
  and with the same reward as the prompt version.
- The forecasting environment of Phase 3 is far from saturated: the model's 0.128 is no better
  than the midpoint baseline's 0.118, against HRES's 0.34 to 0.71 per variable and lead, so there
  is headroom and no skill yet to build on.

## Spend

$10.9267 of a managed $20 budget on the Anthropic key over 14 runs (a probe projected each
run's cost before it started; the ledger is checked after each run), probes included, all
through the Batch API but the Phase 6 probe (`reports/spend.md`). The Gemini 3.8 Flash runs on
Vertex AI are separate and stay as recorded in their reports.

## Limits

- One run per model and condition, with no seed: the run-to-run spread is not measured, and
  one Phase 4 storm drew two different hours answers from the same model.
- One model on the Anthropic key; the Gemini numbers come from runs that cannot be repeated.
- Every review is in `docs/reviews/`; the choices are in `docs/decisions/`.
