# Log

Newest first. One entry per working session: what changed, what we learned, what is next.

## 2026-10-30, Phase 3 start

- Radar refreshed for Phase 3 (17 entries). No existing environment scores forecasts with the
  WB2 rules; WB2 publishes score files that can serve as answer keys.
- Grader: `rlenv.era5.scores` ports the WB2 rules (cell-area weights, MSE over init time and
  grid, root after the mean, float64). From a pinned 12.0 MB subset it gives IFS HRES MSLP
  RMSE at 72 h for 2020 as 133.890547 Pa, the published value to all six decimals.
- Lesson: on a grid without poles, cell-area weights equal cosine weights, so only a test on
  a grid with poles catches a cosine bug. Lesson: float32 squares shift MSE at the eighth
  digit; the scores now compute in float64.
- ACC reproduced too: 0.981878, the published value. Finding: the published ACC pools the
  anomaly statistics over all inits before the ratio (WeatherBench-X); the WB2 paper's mean of
  per-init correlations gives 0.981470 on the same data. Read the code that made a number, not
  only the paper that defines it.
- Next: stage 2 task design waits for Aswani; until then, more reproduction checks (bias,
  T2M) are possible within the 100 MB limit.

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
