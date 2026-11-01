# era5-forecast-v1 on claude-sonnet-5-5

Model `anthropic/claude-sonnet-5-5` on 648 items, scored by era5_forecast_v1/contract.py at commit bbafe0e. The run answered 720 items; 72 of them failed the gold check (decision 0021) and are left out of every number here.

## Result

Mean reward 0.128 (stderr 0.010) over all 648 items, parse failures and errors scored 0. The reward is the skill over the better of persistence and climatology for each item, clipped to [0, 1] (decision 0007).

Replies without a parseable answer line: 0 of 648. Samples that errored: 0.

Against the midpoint (persistence + climatology) / 2, item by item: +0.0102 (SE 0.0085); the model is higher on 121 items, lower on 89 and tied on 438: not significant at two standard errors.

Area-weighted RMSE and ACC by the WB2 rules, and the mean reward, on the 648 items with a parsed answer, each baseline on the same items:

| variable | lead h | forecast | n | RMSE | ACC | mean reward |
|---|---|---|---|---|---|---|
| mean_sea_level_pressure | 24 | persistence | 100 | 521.810 | 0.707 | 0.000 |
| mean_sea_level_pressure | 24 | climatology | 100 | 687.087 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | always-climatology policy | 100 | 687.087 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | IFS HRES | 100 | 48.406 | 0.998 | 0.709 |
| mean_sea_level_pressure | 24 | midpoint | 100 | 507.819 | 0.707 | 0.178 |
| mean_sea_level_pressure | 24 | mixture (w 0.67, fitted on the train split) | 100 | 486.958 | 0.707 | 0.163 |
| mean_sea_level_pressure | 24 | claude-sonnet-5-5 | 100 | 522.072 | 0.651 | 0.171 |
| mean_sea_level_pressure | 48 | persistence | 114 | 762.595 | 0.291 | 0.000 |
| mean_sea_level_pressure | 48 | climatology | 114 | 635.903 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | always-climatology policy | 114 | 635.903 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | IFS HRES | 114 | 78.145 | 0.993 | 0.701 |
| mean_sea_level_pressure | 48 | midpoint | 114 | 623.782 | 0.291 | 0.102 |
| mean_sea_level_pressure | 48 | mixture (w 0.67, fitted on the train split) | 114 | 656.681 | 0.291 | 0.092 |
| mean_sea_level_pressure | 48 | claude-sonnet-5-5 | 114 | 598.986 | 0.370 | 0.112 |
| mean_sea_level_pressure | 72 | persistence | 110 | 1015.280 | 0.086 | 0.000 |
| mean_sea_level_pressure | 72 | climatology | 110 | 764.512 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | always-climatology policy | 110 | 764.512 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | IFS HRES | 110 | 146.291 | 0.982 | 0.622 |
| mean_sea_level_pressure | 72 | midpoint | 110 | 819.597 | 0.086 | 0.088 |
| mean_sea_level_pressure | 72 | mixture (w 0.67, fitted on the train split) | 110 | 873.683 | 0.086 | 0.103 |
| mean_sea_level_pressure | 72 | claude-sonnet-5-5 | 110 | 776.375 | 0.147 | 0.099 |
| 2m_temperature | 24 | persistence | 106 | 1.540 | 0.818 | 0.000 |
| 2m_temperature | 24 | climatology | 106 | 2.562 | n/a | 0.000 |
| 2m_temperature | 24 | always-climatology policy | 106 | 2.562 | n/a | 0.000 |
| 2m_temperature | 24 | IFS HRES | 106 | 0.758 | 0.955 | 0.342 |
| 2m_temperature | 24 | midpoint | 106 | 1.691 | 0.818 | 0.134 |
| 2m_temperature | 24 | mixture (w 0.67, fitted on the train split) | 106 | 1.527 | 0.818 | 0.158 |
| 2m_temperature | 24 | claude-sonnet-5-5 | 106 | 1.493 | 0.814 | 0.155 |
| 2m_temperature | 48 | persistence | 109 | 2.745 | 0.474 | 0.000 |
| 2m_temperature | 48 | climatology | 109 | 2.708 | n/a | 0.000 |
| 2m_temperature | 48 | always-climatology policy | 109 | 2.708 | n/a | 0.000 |
| 2m_temperature | 48 | IFS HRES | 109 | 0.723 | 0.964 | 0.528 |
| 2m_temperature | 48 | midpoint | 109 | 2.384 | 0.474 | 0.128 |
| 2m_temperature | 48 | mixture (w 0.67, fitted on the train split) | 109 | 2.433 | 0.474 | 0.127 |
| 2m_temperature | 48 | claude-sonnet-5-5 | 109 | 2.308 | 0.523 | 0.139 |
| 2m_temperature | 72 | persistence | 109 | 2.451 | 0.558 | 0.000 |
| 2m_temperature | 72 | climatology | 109 | 2.687 | n/a | 0.000 |
| 2m_temperature | 72 | always-climatology policy | 109 | 2.687 | n/a | 0.000 |
| 2m_temperature | 72 | IFS HRES | 109 | 0.865 | 0.949 | 0.430 |
| 2m_temperature | 72 | midpoint | 109 | 2.243 | 0.558 | 0.081 |
| 2m_temperature | 72 | mixture (w 0.67, fitted on the train split) | 109 | 2.238 | 0.558 | 0.091 |
| 2m_temperature | 72 | claude-sonnet-5-5 | 109 | 2.260 | 0.555 | 0.096 |

## Tokens and cost

322920 input and 257940 output tokens, 0 of the output reasoning; cache writes 0, cache reads 0. Sent through the Batch API, at half price. At the prices in reports/spend.md (Anthropic's pricing page, fetched 2026-11-01): $1.6126, or $0.00249 an item.

## Run config

- Generate settings: batch 100; the rest are the provider's defaults (decision 0010).
- inspect_ai 0.3.286; run from 2026-10-31T22:57:01+00:00 to 2026-10-31T23:03:42+00:00.
- Log `2026-10-31T22-57-01-00-00_era5-forecast_EQsEdqHe9poQqx6NiBoJUg.eval` (not in git).
- Prompt, answer parser and reward: environments/era5_forecast_v1/era5_forecast_v1/contract.py at the commit above.

## Limits

- One reply per item, with no seed or temperature set, so a rerun gives other replies;
  the run-to-run spread is not measured.
- The reward's baseline is the better of persistence and climatology for each item,
  picked with the truth known, so items where one is nearly exact leave little to earn
  (reports/era5/items_v1_baselines.md).
- The items are 2020 ERA5 values, which are public; whether the model saw them in
  training is UNKNOWN.
- The cost uses the token counts in the log; the Anthropic Console's bill is not read.
