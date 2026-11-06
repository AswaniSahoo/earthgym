# earthgym: what each phase found

[`README.md`](README.md) gives the headline results. This page keeps the detail behind them, built
in seven phases from 2026-10-30 to 2026-11-03, with the report each number comes from.

## Phase 1: checking ClimaQA before trusting it

[Write-up](reports/climaqa/2026-11-01-phase-1-writeup.md).

- The audit sorts what it finds into defects and flags. Defects break an item: option labels other
  than a) to d), a key that is not an option, empty or identical options, a cloze item with no
  `<MASK>`, an empty cloze answer, and a Gold question that also appears in Silver. Silver is the
  set the paper fine-tunes on (arXiv 2410.16701v2, A.3.2), so an overlap is a train/test leak. Flags
  go to a human: the keyed option repeated in the question, a cloze answer repeated outside the
  blank, several masks for one answer, "all/none of the above" options, and repeated questions
  within a split, noting when the keyed answer text differs.
- The 43 leaked Gold questions are 17 multiple choice, 9 cloze and 17 freeform; the 6 across tasks
  are 2 multiple choice and 4 freeform (`reports/climaqa/SUMMARY.md`, Findings).
- The Gold multiple choice and freeform files still hold the items the experts rejected
  (`Validation=False`: 47 multiple choice, 20 freeform). The authors' evaluation notebooks keep only
  `Validation=True`, which matches the paper's counts, so any other loader has to filter the same
  way. The later ClimaQA scores I checked, OpenCompass's and SciEvalKit's, use the unfiltered
  multiple choice file (`reports/climaqa/SUMMARY.md`, Inventory; `docs/radar.md`).
- The paper's statistics table matches the released files on all six rows I could compare.

## Phase 2: a filtered ClimaQA, and two models on it

[Write-up](reports/climaqa/2026-11-01-phase-2-writeup.md); both models in
`reports/climaqa/2026-11-01-sonnet-vs-gemini.md`.

- Clean set v1 keeps 350 items after removing exact overlaps with Silver; 21 near matches stay in,
  unresolved (`reports/climaqa/clean_v1_manifest.json`). On the strict variant without them, 329
  items, the scores barely move: multiple choice 0.871 for both models, cloze 0.739 against 0.513.
- Multiple choice: Gemini 3.8 Flash and Claude Sonnet 5.5 both score 0.874 and tie item for item (6
  items each that only one model got right, McNemar p 1.0). Cloze: 0.742 against 0.508; on 18 of
  Sonnet's 63 misses the last line alone is the key, and crediting those still leaves 0.648.
- Both models give the same wrong answer on 18 multiple choice and 11 cloze items: candidates for a
  wrong key, for the expert review.

## Phase 3: forecasts rewarded by skill, checked with WeatherBench 2 metrics

[Write-up](reports/era5/2026-11-01-phase-3-writeup.md).

- Beside the RMSE, the grader reproduces WB2's published ACC for IFS HRES mean sea level pressure at
  72 h, 0.981878, and its bias, -0.406578 Pa (`reports/era5/2026-10-30-wb2-reproduction.md`).
- 648 ERA5 point forecasts pass the gold check, of 720 drawn (decision 0021). Against the midpoint,
  item by item, Sonnet 5.5 is higher on 121, lower on 89 and tied on 438: no measurable skill over a
  trivial statistical forecast. IFS HRES earns 0.34 to 0.71 per variable and lead. The model used no
  extended thinking (`reports/era5/2026-11-01-claude-sonnet-5-5.md`; baselines, with a mixture
  fitted on a train split, in `reports/era5/items_v1_baselines.md`).

## Phase 4: counting hurricanes by NOAA's rules

[Write-up](reports/ibtracs/2026-11-01-phase-4-writeup.md).

- Beside the ACE figures, the counting code reproduces NCEI's 18 named storms, 11 hurricanes, 5
  major and 2 category 5 hurricanes for 2024 (`reports/ibtracs/2026-11-01-ncei-reproduction.md`).
- With the rules hidden, ACE and peak category stay at 0.99. Hours at hurricane strength fall to
  0.13, and 63 of the 87 misses follow a duration reading, a convention the question does not state
  (`reports/ibtracs/2026-11-01-rules-shown-vs-hidden.md`).
- Without a name or year in the prompt, 2 of 300 rules-shown replies and 4 of 300 rules-hidden ones
  still name the storm or its season (same report).

## Phase 5: a heat policy's payouts and its basis risk

[Write-up](reports/heat/2026-11-01-phase-5-writeup.md).

- Beside the 2023 counts, the counting code reproduces NWS Phoenix's 70 days in 2024, a 113-day run
  at 100 F, and 145 days at 100 F in 2020 (`reports/heat/2026-11-01-nws-phoenix-reproduction.md`).
- The basis risk is in the data: with Scottsdale's airport as the index, the urban core at Sky
  Harbor has 7 to 42 days a season at 110 F that the index misses (decision 0013).
