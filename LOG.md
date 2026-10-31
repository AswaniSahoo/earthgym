# Log

Newest first. One entry per working session: what changed, what we learned, what is next.

## 2026-11-01, Phase 4 start

- Aswani parked the Jev third-reader study: there is no TypeSafe key now. The code stays as
  it is; no call was made and nothing was spent.
- Phase 3 is closed in the README and the workboard; its first model run waits for Aswani.
- Phase 4, the IBTrACS cyclone analytics environment, starts with a scout radar check.
- ERA5 probe (Aswani's yes, 2026-11-01): Gemini 3.8 Flash on Vertex, provider-default
  sampling, 10 items from a clean tree at c725bc3. Per item: 489 input and 1,916 output
  tokens, 1,624 of them reasoning; all 10 answers parsed; mean reward 0.256. Projected for 720
  items: 1,731,960 tokens, over the 1.5 million guard, so the full run did not start. Price
  from the Vertex pricing page (2026-11-01): $0.75 input and $3.75 output per million tokens
  through 2026-12-31, reasoning billed as output, so about $5.44 for the full set. The probe's
  items are all MSLP at 24 h, the first ten in file order, so the projection may not hold for
  temperature or longer leads.

## 2026-10-31, Jev third reader

- Task from Aswani: TypeSafe's Jev re-sorts the 83 rows of the expert review sheet, to
  measure agreement (Cohen's kappa) with the build session's sort and Fable's blind sort,
  calibration (Brier) where both agree, stability over 5 calls, cost and latency.
- Checked at the source: the OpenAPI spec (request `model`, `state`, `questions`; a choice
  answer carries `probabilities`) and the models page (`jev-1.14.0`, $0.042 per million input
  tokens, output free).
- Decision 0008: Jev never enters a reward and its outputs never train a model (MCA 2.3(b));
  one item per request; model pinned; raw responses under logs/; spend capped at $0.10.
- Built test-first with the HTTP call mocked; `.env` ignored. The buckets are phrased as
  properties of the item, so one question fits correct answers too. Reference check: the
  build session and Fable agree on 32 of 33 cloze items (kappa 0.914).
- Added in the same run: each other cyclic rotation of the option order, once per item (626
  calls in all), to measure the first-position lean TypeSafe documents. A mocked server that
  always picks the first option scores 294 of 294 against 0.282 expected, so the measure works.
- Next: the real run once the key exists; no call has been made.

## 2026-10-30, Phase 3 start

- Radar refreshed for Phase 3 (17 entries). No existing environment scores forecasts with the
  WB2 rules; WB2 publishes score files that can serve as answer keys.
- Grader: `rlenv.era5.scores` ports the WB2 rules (cell-area weights, MSE over init time and
  grid, root after the mean, float64). From a pinned 12.0 MB subset (18.0 MB once the
  climatology joined) it gives IFS HRES MSLP
  RMSE at 72 h for 2020 as 133.890547 Pa, the published value to all six decimals.
- Lesson: on a grid without poles, cell-area weights equal cosine weights, so only a test on
  a grid with poles catches a cosine bug. Lesson: float32 squares shift MSE at the eighth
  digit; the scores now compute in float64.
- ACC reproduced too: 0.981878, the published value. Finding: the published ACC pools the
  anomaly statistics over all inits before the ratio (WeatherBench-X); the WB2 paper's mean of
  per-init correlations gives 0.981470 on the same data. Read the code that made a number, not
  only the paper that defines it.
- Decisions from Aswani, about 19:25 IST: 0007 accepted as forecast-answer tasks, rewarded by
  skill over the better of persistence and climatology, bounded, so copying a baseline earns
  0; 0005 accepted, with the review sheet after stage 2 and accepted answers written only by
  the expert. The reward floor was not his decision (see the correction below).
- Stage 2 so far: the answer contract and reward (copying a baseline earns 0 exactly), the
  prompt, and 720 items (MSLP and 2 m temperature, leads 24, 48, 72 h) built from the pinned
  stores. Baseline rows: persistence, climatology and the always-climatology policy earn
  0.000; IFS HRES earns 0.57 to 0.66 (MSLP) and 0.28 to 0.45 (2 m temperature). HRES item RMSE
  at 72 h (139.4 Pa, 0.86 K) sits near the published global values (133.9 Pa, 0.881 K).
- Finding: the first floors, 50 Pa and 0.5 K (the build session's own guess), bound on 65 and
  167 of 360 items; 0.5 K capped nearly half the temperature rewards.
- Correction: earlier notes said Aswani set those floors; he did not. The guard was suggested
  in coordination, and the rule was then set by the coordinating session. Rule now: each variable's floor is
  the 10th percentile of the better-baseline error over the items (baseline data only), 28.75
  Pa and 0.069 K, each binding on 36 of 360. HRES rewards on 2 m temperature rose to 0.30 to
  0.49; every copy-baseline row still pays 0.000.
- Lesson: a piped `pytest | tail` hid a failing test and let a commit through (amended before
  any push); every commit now runs with `set -o pipefail`.
- The verifiers taskset (720 of 720 valid) and the Inspect task share one contract; the
  documented `inspect eval` command runs from the repo root on mockllm.
- The 0005 review sheet is ready for an expert: 83 rows (61 misses, 2 review flags, 20 sampled
  hits), expert columns empty, written once and never overwritten.
- Fable's Phase 3 review: no High (correctness 9, publish 6). It read the published score
  file at its root, recomputed items online and found a latent division by zero in the floor
  rule, no test tying items to source data, a parser stricter than 0004, one wrong sheet cell
  and undisclosed reward limits: on the quarter of temperature items with the smallest
  baseline error, HRES earns 0.086 and 3 items cannot be won. All fixed test-first; the bias
  now reproduces too (1.2e-15 Pa).
- Lesson: the editing tool turned `\u` escapes into literal characters (an en dash, a Unicode
  minus) in two files; a grep for the code points caught it, and they are escapes again.
- Next: a first real model run needs Aswani's yes; LICENSE and the expert's name are open.

## 2026-10-30, Phase 2 baseline

- Baseline: Gemini 3.8 Flash on Vertex over clean set v1. MCQ 0.874 (194 of 222, stderr 0.022;
  BASE 0.907, HYPOTHETICAL 0.848, REASONING 0.841), cloze 0.742 (95 of 128, stderr 0.039),
  0 format failures. Report: reports/climaqa/runs/2026-10-30-gemini-3.8-flash.md.
- Checked: a separate stdlib reader of the two .eval files gives the same counts, stderr and
  tokens; all 350 logged prompts and keys equal the bundled set (sha256 5f345d8e), and today's
  contract gives every logged verdict. Inspect marks the run dirty at 3c70706; the only later
  commit touches WORKBOARD.md and the Phase 2 review.
- Finding: the run set no temperature, max tokens or seed, so it used provider defaults and a
  rerun need not match. Reasoning is 89.2 percent of MCQ output tokens (108,017 of 121,121)
  and 99.8 percent of cloze output (93,278 of 93,511).
- The report now records commit, generate config, tokens and log file. Lesson: Inspect keeps
  eval-level settings in `plan.config`, not `eval.model_generate_config`; a test caught it.
- Finding: of the 33 cloze misses, 8 say the same thing in another string (symbols 22 and 105,
  word order 37, plural 114, synonyms 47, 72, 136, 142), 25 are other words that still make a
  correct sentence (8 debatable), and none is clearly wrong. Counting the 8 lifts cloze from
  0.742 to 0.805. For this model the cloze score mostly measures picking the source's word.
  Fable's blind second sort matched 31 of 33; 157 went from "model error" to debatable because
  no source showed the study's method.
- Finding: of the 28 MCQ misses, 7 are model errors (3 debatable) and 21 are item problems:
  6 flawed (keys wrong in 232 and 247), 3 source only, 12 with two defensible options. So the
  MCQ reward is noisy too; 167 and 207 are the same question.
- Fable's baseline review: no High; every report number reproduced from the logs. Medium: the
  157 label, 0005 resting on cloze alone, the report hiding the dirty tree and provider
  defaults, items that test the source document. Lesson: a label needs the same evidence bar
  as a number.
- The contract stays: no single rule recovers more than 1 item, and aliases need a person's
  approval. Decision for Aswani in WORKBOARD.md.
- Follow-ups: the report shows n per complexity level and n/a for cloze format failures (only
  MCQ has a format check); `.serena/` is ignored. Decision 0005 (proposed, revised after the
  MCQ sort): expert item review of both splits, accepted-answer lists for cloze, rewards from
  reviewed items only, no judge model; contract v1 unchanged.
- Decisions relayed from Aswani: Gemini 3.8 Flash stays the only baseline for now (the
  two-model Register run is parked), and no v2 work starts until he answers on 0005.
- Next: Phase 3 once the radar lands; downloads over 100 MB wait for Aswani's yes.

## 2026-10-30

- Phase 1 ClimaQA audit built stdlib-only on a pinned dataset revision (3f084a0, sha256 per
  file). The paper's statistics table matches the released files on all 6 rows.
- Finding: 43 validated Gold test questions appear verbatim in Silver (17 MCQ, 9 cloze,
  17 freeform), plus 6 across tasks. The paper fine-tunes Llama-3.1-8B and Mistral-7B on
  Silver (arXiv 2410.16701v2, A.3.2), so these are train/test leaks for its ft-silver results.
  34 reworded near copies wait for a human verdict.
- Lesson: the "292 vs 245" gap first looked like a defect; the Validation column and the
  authors' notebooks showed it is the expert-rejected items. Check the source before claiming.
- Lesson: stripping punctuation made `(scl - senv)` equal `(senv - scl)`; a test now guards it.
- Fable review (correctness 7, tests 5, publish-readiness 4); every fix landed test-first,
  20 tests, CI green. Runner pinned to ubuntu-24.04.
- Phase 2 started. Radar refreshed to 20 entries: verifiers 0.4.0 replaced its API with
  `verifiers.v1` tasksets; Inspect 0.3.286 never shuffles MCQ choices by itself; Gemini 2.5
  Flash on Vertex retired 2026-10-20; torchtpu is real but needs TPU v5e or newer.
- Finding: every published ClimaQA score we checked uses the unfiltered file, which still holds
  the 47 expert-rejected MCQ items; 12 Gold cloze keys end in "," or "." and break exact match.
- Clean set v0: 377 items (226 MCQ, 151 cloze), 75 excluded with reasons; MCQ keys uppercase,
  cloze keys cleaned. Inspect tasks use built-in choice() and exact(); 26 tests, CI green.
- Next: baselines (model access decision), verifiers taskset, Phase 2 review.
