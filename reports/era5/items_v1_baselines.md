# era5-forecast-v1 baseline rows

Area-weighted RMSE and ACC over the items (WB2 rules), mean reward per item (0007).

| variable | lead h | baseline | n | RMSE | ACC | mean reward |
|---|---|---|---|---|---|---|
| mean_sea_level_pressure | 24 | persistence | 100 | 521.810 | 0.707 | 0.000 |
| mean_sea_level_pressure | 24 | climatology | 100 | 687.087 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | always-climatology policy | 100 | 687.087 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | IFS HRES | 100 | 48.406 | 0.998 | 0.709 |
| mean_sea_level_pressure | 24 | midpoint | 100 | 507.819 | 0.707 | 0.178 |
| mean_sea_level_pressure | 24 | mixture (w 0.67, fitted on the train split) | 100 | 486.958 | 0.707 | 0.163 |
| mean_sea_level_pressure | 48 | persistence | 114 | 762.595 | 0.291 | 0.000 |
| mean_sea_level_pressure | 48 | climatology | 114 | 635.903 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | always-climatology policy | 114 | 635.903 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | IFS HRES | 114 | 78.145 | 0.993 | 0.701 |
| mean_sea_level_pressure | 48 | midpoint | 114 | 623.782 | 0.291 | 0.102 |
| mean_sea_level_pressure | 48 | mixture (w 0.67, fitted on the train split) | 114 | 656.681 | 0.291 | 0.092 |
| mean_sea_level_pressure | 72 | persistence | 110 | 1015.280 | 0.086 | 0.000 |
| mean_sea_level_pressure | 72 | climatology | 110 | 764.512 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | always-climatology policy | 110 | 764.512 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | IFS HRES | 110 | 146.291 | 0.982 | 0.622 |
| mean_sea_level_pressure | 72 | midpoint | 110 | 819.597 | 0.086 | 0.088 |
| mean_sea_level_pressure | 72 | mixture (w 0.67, fitted on the train split) | 110 | 873.683 | 0.086 | 0.103 |
| 2m_temperature | 24 | persistence | 106 | 1.540 | 0.818 | 0.000 |
| 2m_temperature | 24 | climatology | 106 | 2.562 | n/a | 0.000 |
| 2m_temperature | 24 | always-climatology policy | 106 | 2.562 | n/a | 0.000 |
| 2m_temperature | 24 | IFS HRES | 106 | 0.758 | 0.955 | 0.342 |
| 2m_temperature | 24 | midpoint | 106 | 1.691 | 0.818 | 0.134 |
| 2m_temperature | 24 | mixture (w 0.67, fitted on the train split) | 106 | 1.527 | 0.818 | 0.158 |
| 2m_temperature | 48 | persistence | 109 | 2.745 | 0.474 | 0.000 |
| 2m_temperature | 48 | climatology | 109 | 2.708 | n/a | 0.000 |
| 2m_temperature | 48 | always-climatology policy | 109 | 2.708 | n/a | 0.000 |
| 2m_temperature | 48 | IFS HRES | 109 | 0.723 | 0.964 | 0.528 |
| 2m_temperature | 48 | midpoint | 109 | 2.384 | 0.474 | 0.128 |
| 2m_temperature | 48 | mixture (w 0.67, fitted on the train split) | 109 | 2.433 | 0.474 | 0.127 |
| 2m_temperature | 72 | persistence | 109 | 2.451 | 0.558 | 0.000 |
| 2m_temperature | 72 | climatology | 109 | 2.687 | n/a | 0.000 |
| 2m_temperature | 72 | always-climatology policy | 109 | 2.687 | n/a | 0.000 |
| 2m_temperature | 72 | IFS HRES | 109 | 0.865 | 0.949 | 0.430 |
| 2m_temperature | 72 | midpoint | 109 | 2.243 | 0.558 | 0.081 |
| 2m_temperature | 72 | mixture (w 0.67, fitted on the train split) | 109 | 2.238 | 0.558 | 0.091 |

## Held out

Mean reward on the test split (102 items, one init week in five by a hash of the week; era5_forecast_v1/contract.py), where the mixture's weight was not fitted:

| forecast | n | mean reward |
|---|---|---|
| persistence | 102 | 0.000 |
| climatology | 102 | 0.000 |
| always-climatology policy | 102 | 0.000 |
| IFS HRES | 102 | 0.554 |
| midpoint | 102 | 0.109 |
| mixture (w 0.67, fitted on the train split) | 102 | 0.108 |

Reward floor per variable: the 10th percentile of the better-baseline error (0007);
it binds where that error is below the floor.

| variable | floor | binds |
|---|---|---|
| mean_sea_level_pressure | 28.750 | 0 of 324 |
| 2m_temperature | 0.069 | 0 of 324 |

## Limits

The baseline is the better of persistence and climatology for each item, picked with the
truth known, so where one of them is nearly exact little skill is left to earn. Items
ranked by that error b and split into quarters:

| variable | quarter | n | median b | IFS HRES mean reward | HRES earns 0 |
|---|---|---|---|---|---|
| mean_sea_level_pressure | 1 | 81 | 57.200 | 0.401 | 27 |
| mean_sea_level_pressure | 2 | 81 | 146.900 | 0.652 | 9 |
| mean_sea_level_pressure | 3 | 81 | 378.100 | 0.787 | 1 |
| mean_sea_level_pressure | 4 | 81 | 879.900 | 0.867 | 1 |
| 2m_temperature | 1 | 81 | 0.150 | 0.163 | 53 |
| 2m_temperature | 2 | 81 | 0.450 | 0.380 | 31 |
| 2m_temperature | 3 | 81 | 0.990 | 0.525 | 13 |
| 2m_temperature | 4 | 81 | 2.830 | 0.670 | 6 |

Items where a baseline is exact, so no reply can earn a reward: mean_sea_level_pressure 0, 2m_temperature 0.
