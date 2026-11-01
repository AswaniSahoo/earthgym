# Log

Newest first. One entry per working session: what changed, what we learned, what is next.

## 2026-11-01, Phase 5 runs and review

- Phase 5 on Sonnet 5.5, the rules-shown control: 296 of 300 (0.987), $1.8801; all four misses
  are one extra day on missed days. Terms-only ablation: 0.960, $1.9036. Trigger days and events
  stay at the ceiling; missed days fall from 0.96 to 0.89, and 7 of the 8 items where a missing
  index value decides the key, all Deer Valley 2019, took the other reading.
- Fable review of Phase 5 (correctness 9, publish-readiness 7): the heat reports said "storms"
  and "rows" (Phase 4 wording), now seasons and days; the pair report called the missed-days
  gap a constant offset, now a convention a policy would take from the reward; the reports name
  Deer Valley 2019 as the only place the missing-value rules change a key, count misses off by
  one (4 of 4 in the control) and replies that name a season (0 of 600), and carry five more
  careless readings; CI's smoke runs now cover every question type.
- Lesson: a template written for one phase carried its nouns into the next; a test now asserts
  the heat reports never say "storm".

## 2026-11-01, a wait that could not end

- Bug, found by lfx-prep-b7: the wait for the Phase 5 terms-only probe was
  `while pgrep -f "inspect eval src/rlenv/heat"; do sleep 10; done`, and `pgrep -f` matched
  the waiting shell's own command line, which holds the same text, so the loop never ended
  (2 hours). The same pattern in the one-off checks reported "probe still running" at 07:19,
  07:21 and 07:23, when the probe had finished at 07:20. Waits now use the run's own
  completion notice (`run_in_background`), a PID, or a pattern that cannot match itself
  (`pgrep -f "[i]nspect eval ..."`).

## 2026-11-01, Phase 4 ablation and review

- Rules-hidden ablation on the same 300 items: 0.703 against the control's 0.997. ACE and
  peak category stay at 0.99 with the rule left out; hours fall to 0.13, and 63 of the 87
  misses follow a duration reading (status held until the next row, or the elapsed time of each
  spell), since 6 hours per 6-hourly row is our convention. Same storm, two runs: Keith 2000
  drew 75 in the probe and 71 in the full run. $1.7800.
- Fable review of Phase 4 (correctness 9, publish-readiness 6): the rule wording now says
  "at exactly 00:00, 06:00, 12:00 or 18:00 UTC" (9 items turn on it; the runs used the old
  words and Sonnet got all 9 right); the one-decimal ACE format stays, with its 39 percent slack
  on single 5 kt misreads stated; reports count the replies that name the storm (2 shown, 4
  hidden) instead of UNKNOWN; the hidden report says it is the hidden run; the pair report
  judges each question; new careless readings (no SS, mph thresholds, status held, spell
  time); tests rebuild the bundled items from the pinned files; hatchling pinned (0014);
  `--cache-prompt false` from the Phase 5 full runs on (about 10 percent of input cost).
- Lesson: a diagnostic reading (first to last HU row) looked right on the probe's numbers but
  spanned the gaps between spells; the reviewer's recomputation from the raw rows caught it.

## 2026-11-01, Phase 4 baseline and Phase 5 build

- Phase 4 on Sonnet 5.5, the rules-shown control: probe 6 of 6, then 299 of 300 (0.997; ACE
  0.99, category and hours 1.00), $1.3626. With the rules in the prompt the environment is saturated for this model;
  lfx-prep-b7 asked for the rules-hidden ablation, now built as a switch (`-T rules=false`)
  with a side-by-side report.
- Phase 5 radar (scout): 21 rows added, 6 moved to hold (every non-Claude model under 0010).
  First published number: NWS Phoenix's heat counts. From the pinned GHCN-Daily file for
  Sky Harbor (NCEI rewrites it daily, so the sha256 is ours), every anchor reproduces exactly:
  2023 55 days at 110 F or more, 133 at 100, 185 at 90, high 119 F on 19 Jul, a 31-day 110 F run
  from 30 Jun to 30 Jul; 2024 70 days at 110 F and a 113-day 100 F run; 2020 145 days at 100 F.
- Phase 5 design: Sky Harbor is the hottest station around, so with it as the index almost no
  heat was missed; the airports (Scottsdale, Deer Valley) are the index and the core (Sky
  Harbor, Tempe ASU) the insured sites, 20.7 to 32.3 km apart, which gives 7 to 42 missed days
  a season at 110 F. heat-basis-v1: 300 items, trigger days, events and missed days.
- Trap rates in Phase 5: the at-or-above, column and run-length rules change most answers;
  the missing-value rules rarely do, since the airport stations have few gaps.

## 2026-11-01, clean ClimaQA v1 on Sonnet 5.5

- Probe of 16 items (8 per task, seeded shuffle) for $0.0172, then all 350 through the Batch
  API for $0.4123 (projected $0.44, $0.60 at two standard errors). MCQ 0.874 (stderr 0.022,
  2 format failures), cloze 0.508 (stderr 0.044).
