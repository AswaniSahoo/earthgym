# heat-basis-v1 on claude-sonnet-5-5 (terms only)

Model `anthropic/claude-sonnet-5-5` on 300 items, scored by heat_basis_v1/contract.py at commit bb6fd9b.

## Result

Accuracy 0.960 (stderr 0.011) over all 300 items, parse failures and errors scored 0. Each answer is right or wrong against the exact key (decision 0013).

Replies without a parseable answer line: 0 of 300. Samples that errored: 0.

Accuracy per question, with the best constant answer and each careless reading of the rule as baselines:

| question | answer by | n | accuracy |
|---|---|---|---|
| trigger_days | model | 100 | 0.990 |
| trigger_days | best constant (5) | 100 | 0.050 |
| trigger_days | above, not at, the threshold | 100 | 0.070 |
| trigger_days | the site's column | 100 | 0.030 |
| events | model | 100 | 1.000 |
| events | best constant (0) | 100 | 0.270 |
| events | trigger days, not events | 100 | 0.030 |
| events | every run, whatever its length | 100 | 0.090 |
| events | missing days skipped | 100 | 0.990 |
| missed_days | model | 100 | 0.890 |
| missed_days | best constant (3) | 100 | 0.090 |
| missed_days | both ways | 100 | 0.710 |
| missed_days | every hot site day | 100 | 0.020 |
| missed_days | missing index days left out | 100 | 0.920 |

Wrong answers by the model that equal a careless reading of the rule:

| question | careless reading | model misses that match |
|---|---|---|
| trigger_days | above, not at, the threshold | 0 |
| trigger_days | the site's column | 0 |
| events | trigger days, not events | 0 |
| events | every run, whatever its length | 0 |
| events | missing days skipped | 0 |
| missed_days | both ways | 0 |
| missed_days | every hot site day | 0 |
| missed_days | missing index days left out | 6 |

## Tokens and cost

618216 input and 257075 output tokens, 160216 of the output reasoning; cache writes 0, cache reads 0. Sent through the Batch API, at half price. At the prices in reports/spend.md (Anthropic's pricing page, fetched 2026-11-01): $1.9036, or $0.00635 an item.

## Run config

- Generate settings: cache_prompt False, batch 100; the rest are the provider's defaults (decision 0010).
- inspect_ai 0.3.286; run from 2026-11-01T04:15:23+00:00 to 2026-11-01T04:25:14+00:00.
- Log `2026-11-01T04-15-23-00-00_heat-basis_3LBF436XUqfAmbhB6pqHtN.eval` (not in git).
- Prompt, rules, answer parser and reward: environments/heat_basis_v1/heat_basis_v1/contract.py at the commit above.

## Limits

- One reply per item, with no seed or temperature set, so a rerun gives other replies;
  the run-to-run spread is not measured.
- The prompt leaves out the year. The station data are public, but a recalled daily
  series is unlikely; whether any answer was recalled rather than counted is UNKNOWN.
- Four Phoenix-area stations, seasons 2015 to 2024. The prompt gives the policy terms alone; the rules-shown run is the control.
- The cost uses the token counts in the log; the Anthropic Console's bill is not read.
- events: 'missing days skipped' is right on 99 of 100 items, so on these storms the question mostly tests finding the runs, not the rule's choice of rows (decision 0013).
- missed_days: 'missing index days left out' is right on 92 of 100 items, so on these storms the question mostly tests comparing the two columns, not the rule's choice of rows (decision 0013).
