# Reproducing NWS Phoenix's published heat counts from GHCN-Daily

Date: 2026-11-01. Code: `src/rlenv/heat/data.py` and `src/rlenv/heat/stats.py`. Tests:
`tests/test_heat_reproduction.py`.

## Result

| year | quantity | ours | published |
|---|---|---|---|
| 2023 | days with a high of 110 F or more | 55 | 55 |
| 2023 | days with a high of 100 F or more | 133 | 133 |
| 2023 | days with a high of 90 F or more | 185 | 185 |
| 2023 | highest temperature and date | 119 F, 19 Jul | 119, 07/19 |
| 2023 | longest stretch of 110 F days | 31, 30 Jun to 30 Jul | 31 (30 Jun 2023 - 30 Jul 2023) |
| 2024 | days with a high of 110 F or more | 70 | 70 |
| 2024 | longest stretch of 100 F days | 113, 27 May to 16 Sep | 113 (27 May 2024 - 16 Sep 2024) |
| 2020 | days with a high of 100 F or more | 145 | 145 |

Published values, read on the live pages on 2026-11-01: NWS Phoenix's climate summary for 2023
(weather.gov/psr/yearinreview2023: "DAYS MAX >= 110 55", "DAYS MAX >= 100 133", "DAYS MAX >= 90
185", "HIGHEST 119 07/19") and the Phoenix column of its extreme temperatures page
(weather.gov/psr/ExtremeTemps, period of record 1896 to 2025).

## Config

- File: `https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/USW00023183.csv.gz` (Phoenix
  Sky Harbor), 1,479,584 bytes, Last-Modified Sun, 01 Nov 2026 00:01:02 GMT, sha256
  `8c0de135bbafa0d0264069ddacf8d5acfed61cd9bef3af0aa7ef27f78b077eed`. NCEI publishes no
  checksum and rewrites the file daily, so the pin is ours and the copy under `data/heat/` (not
  in git) is the one kept.
- Reader: the standard library `gzip` and `csv` modules; TMAX rows only; values with a quality
  flag dropped (none in these years).
- Rule: GHCN-Daily stores a whole-degree-F reading in tenths of a degree C, so the comparison is
  made in that unit: a day reaches 110 F when its value is at least round((110 - 32) * 50 / 9) =
  433. A run is consecutive calendar days; a missing day ends it.
- Commands:

      uv run python -m rlenv.heat.data      # about 1.5 MB, anonymous HTTPS
      uv run pytest tests/test_heat_reproduction.py

## Limits

- One station. The file is rewritten every day, and a later build can revise old values; the pin
  catches that.
- NOAA names no licence for GHCN-Daily, only citations (doi:10.7289/V5D21VHZ).