- Against Gemini 3.8 Flash, item by item: MCQ ties at 0.874 (6 items each only one model got
  right, McNemar p 1.0); cloze 0.742 against 0.508 (33 only Gemini, 3 only Sonnet, p < 0.001).
- Finding: the cloze prompt says "Reply with only the missing word or phrase". Sonnet wrote
  more than one line on 34 of 128 replies, Gemini on none; on 18 of Sonnet's 63 misses the last
  line alone is the key. Part of the gap is format, but crediting those 18 would give 0.648,
  still below Gemini. The contract stays as it is; the comparison reports both.
- Both models gave the same wrong answer on 18 MCQ and 11 cloze items: candidates for a wrong
  key, for the expert review of decision 0005.
- Peak category stays in Phase 4 (lfx-prep-b7 offered a swap for a rapid-intensification
  question); the report says where a careless reading is right anyway.

## 2026-11-01, ERA5 on Sonnet 5.5 and Phase 4 stage 2

- ERA5 through the Batch API: a 12-item probe ($0.0259, mean reward 0.282), then all 720 from
  bbafe0e: 720 parsed, 0 errors, mean reward 0.116 (stderr 0.009), $1.6126 against a
  projection of $1.55 to $1.64. IFS HRES earns 0.30 to 0.67 per cell. The model beats
  persistence RMSE at every lead but trails climatology for MSLP at 72 h (738.1 against 726.1
  Pa). No reply used extended thinking: 0 reasoning tokens, about 360 output tokens an item.
  Report: reports/era5/2026-11-01-claude-sonnet-5-5.md.
- Inspect sends `thinking: {"type": "adaptive"}` itself (`apply_thinking_block_binding`);
  decision 0010 first said it did not, and is corrected. The stage 1 IBTrACS report put the
  458 provisional rows in 2025 and 2026; all of them are in 2026, corrected.
- Phase 4 stage 2: 0009 accepted, 0011 records the design. 300 items from 613 eligible storms
  (seed 2026). The first draw gave the hurricanes to category and hours first and left ACE
  with weaker storms (median 42.5 rows); ACE now draws first (median 56, all storms 53). The
  category rule reproduces NCEI's 2024 count of two category 5 hurricanes.
- Trap rates on the items: ACE over every row is right on 0 of 100, ACE ignoring status on
  56, hours over every HU row on 1; for peak category, ignoring status is right on 100 and
  synoptic rows only on 96, so that question is mostly a control.
- Lesson: a gate chained with `;` after `grep ... && echo` let the commits run although ruff
  had failed, and pushed a commit that failed CI (944d248, fixed forward in 9341972). Gates
  now wrap the commit in `if ...; then ...; fi`.
- The tool layer again wrote `\u2212` as the literal character; rewritten as escapes.

## 2026-11-01, Claude Sonnet 5.5 runs

- Aswani moved every model run to Claude Sonnet 5.5 on the Anthropic key, first with "use
  sonnet 5-5 and use as much credit you need", then with "use for everything keep cap at 20
  $": a hard cap of $20 in total, a spend ledger in reports/spend.md, and a probe before each
  run (decision 0010). The Gemini full ERA5 run is dropped; its probe log is kept.
- Hard rule from Aswani: "never use my gemini further ... from now no more vertex ai call".
  Audit of defaults, tests, CI and documented commands: no code default, test or CI job names
  a Google model, and CI's only eval runs on mockllm/model. The eval group still installed
  `google-genai`, the client Inspect uses for `google/...` models, so one could still have
  been called. Removed it, with `google-auth`; a test fails if either comes back. The commands
  recorded in the 2026-10-30 Gemini reports stay as records of those runs.
- Goal set by lfx-prep-b7 under Aswani's instruction "set goal and complete until all and
  everything is completed": the Definition of done in WORKBOARD.md. Decision 0009 is decided
  (option 1, with the counting rules in the prompt).
- An editor's copy, `.env.save` (1 byte), appeared next to `.env`; git now ignores `.env*`
  and swap files.

## 2026-11-01, Phase 4 start

- Aswani parked the Jev third-reader study: there is no TypeSafe key now. The code stays as
  it is; no call was made and nothing was spent.
- Phase 3 is closed in the README and the workboard; its first model run waits for Aswani.
- Phase 4, the IBTrACS cyclone analytics environment, starts with a scout radar check.
- Phase 4 radar: 12 entries; the North Atlantic CSV (57.6 MB) is the source; NCEI publishes no
  checksum and overwrites in place, so we pin our own sha256 (666681be, build of 2026-10-30).
- Stage 1: a stdlib reader and season statistics by the NOAA rules reproduce every NCEI
  anchor: 1933 ACE 258.6; 2005 15 hurricanes and 7 major; 2020 30 named and 7 major; 2024 18,
  11, 5 and ACE 161.6. Both row scopes (basin rows only, or every row of a storm) agree on
  these seasons; the code counts basin rows only.
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
