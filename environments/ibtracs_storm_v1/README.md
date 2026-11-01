# ibtracs-storm-v1

Per-storm questions about North Atlantic tropical cyclones from IBTrACS, with exact answers
(decisions 0009 and 0011). Each of the 300 items is one storm from the 1980 to 2025 seasons and
one question: its accumulated cyclone energy (100 items), its peak Saffir-Simpson category (100)
or its hours at hurricane strength (100), drawn with seed 2026 from 613 eligible storms. The
prompt shows every row the archive has for the storm (the 6-hourly rows, the 3-hourly rows
between them and extra rows such as landfall), with the time as month, day and UTC hour, the
status, the wind in kt and the pressure in mb; no name, year or storm id. The rule for the
question is in the prompt. The reply must end with a line `ANSWER: <number>`.

Reward per item, from `ibtracs_storm_v1/contract.py`: 1 for a right answer, else 0. ACE is
right only at one decimal, as the exact value rounded or, when the exact value is a tie, either
neighbour; category and hours must match exactly (decision 0016).

The keys come from `src/rlenv/ibtracs/stats.py`, which reproduces NCEI's published North
Atlantic season numbers (`reports/ibtracs/2026-11-01-ncei-reproduction.md`).

Rebuild the items from the repo root, after `uv run python -m rlenv.ibtracs.data` has fetched
the pinned 57.6 MB CSV (the items' sha256 is in `reports/ibtracs/items_v1_manifest.json`):

    uv run python -m rlenv.ibtracs.items

Data: IBTrACS v04r01 (Knapp, Kruk, Levinson, Diamond and Neumann 2010, BAMS 91,
doi:10.1175/2009BAMS2755.1; Gahtan et al. 2024, NOAA NCEI, doi:10.25921/82ty-9e16), "full and
open access", with WMO Resolution 40 as the guide for commercial use.
