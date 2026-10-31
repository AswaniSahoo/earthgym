# era5-forecast-v1 on claude-sonnet-5-5

Model `anthropic/claude-sonnet-5-5` on 720 items, scored by era5_forecast_v1/contract.py at commit bbafe0e.

## Result

Mean reward 0.116 (stderr 0.009) over all 720 items, parse failures and errors scored 0. The reward is the skill over the better of persistence and climatology for each item, clipped to [0, 1] (decision 0007).

Replies without a parseable answer line: 0 of 720. Samples that errored: 0.

Area-weighted RMSE and ACC by the WB2 rules, and the mean reward, on the 720 items with a parsed answer, each baseline on the same items:

| variable | lead h | forecast | n | RMSE | ACC | mean reward |
|---|---|---|---|---|---|---|
| mean_sea_level_pressure | 24 | persistence | 120 | 539.344 | 0.643 | 0.000 |
| mean_sea_level_pressure | 24 | climatology | 120 | 609.904 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | always-climatology policy | 120 | 609.904 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | IFS HRES | 120 | 50.509 | 0.997 | 0.594 |
| mean_sea_level_pressure | 24 | claude-sonnet-5-5 | 120 | 487.508 | 0.613 | 0.147 |
| mean_sea_level_pressure | 48 | persistence | 120 | 754.163 | 0.283 | 0.000 |
| mean_sea_level_pressure | 48 | climatology | 120 | 614.807 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | always-climatology policy | 120 | 614.807 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | IFS HRES | 120 | 76.907 | 0.992 | 0.666 |
| mean_sea_level_pressure | 48 | claude-sonnet-5-5 | 120 | 586.037 | 0.357 | 0.109 |
| mean_sea_level_pressure | 72 | persistence | 120 | 967.296 | 0.086 | 0.000 |
| mean_sea_level_pressure | 72 | climatology | 120 | 726.078 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | always-climatology policy | 120 | 726.078 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | IFS HRES | 120 | 139.379 | 0.981 | 0.570 |
| mean_sea_level_pressure | 72 | claude-sonnet-5-5 | 120 | 738.092 | 0.147 | 0.091 |
| 2m_temperature | 24 | persistence | 120 | 1.448 | 0.825 | 0.000 |
| 2m_temperature | 24 | climatology | 120 | 2.455 | n/a | 0.000 |
| 2m_temperature | 24 | always-climatology policy | 120 | 2.455 | n/a | 0.000 |
| 2m_temperature | 24 | IFS HRES | 120 | 0.726 | 0.955 | 0.303 |
| 2m_temperature | 24 | claude-sonnet-5-5 | 120 | 1.405 | 0.821 | 0.136 |
| 2m_temperature | 48 | persistence | 120 | 2.591 | 0.516 | 0.000 |
| 2m_temperature | 48 | climatology | 120 | 2.660 | n/a | 0.000 |
| 2m_temperature | 48 | always-climatology policy | 120 | 2.660 | n/a | 0.000 |
| 2m_temperature | 48 | IFS HRES | 120 | 0.760 | 0.958 | 0.490 |
| 2m_temperature | 48 | claude-sonnet-5-5 | 120 | 2.198 | 0.564 | 0.126 |
| 2m_temperature | 72 | persistence | 120 | 2.300 | 0.564 | 0.000 |
| 2m_temperature | 72 | climatology | 120 | 2.536 | n/a | 0.000 |
| 2m_temperature | 72 | always-climatology policy | 120 | 2.536 | n/a | 0.000 |
| 2m_temperature | 72 | IFS HRES | 120 | 0.859 | 0.943 | 0.391 |
| 2m_temperature | 72 | claude-sonnet-5-5 | 120 | 2.126 | 0.560 | 0.087 |

## Tokens and cost

322920 input and 257940 output tokens, 0 of the output reasoning; cache writes 0, cache reads 0. Sent through the Batch API, at half price. At the prices in reports/spend.md (Anthropic's pricing page, fetched 2026-11-01): $1.6126, or $0.00224 an item.

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
