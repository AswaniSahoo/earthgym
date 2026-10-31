# Reproducing NCEI's North Atlantic season numbers from IBTrACS

Date: 2026-11-01. Code: `src/rlenv/ibtracs/data.py` and `src/rlenv/ibtracs/stats.py` at commit
e640dc7. Tests: `tests/test_ibtracs_reproduction.py`.

## Result

| season | quantity | ours | published |
|---|---|---|---|
| 1933 | ACE (1e4 kt^2) | 258.57 | 258.6 |
| 2005 | hurricanes, major hurricanes | 15, 7 | 15, 7 |
| 2020 | named storms, major hurricanes | 30, 7 | 30, 7 |
| 2024 | named storms, hurricanes, major hurricanes | 18, 11, 5 | 18, 11, 5 |
| 2024 | ACE (1e4 kt^2) | 161.58 | 161.6 |

Published values: NCEI's annual tropical cyclone reports (`ncei.noaa.gov/access/monitoring/
monthly-report/tropical-cyclones/202413` and `/202513`) and NHC's 2024 season summary, as the
Phase 4 radar records them (`docs/radar.md`). Not anchored here, from the same code: 2005 has
28 named storms and 2020 has 14 hurricanes.

## Config

- File: `https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NA.list.v04r01.csv`,
  57,593,323 bytes, Last-Modified Fri, 30 Oct 2026 04:27:28 GMT, sha256
  `666681be5b12caf5bad7a511bae5f6e5fa8b03789f7f6dd00ee2f0aaa41c2c97`. NCEI publishes no
  checksum and overwrites the file in place, so the pin is ours and the copy under
  `data/ibtracs/` (not in git) is the one kept; a newer build fails the pin.
- Reader: the standard library `csv` module; the second header row (units) skipped; every cell
  stripped, since a blank is a single space.
- Rules (NOAA CPC, by way of the radar): ACE is the sum of squared `USA_WIND` at 00, 06, 12 and
  18 UTC while `USA_STATUS` is TS, HU or SS and the wind is at least 34 kt, times 1e-4; the
  3-hourly interpolated rows are left out, because summing them doubles ACE. A named storm,
  hurricane or major hurricane has a row at 34 kt with that status, or 64 or 96 kt as HU.
  Spur tracks are left out, and only rows with `BASIN` NA count (counting every row of each
  storm gives the same numbers for these four seasons).
- Commands:

      uv run python -m rlenv.ibtracs.data      # about 58 MB, anonymous HTTPS
      uv run pytest tests/test_ibtracs_reproduction.py

## Limits

- Provisional data: 458 rows of the 2025 and 2026 seasons carry `TRACK_TYPE` PROVISIONAL. NCEI
  published 2025's ACE as 132.6 from provisional tracks; today's build gives 130.77. Seasons
  with provisional rows are not used as answer keys.
- Reanalysis rewrites old seasons in place, so another build can change any number above;
  the pin catches that.
- North Atlantic only: agencies in other basins average wind over 1, 2, 3 or 10 minutes, and
  those winds are never pooled.

## Attribution

IBTrACS: Knapp, Kruk, Levinson, Diamond and Neumann (2010), BAMS 91, doi:10.1175/2009BAMS2755.1;
Gahtan et al. (2024), IBTrACS Version 4r01, NOAA NCEI, doi:10.25921/82ty-9e16. Terms: "full
and open access", with WMO Resolution 40 as the guide for commercial use.
