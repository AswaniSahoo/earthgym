# era5-forecast-v1 baseline rows

Area-weighted RMSE and ACC over the items (WB2 rules), mean reward per item (0007).

| variable | lead h | baseline | n | RMSE | ACC | mean reward |
|---|---|---|---|---|---|---|
| mean_sea_level_pressure | 24 | persistence | 120 | 539.344 | 0.643 | 0.000 |
| mean_sea_level_pressure | 24 | climatology | 120 | 609.904 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | always-climatology policy | 120 | 609.904 | n/a | 0.000 |
| mean_sea_level_pressure | 24 | IFS HRES | 120 | 50.509 | 0.997 | 0.594 |
| mean_sea_level_pressure | 48 | persistence | 120 | 754.163 | 0.283 | 0.000 |
| mean_sea_level_pressure | 48 | climatology | 120 | 614.807 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | always-climatology policy | 120 | 614.807 | n/a | 0.000 |
| mean_sea_level_pressure | 48 | IFS HRES | 120 | 76.907 | 0.992 | 0.666 |
| mean_sea_level_pressure | 72 | persistence | 120 | 967.296 | 0.086 | 0.000 |
| mean_sea_level_pressure | 72 | climatology | 120 | 726.078 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | always-climatology policy | 120 | 726.078 | n/a | 0.000 |
| mean_sea_level_pressure | 72 | IFS HRES | 120 | 139.379 | 0.981 | 0.570 |
| 2m_temperature | 24 | persistence | 120 | 1.448 | 0.825 | 0.000 |
| 2m_temperature | 24 | climatology | 120 | 2.455 | n/a | 0.000 |
| 2m_temperature | 24 | always-climatology policy | 120 | 2.455 | n/a | 0.000 |
| 2m_temperature | 24 | IFS HRES | 120 | 0.726 | 0.955 | 0.303 |
| 2m_temperature | 48 | persistence | 120 | 2.591 | 0.516 | 0.000 |
| 2m_temperature | 48 | climatology | 120 | 2.660 | n/a | 0.000 |
| 2m_temperature | 48 | always-climatology policy | 120 | 2.660 | n/a | 0.000 |
| 2m_temperature | 48 | IFS HRES | 120 | 0.760 | 0.958 | 0.490 |
| 2m_temperature | 72 | persistence | 120 | 2.300 | 0.564 | 0.000 |
| 2m_temperature | 72 | climatology | 120 | 2.536 | n/a | 0.000 |
| 2m_temperature | 72 | always-climatology policy | 120 | 2.536 | n/a | 0.000 |
| 2m_temperature | 72 | IFS HRES | 120 | 0.859 | 0.943 | 0.391 |

Reward floor per variable: the 10th percentile of the better-baseline error (0007);
it binds where that error is below the floor.

| variable | floor | binds |
|---|---|---|
| mean_sea_level_pressure | 28.750 | 36 of 360 |
| 2m_temperature | 0.069 | 36 of 360 |