- With the policy terms alone, missed days drop from 0.96 to 0.89. The model misses 7 of the 8 items
  where a missing index value decides the key, all at Deer Valley in 2019: on 6 its answer is the
  other reading of that missing value, which the terms leave open, and on the seventh it is one day
  from that reading (`reports/heat/2026-11-01-rules-shown-vs-terms-only.md`).

## Phase 6: the storm's rows behind a query tool

[Write-up](reports/ibtracs/2026-11-02-phase-6-writeup.md).

- Tools mode asks the same 300 IBTrACS items with the rule left out and each storm's rows behind one
  read-only SQL tool (decision 0023). A first version, run under Inspect's react agent, scores 0.747
  on Sonnet 5.5 against 0.703 with the rows in the prompt: ACE and peak category stay at 0.99 and
  1.00, and hours rise from 0.13 to 0.25, with 16 items right only in that run and 4 only with the
  rows in the prompt, an exact McNemar p of 0.012
  (`reports/ibtracs/2026-11-02-rows-in-prompt-vs-tool-react.md`). React's system prompt is a second
  difference from the prompt run, so that gain is not the tool's alone
  (`docs/reviews/phase-6-tools.md`, M1).
- Tools mode now runs as a plain tool loop in both harnesses. Its Sonnet run has no reported result
  until it finishes.

## Small open models: where the reward varies

Qwen3.5-2B and Granite 4.0 H-1B, 8 samples an item (decisions 0022 and 0025). An item whose reward
varies across its samples is one a GRPO-style update can learn from, and pass@8 is the chance that
any of 8 samples passes.

| environment | Qwen3.5-2B: items that vary | pass@8 | Granite 4.0 H-1B: items that vary | pass@8 | report |
|---|---|---|---|---|---|
| ClimaQA | 0.417 | 0.711 | 0.151 | 0.463 | `reports/climaqa/2026-11-02-small-models.md` |
| IBTrACS | 0.317 | 0.537 | 0.120 | 0.120 | `reports/ibtracs/2026-11-02-small-models.md` |
| heat | 0.487 | 0.523 | 0.163 | 0.163 | `reports/heat/2026-11-02-small-models.md` |
| ERA5 | 0.357 | 0.357 | 0.304 | 0.304 | `reports/era5/2026-11-02-small-models.md` |

ERA5's rows pass at a reward above 0, the others at reward 1. Qwen3.5-2B writes long replies and
Granite very short ones: each report gives the replies cut at the 4,096-token cap and those with no
parseable answer.

## Phase 7: a small GRPO run

[Write-up](reports/grpo/2026-11-02-phase-7-writeup.md).

- Qwen3.5-2B with a LoRA on climaqa-v1 MCQ, 250 steps on a Kaggle T4. On the first 52 train items,
  22 got better, 5 worse and 25 stayed the same (sign test p 0.0015). On the 52 held-out items, 12,
  10 and 30 (p 0.83) (`reports/grpo/2026-11-02-run.md`).
- Replies nearly doubled in length, from a median of 369 tokens to 681 on train and 356.5 to 675 on
  test. The two samplings stopped on different tokens, so the fall in replies cut at the 1,024-token
  cap, 24 to 5 and 39 to 19, is not like for like. The headline holds under the worst case of that
  flaw, and the samplings run again under one stop set (`docs/reviews/phase-7-grpo.md`, H1).

## What it means for RL

- The exact-answer environments of Phases 4 and 5 are saturated for a model as strong as Sonnet 5.5:
  told the rules, it gets nearly every item right, so nearly every rollout earns the same reward.
  Not told them, it still applies NOAA's ACE convention, the Saffir-Simpson scale and the policy's
  thresholds. What remains is convention: hours at hurricane strength, short by a constant 3 or 6
  hours, and a missing index value, which matters only at Deer Valley in 2019. My untested guess is
  that a policy would take either from the reward in a few steps; no training run has checked it.
- In its first version, tools mode adds no headroom for Sonnet 5.5 on ACE or peak category. What it
  adds is a rollout whose transcript records how the model read the data, on the same items and with
  the same reward as the prompt version.
- The forecasting environment of Phase 3 is far from saturated, with no skill yet to build on.

## Spend

$12.2793 of a managed $20 budget on the Anthropic key over 16 runs (a probe projected each run's
cost before it started; the ledger is checked after each run), probes included, all through the
Batch API but the two Phase 6 probes (`reports/spend.md`). Sonnet 5.5 is the only paid model
(decision 0010). The account ran out of credit during the last run, at a ledger total under $20, so
the account's bill and this ledger differ by an amount that is UNKNOWN here. The small models ran on
Kaggle's free GPUs. The Gemini 3.8 Flash runs on Vertex AI are separate and stay as recorded in
their reports; no Vertex AI or Gemini calls are made from 2026-11-01.

## Limits

- One run per model and condition, with no seed: the run-to-run spread is not measured, and one
  Phase 4 storm drew two different hours answers from the same model.
- One paid model on the Anthropic key; the Gemini numbers come from runs that cannot be repeated.
