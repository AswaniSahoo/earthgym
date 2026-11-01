# era5-forecast-v1 baseline rows

Area-weighted RMSE and ACC over the items (WB2 rules), mean reward per item (0007).

| variable | lead h | baseline | n | RMSE | ACC | mean reward |
|---|---|---|---|---|---|---|
| mean_sea_level_pressure | 24 | persistence | 120 | 539.344 | 0.643 | 0.000 |
| mean_sea_level_pressure | 24 | climatology | 120 | 609.904 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | always-climatology policy | 120 | 609.904 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | IFS HRES | 120 | 50.509 | 0.997 | 0.594 |
| mean_sea_level_pressure | 24 | midpoint | 120 | 471.352 | 0.643 | 0.151 |
| mean_sea_level_pressure | 24 | mixture (w 0.67, fitted on the train split) | 120 | 470.126 | 0.643 | 0.136 |
| mean_sea_level_pressure | 48 | persistence | 120 | 754.163 | 0.283 | 0.000 |
| mean_sea_level_pressure | 48 | climatology | 120 | 614.807 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | always-climatology policy | 120 | 614.807 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | IFS HRES | 120 | 76.907 | 0.992 | 0.666 |
| mean_sea_level_pressure | 48 | midpoint | 120 | 607.895 | 0.283 | 0.102 |
| mean_sea_level_pressure | 48 | mixture (w 0.67, fitted on the train split) | 120 | 643.407 | 0.283 | 0.089 |
| mean_sea_level_pressure | 72 | persistence | 120 | 967.296 | 0.086 | 0.000 |
| mean_sea_level_pressure | 72 | climatology | 120 | 726.078 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | always-climatology policy | 120 | 726.078 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | IFS HRES | 120 | 139.379 | 0.981 | 0.570 |
| mean_sea_level_pressure | 72 | midpoint | 120 | 779.265 | 0.086 | 0.081 |
| mean_sea_level_pressure | 72 | mixture (w 0.67, fitted on the train split) | 120 | 831.293 | 0.086 | 0.098 |
| 2m_temperature | 24 | persistence | 120 | 1.448 | 0.825 | 0.000 |
| 2m_temperature | 24 | climatology | 120 | 2.455 | n/a | 0.000 |
| 2m_temperature | 24 | always-climatology policy | 120 | 2.455 | n/a | 0.000 |
| 2m_temperature | 24 | IFS HRES | 120 | 0.726 | 0.955 | 0.303 |
| 2m_temperature | 24 | midpoint | 120 | 1.606 | 0.825 | 0.121 |
| 2m_temperature | 24 | mixture (w 0.67, fitted on the train split) | 120 | 1.443 | 0.825 | 0.139 |
| 2m_temperature | 48 | persistence | 120 | 2.591 | 0.516 | 0.000 |
| 2m_temperature | 48 | climatology | 120 | 2.660 | n/a | 0.000 |
| 2m_temperature | 48 | always-climatology policy | 120 | 2.660 | n/a | 0.000 |
| 2m_temperature | 48 | IFS HRES | 120 | 0.760 | 0.958 | 0.490 |
| 2m_temperature | 48 | midpoint | 120 | 2.279 | 0.516 | 0.116 |
| 2m_temperature | 48 | mixture (w 0.67, fitted on the train split) | 120 | 2.309 | 0.516 | 0.115 |
| 2m_temperature | 72 | persistence | 120 | 2.300 | 0.564 | 0.000 |
| 2m_temperature | 72 | climatology | 120 | 2.536 | n/a | 0.000 |
| 2m_temperature | 72 | always-climatology policy | 120 | 2.536 | n/a | 0.000 |
| 2m_temperature | 72 | IFS HRES | 120 | 0.859 | 0.943 | 0.391 |
| 2m_temperature | 72 | midpoint | 120 | 2.108 | 0.564 | 0.074 |
| 2m_temperature | 72 | mixture (w 0.67, fitted on the train split) | 120 | 2.101 | 0.564 | 0.082 |

## Held out

Mean reward on the test split (119 items, one init week in five by a hash of the week; era5_forecast_v1/contract.py), where the mixture's weight was not fitted:

| forecast | n | mean reward |
|---|---|---|
| persistence | 119 | 0.000 |
| climatology | 119 | 0.000 |
| always-climatology policy | 119 | 0.000 |
| IFS HRES | 119 | 0.478 |
| midpoint | 119 | 0.098 |
| mixture (w 0.67, fitted on the train split) | 119 | 0.094 |

Reward floor per variable: the 10th percentile of the better-baseline error (0007);
it binds where that error is below the floor.

| variable | floor | binds |
|---|---|---|
| mean_sea_level_pressure | 28.750 | 36 of 360 |
| 2m_temperature | 0.069 | 36 of 360 |

## Limits

The baseline is the better of persistence and climatology for each item, picked with the
truth known, so where one of them is nearly exact little skill is left to earn. Items
ranked by that error b and split into quarters:

| variable | quarter | n | median b | IFS HRES mean reward | HRES earns 0 |
|---|---|---|---|---|---|
| mean_sea_level_pressure | 1 | 90 | 35.750 | 0.184 | 56 |
| mean_sea_level_pressure | 2 | 90 | 103.800 | 0.612 | 12 |
| mean_sea_level_pressure | 3 | 90 | 307.300 | 0.775 | 1 |
| mean_sea_level_pressure | 4 | 90 | 821.250 | 0.871 | 1 |
| 2m_temperature | 1 | 90 | 0.075 | 0.086 | 74 |
| 2m_temperature | 2 | 90 | 0.360 | 0.328 | 37 |
| 2m_temperature | 3 | 90 | 0.855 | 0.489 | 19 |
| 2m_temperature | 4 | 90 | 2.645 | 0.676 | 6 |

Items where a baseline is exact, so no reply can earn a reward: mean_sea_level_pressure 0, 2m_temperature 3.
