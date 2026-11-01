# heat-basis-v1

Questions about a parametric heat policy over real station data, with exact answers (decisions
0012 and 0013). The index stations are two Phoenix-area airports (Scottsdale Municipal and
Phoenix Deer Valley Municipal); the insured sites are in the hotter urban core (Phoenix Sky
Harbor and Tempe ASU), 20.7 to 32.3 km away. Each of the 300 items is one season from 2015 to
2024, a cover window of 1 May to 30 September, a whole-degree threshold from 100 to 115 F and
one question: the index station's trigger days, the events the policy pays (runs of at least
2 to 5 consecutive trigger days), or the missed days, when the site was at or above the
threshold and the index was not: the policyholder's side of basis risk (days the index paid
while the site was not hot are not asked). 100 items per question, seed 2026. The
missing-value rules change a key only at Deer Valley in 2019, the one index season with gaps.

The prompt shows both stations' daily maxima in whole degrees F, a dash for a missing value,
the year left out, and the rule for the question. The reply must end with `ANSWER: <number>`.
The reward is 1 for the exact count, else 0 (`heat_basis_v1/contract.py`).

A held-out split by season, so every station's readings for a season fall on one side:
`HeatConfig(split="train")` loads 245 items and `split="test"` 55, the 2017 and 2020 seasons
(decision 0017).

The counting code reproduces NWS Phoenix's published heat counts from the same GHCN-Daily
files (`reports/heat/2026-11-01-nws-phoenix-reproduction.md`). Rebuild the items from the repo
root (about 2.9 MB of pinned station files; the items' sha256 is in
`reports/heat/items_v1_manifest.json`):

    uv run python -m earthgym.heat.data
    uv run python -m earthgym.heat.items

Data: GHCN-Daily (NOAA NCEI), doi:10.7289/V5D21VHZ. NOAA names no licence for it.
