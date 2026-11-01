# README corrections for the rewrite

Collected during fix batch 1 (2026-11-02); folded into the README rewrite and then deleted.

- Phase 3 row: add that the midpoint of persistence and climatology earns 0.1074 against the
  model's 0.1161, a difference of +0.0087 (SE 0.0077), not significant
  (`reports/era5/2026-11-01-claude-sonnet-5-5.md`).
- Phase 2 row and the `climaqa-v1` table row: say exact-overlap-filtered, with 21 near matches
  of Silver unresolved and a strict 329-item variant (`-T strict=true`), not "clean" alone.
- "with $20 in total as a hard cap": say a managed budget of $20 (probe projections before
  each run, the ledger checked after), not a hard cap (decision 0010).
- `era5-forecast-v1` row, "graded by the WB2 rules": the reward is a custom clipped skill score;
  the WB2 rules give the RMSE and ACC reference metrics, not the reward.
- `ibtracs-storm-v1` row: ACE pays only its one-decimal rounding, or either neighbour at an
  exact tie, not any answer within 0.05 (decision 0016).
- Each environment row: a held-out split by group, `split="train"` or `"test"` in the taskset
  config (decision 0017).
- License section: the pinned IBTrACS build is the `data-v1` release asset; the GHCN-Daily
  station files are not published, since NOAA names no licence for them (decision 0018).
- Reproduce section: point to `docs/reproduce.md` (rebuild the data, recompute the published
  numbers from `reports/<env>/results/`, run fresh evals), and name the weekly `reproduce`
  workflow beside `ci` (decision 0019).
