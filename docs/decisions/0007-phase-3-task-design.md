# 0007: what a Phase 3 task asks

Date: 2026-10-30. Status: accepted (Aswani, 2026-10-30), option 1 with his reward rule below.

Context: stage 1 gave a grader that reproduces two published WeatherBench 2 scores exactly
(IFS HRES MSLP at 72 h, 2020: RMSE 133.890547 Pa and ACC 0.981878;
`reports/era5/2026-10-30-wb2-reproduction.md`). The README says Phase 3 is "graded against
weatherbench2", which fits two task designs. The radar found no environment that scores
forecasts with the WB2 rules; numeric question answering over ERA5 already exists (Zephyrus,
TerraBench; `docs/radar.md`).

Options considered:

1. Forecast-answer tasks: the model forecasts a value and the WB2 rules grade it.
2. Score-computation tasks: the model computes RMSE, bias or ACC from a small crop. Exact, but
   it mostly tests arithmetic and conventions, close to existing numeric QA.

Decision: option 1.

- A prompt gives a 64x32 grid cell, a variable (MSLP or 2 m temperature), an init time in
  2020, a lead of 24, 48 or 72 h, the cell's ERA5 values over the three days up to the init
  and the climatology at the valid time. The reply ends with a line `ANSWER: <number>`.
- Reward per item, Aswani's rule: skill over the better of persistence and climatology for
  that item, bounded, so copying a baseline earns zero. With truth y, forecast f, persistence p
  (the cell's ERA5 value at the init time) and climatology c, let e = |f - y| and
  b = min(|p - y|, |c - y|). The reward is clip((b - e) / max(b, floor), 0, 1). A copy of p or
  c gives e >= b and so 0. A reply without a valid answer line scores 0.
- The floor is a technical guard, not Aswani's decision: it only stops a near-zero b from
  inflating the reward, so it should bind rarely. Rule: each variable's floor is the 10th
  percentile (numpy's linear rule) of b over the item set, a baseline-only statistic with no
  model information, and each item carries its floor. On the 720 items that gives 28.75 Pa for
  MSLP and 0.069 K for 2 m temperature, each binding on 36 of 360 items
  (`reports/era5/items_v1_manifest.json`). The first values, 50 Pa and 0.5 K, were the build
  session's own guess; they bound on 65 and 167 of 360.
- The eval reports WB2-graded RMSE and ACC over the items with area weights, and baseline rows
  for persistence, climatology, an always-climatology policy run through the parser and the
  reward (its mean reward must be 0), and IFS HRES at the same cells.

Consequences: the data (ERA5, climatology and HRES for MSLP and 2 m temperature, 2020, three
leads) stays under 100 MB by the radar's sizes. No paid run: tests use mockllm, and a baseline
run needs Aswani's yes.
