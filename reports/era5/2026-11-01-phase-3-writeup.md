# Scoring a language model's weather forecasts, with WeatherBench 2 metrics as the check

Phase 3 of earthgym, written up on 2026-11-01. Every number below comes from a report in this
repo; the source is named next to it.

Update, 2026-11-02: the gold check (decision 0021) dropped the 72 of the 720 items where a
perfect forecast cannot earn the whole reward, because the floor binds. The numbers below are
the 720-item ones of 2026-11-01. On the 648 items that remain, Sonnet 5.5 earns 0.1277, the
midpoint 0.1175, a difference of +0.0102 (SE 0.0085), still not significant, and IFS HRES 0.34
to 0.71 per variable and lead (`reports/era5/2026-11-01-claude-sonnet-5-5.md`).

## The question

People ask language models about the weather all the time. How good is a model's own
forecast when it is graded the way forecasters grade forecasts? I built an environment that
scores point forecasts against ERA5 by the WeatherBench 2 (WB2) rules, checked the grader
against WB2's published numbers first, and then ran Claude Sonnet 5.5 on it.

## The grader, checked before anything is scored

A grader that cannot reproduce a published score is not trusted with new ones. WB2 publishes
the global RMSE of the ECMWF IFS HRES forecast of mean sea level pressure against ERA5 at a
72 h lead, for the 2020 inits on its 64x32 grid: 133.890547 Pa. My numpy port gives the same
133.890547 Pa (a difference of 3.2e-8 Pa), and matches the published ACC (0.981878) and bias
(-0.406578 Pa) too (`reports/era5/2026-10-30-wb2-reproduction.md`, lines 11 to 13 and 26 to 27).

One detail decided the ACC. The published value pools the anomaly statistics over all inits
before it takes the ratio, as WeatherBench-X does, rather than averaging one correlation per
init as in the WB2 paper (same report, line 15). Reading the code that made the published
number, not only the paper, is what got the last digits right.

## The task

720 items (`environments/era5_forecast_v1/README.md`). Each is one cell of the 64x32 grid, one
variable (mean sea level pressure in Pa, or 2 m temperature in K), one 2020 init and one lead
of 24, 48 or 72 h, with 120 items for each variable and lead. The prompt gives the cell's ERA5
values every 6 hours over the 72 h before the init, and the ERA5 1990 to 2019 climatology at
the valid time. The reply ends with `ANSWER: <number>`.

## The reward: skill over the better free forecast

Two forecasts cost nothing: persistence (the value at the init) and climatology. With truth
y, persistence p, climatology c and forecast f, let b = min(|p - y|, |c - y|). The reward is
clip((b - |f - y|) / max(b, floor), 0, 1), so copying either free forecast earns 0 and a
perfect forecast earns 1. Each variable's floor is the 10th percentile of b over the items,
28.75 Pa and 0.069 K, so a near-perfect free forecast cannot blow up the ratio (decision 0007,
`reports/era5/items_v1_baselines.md`).

This reward is my own. The WB2 rules give the RMSE and ACC in the tables below as reference
metrics; they are not the reward.

## Results

Claude Sonnet 5.5 (`anthropic/claude-sonnet-5-5`, provider defaults, Batch API) answered all
720 items with a parseable line and no errors. Mean reward 0.116 (stderr 0.009). Area-weighted
RMSE and mean reward per variable and lead (`reports/era5/2026-11-01-claude-sonnet-5-5.md`):

| variable | lead h | persistence RMSE | climatology RMSE | IFS HRES RMSE | Sonnet 5.5 RMSE | HRES reward | Sonnet 5.5 reward |
|---|---|---|---|---|---|---|---|
| MSLP (Pa) | 24 | 539.3 | 609.9 | 50.5 | 487.5 | 0.594 | 0.147 |
| MSLP (Pa) | 48 | 754.2 | 614.8 | 76.9 | 586.0 | 0.666 | 0.109 |
| MSLP (Pa) | 72 | 967.3 | 726.1 | 139.4 | 738.1 | 0.570 | 0.091 |
| 2 m temperature (K) | 24 | 1.448 | 2.455 | 0.726 | 1.405 | 0.303 | 0.136 |
| 2 m temperature (K) | 48 | 2.591 | 2.660 | 0.760 | 2.198 | 0.490 | 0.126 |
| 2 m temperature (K) | 72 | 2.300 | 2.536 | 0.859 | 2.126 | 0.391 | 0.087 |

What the table says:

- A trivial statistical forecast does about as well. The midpoint of persistence and
  climatology earns a mean reward of 0.1074 against the model's 0.1161; item by item the
  model is ahead by +0.0087 (SE 0.0077), not significant at two standard errors, and a mixture
  weighted 0.67 toward persistence, fitted on a train split, does no better on the test split
  (`reports/era5/items_v1_baselines.md`). On this task the model shows no measurable skill
  over a trivial statistical forecast, so the environment has headroom.
- The model beats both free forecasts in RMSE everywhere except MSLP at 72 h, where it is a
  little worse than climatology (738.1 against 726.1 Pa).
- The margins are small. At 24 h its temperature RMSE is 1.405 K against persistence's
  1.448 K; IFS HRES is at 0.726 K. For pressure at 24 h, HRES's error is about a tenth of the
  model's (50.5 against 487.5 Pa).
- Its anomaly correlation follows persistence's closely: for MSLP 0.613, 0.357 and 0.147 at
  24, 48 and 72 h, against persistence's 0.643, 0.283 and 0.086 (same report).
- It never used extended thinking. Inspect sent adaptive thinking at the default effort, and
  the model chose not to think on any of the 720 items: 0 reasoning tokens, about 358 output
  tokens a reply (257,940 in all).

## Cost

$1.6126 for the 720 items through the Batch API at half price: 322,920 input and 257,940
output tokens at Anthropic's prices fetched on 2026-11-01 (`reports/spend.md`). A 12-item
probe, balanced over variable and lead, projected $1.55 to $1.64 before the run started.

## What this measures, and what it does not

- The model sees one cell's recent history and the climatology, nothing else: no neighbouring
  cells, no upper air, no satellite. A numerical model like HRES assimilates far more. So this
  measures reasoning from a local time series, not the best a model could do with tools.
- The reward's baseline is picked with the truth known, so items where persistence or
  climatology is nearly exact leave little to earn, and 3 temperature items cannot be won
  (`environments/era5_forecast_v1/README.md`).
- One reply per item, no seed: the run-to-run spread is not measured.
- The items are 2020 ERA5 values, which are public. Whether the model saw them in training is
  UNKNOWN.
- Whether thinking would help is not measured; a run at a set effort is the obvious next
  ablation.

## Reproduce

    uv run pytest tests/test_era5_reproduction.py   # the WB2 numbers (pinned subset)
    uv run python -m earthgym.era5.baselines            # the baseline rows
    uv run inspect eval src/earthgym/era5/tasks.py@era5_forecast \
        --model anthropic/claude-sonnet-5-5 --batch
    uv run python -m earthgym.era5.report <log dir> --out <report>.md

Sources: WeatherBench 2 (arXiv 2308.15560v2; JAMES 16(6) e2023MS004019, 2024, CC BY 4.0) and
its published results, as listed in `docs/radar.md`; ERA5 (Copernicus, CC BY 4.0); IFS HRES forecasts as served by WB2.
