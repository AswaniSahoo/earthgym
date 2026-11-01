# ibtracs-storm-v1 on claude-sonnet-5-5

Model `anthropic/claude-sonnet-5-5` on 300 items, scored by ibtracs_storm_v1/contract.py at commit 3d11eef.

## Result

Accuracy 0.703 (stderr 0.026) over all 300 items, parse failures and errors scored 0. Each answer is right or wrong against the exact key (decision 0011).

Replies without a parseable answer line: 0 of 300. Samples that errored: 0.

Accuracy per question, with the best constant answer and each careless reading of the rule as baselines:

| question | answer by | n | accuracy |
|---|---|---|---|
| ace | model | 100 | 0.990 |
| ace | best constant (0.5) | 100 | 0.050 |
| ace | ACE over every row | 100 | 0.000 |
| ace | ACE ignoring status | 100 | 0.560 |
| peak_category | model | 100 | 0.990 |
| peak_category | best constant (1) | 100 | 0.350 |
| peak_category | category ignoring status | 100 | 1.000 |
| peak_category | category from synoptic rows only | 100 | 0.960 |
| hurricane_hours | model | 100 | 0.130 |
| hurricane_hours | best constant (12) | 100 | 0.120 |
| hurricane_hours | hours over every HU row | 100 | 0.010 |
| hurricane_hours | elapsed time, first to last HU row | 100 | 0.010 |

Wrong answers by the model that equal a careless reading of the rule:

| question | careless reading | model misses that match |
|---|---|---|
| ace | ACE over every row | 0 |
| ace | ACE ignoring status | 0 |
| peak_category | category ignoring status | 0 |
| peak_category | category from synoptic rows only | 0 |
| hurricane_hours | hours over every HU row | 0 |
| hurricane_hours | elapsed time, first to last HU row | 41 |

## Tokens and cost

2090 input and 227435 output tokens, 124643 of the output reasoning; cache writes 512499, cache reads 2077. Sent through the Batch API, at half price. At the prices in reports/spend.md (Anthropic's pricing page, fetched 2026-11-01): $1.7800, or $0.00593 an item.

## Run config

- Generate settings: batch 100; the rest are the provider's defaults (decision 0010).
- inspect_ai 0.3.286; run from 2026-11-01T01:31:33+00:00 to 2026-11-01T01:37:22+00:00.
- Log `2026-11-01T01-31-33-00-00_ibtracs-storm_Uom4YK44FSJxfdNAGmH86h.eval` (not in git).
- Prompt, rules, answer parser and reward: environments/ibtracs_storm_v1/ibtracs_storm_v1/contract.py at the commit above.

## Limits

- One reply per item, with no seed or temperature set, so a rerun gives other replies;
  the run-to-run spread is not measured.
- The prompt leaves out the name and year, but a model can still recognize a famous
  track; whether any answer was recalled rather than counted is UNKNOWN.
- North Atlantic storms from 1980 to 2025 only, with the rules in the prompt; the
  rules-hidden ablation is not run here.
- The cost uses the token counts in the log; the Anthropic Console's bill is not read.
- peak_category: 'category ignoring status' is right on 100 of 100 items, so on these storms the question mostly tests reading the Saffir-Simpson scale, not the rule's choice of rows (decision 0011).
- peak_category: 'category from synoptic rows only' is right on 96 of 100 items, so on these storms the question mostly tests reading the Saffir-Simpson scale, not the rule's choice of rows (decision 0011).
