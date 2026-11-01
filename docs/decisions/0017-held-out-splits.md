# 0017: a held-out split by group in every taskset

Date: 2026-11-02. Status: accepted, 2026-11-02. From the Codex review's finding 2, which I took
up in fix batch 1.

Context: items that share their data (one storm's track, one season's station readings, one
week's weather) make a random split leak, since a policy trained on one item can learn what
another item asks. The tasksets had no split at all, so no held-out evaluation was possible.

Decision: each `contract.py` has `group(item)` and `split(item)`. An item is in `test` when the
first byte of the sha256 of its group key is 0 modulo 5, about one group in five, else in
`train`: no seed, no state, and a group never straddles the split. Each verifiers taskset takes
`split="train"` or `split="test"` in its config; with no split, the default, it loads every item
as before.

| environment | group | train items (groups) | test items (groups) |
|---|---|---|---|
| climaqa-v1 | the item, since ClimaQA gives no source passage | 269 (269) | 81 (81) |
| era5-forecast-v1 | the ISO week of the init time | 546 (43) | 102 (10) |
| ibtracs-storm-v1 | the storm (IBTrACS SID) | 233 (233) | 67 (67) |
| heat-basis-v1 | the season | 245 (8) | 55 (2: 2017 and 2020) |

For heat the season is the smallest group that keeps every station-season on one side: each
index station is paired with both sites, so the four pairs of a season share all four stations.
`tests/test_splits.py` checks that each split partitions the items and that no group is on both
sides.

Consequences:

- No training run uses the split, and no result in this repo comes from one. The split makes a
  held-out evaluation possible; it does not show that a policy generalizes.
- The reported model runs cover every item. The ERA5 baselines report already fits the mixture
  weight on `train` and scores it on `test` (`reports/era5/items_v1_baselines.md`).
- Limits: two ClimaQA items from one textbook passage can fall on different sides, and how many
  share a passage is UNKNOWN. Weather does not stop at a week boundary: ERA5 inits are at 00 and 12
  UTC, so a train init and a test init can be 12 hours apart. On the 720 drawn items one test item's
  truth was among the values a train item's prompt shows (same cell and variable); that item failed
  the gold check (decision 0021), and among the 648 that remain none does. Storms of one season
  share large-scale conditions, though each item shows only its own track. The heat test split is 2
  of 10 seasons, 55 items.
- The Inspect tasks still run every item; a split option there is a later change.
