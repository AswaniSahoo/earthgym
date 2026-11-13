# earthgym

RL environments and evals for weather and climate whose rewards a program can check: the forecast,
cyclone and heat graders reproduce published numbers before they pay a reward.

| environment | the model must | reward | trivial baseline | Claude Sonnet 5.5 | Qwen3.5-2B | Granite 4.0 H-1B |
|---|---|---|---|---|---|---|
| [`era5-forecast-v1`](environments/era5_forecast_v1/README.md), 648 items | forecast ERA5 pressure or temperature 24 to 72 h ahead from one grid cell's history | skill over persistence and climatology, from 0 to 1 | 0.118, the midpoint of persistence and climatology | 0.128 | 0.029 | 0.042 |
| [`ibtracs-storm-v1`](environments/ibtracs_storm_v1/README.md), 300 | compute a storm's ACE, peak category or hours at hurricane strength from its track rows | exact answer | 0.05 to 0.35 per question, the best constant answer | 0.997 with the rules shown (saturated), 0.703 hidden | 0.370 | 0.032 |
| [`heat-basis-v1`](environments/heat_basis_v1/README.md), 300 | count a heat policy's trigger days, payout events or missed days from station data | exact answer | 0.05 to 0.27 per question, the best constant answer | 0.987 with the rules shown (saturated), 0.960 with the terms only | 0.217 | 0.028 |
| [`climaqa-v1`](environments/climaqa_v1/README.md), 350 | answer ClimaQA multiple choice and cloze questions, exact-overlap leaks removed | exact match | 0.25 on multiple choice, by chance | 0.874 multiple choice, 0.508 cloze | 0.710 multiple choice, 0.145 cloze | 0.584 multiple choice, 0.020 cloze |

The small models answered each item 8 times with the rules shown, and their columns give the mean
reward. Saturated means a strong model gets nearly every item right, so a policy that strong gets
almost no signal: those versions stay as controls for the ablations and for small models.
[`SUMMARY.md`](SUMMARY.md) gives the detail behind every row, phase by phase.

## Findings

1. A train/test leak in ClimaQA (ICLR 2025). 43 validated Gold test questions appear word for word
   in Silver, the set the paper fine-tunes on: 29 with the same answer, 14 with a different one. 6
   more appear in another Silver task. These are exact matches, so they are a lower bound
   ([`reports/climaqa/SUMMARY.md`](reports/climaqa/SUMMARY.md)).
2. A frontier model ties a trivial forecast. On ERA5, Claude Sonnet 5.5 earns 0.1277 and the
   midpoint of persistence and climatology 0.1175: a difference of +0.0102 (SE 0.0085), not
   significant. IFS HRES earns 0.5555, so the environment has headroom
   ([model](reports/era5/2026-11-01-claude-sonnet-5-5.md),
   [baselines](reports/era5/items_v1_baselines.md)).
3. The graders match published references. The forecast grader reproduces WeatherBench 2's IFS HRES
   MSLP 72 h RMSE, 133.890547 Pa, to within 3.2e-8 Pa
   ([report](reports/era5/2026-10-30-wb2-reproduction.md)), and all 18 of its published global RMSE,
   ACC and bias values for MSLP and 2 m temperature at 24, 48 and 72 h to float32 precision
   ([report](reports/era5/2026-11-13-wb2-reproduction-leads-and-t2m.md)). The cyclone grader
   reproduces NOAA NCEI's North Atlantic figures, among them 1933's ACE of 258.6 and 2024's of 161.6
   ([report](reports/ibtracs/2026-11-01-ncei-reproduction.md)). The heat grader reproduces NWS
   Phoenix's counts: 55 days at 110 F or more in 2023 and a 31-day run
   ([report](reports/heat/2026-11-01-nws-phoenix-reproduction.md)).

A small GRPO run of Qwen3.5-2B on ClimaQA's multiple choice items learned the train items with no
measurable transfer: train items went from 0.712 to 0.844, held-out items from 0.750 to 0.774, with
both samplings under one stop set. One seed
([write-up](reports/grpo/2026-11-02-phase-7-writeup.md)).

## Not finished

- My review. I have not yet confirmed the decision records or done the hand checks, so read them as
  drafted ([`docs/how-built.md`](docs/how-built.md), [sheets](docs/human-checks/README.md)).
- The expert review of ClimaQA's cloze items: no expert has it yet (decision 0005).
- Tools mode for `ibtracs-storm-v1`. Its Sonnet run stopped at 225 of 300 items when the API's
  credit ran out, so it has no reported result. The numbers from a first version carry a caveat
  ([write-up](reports/ibtracs/2026-11-02-phase-6-writeup.md)).

## Quick start

With [uv](https://docs.astral.sh/uv/) and Python 3.12:

    uv sync --locked --all-groups
    uv run pytest -q tests/test_published_numbers.py   # every published number, from committed results
    uv run inspect eval src/earthgym/heat/tasks.py@heat_basis --model mockllm/model --limit 3

Each package in `environments/` is a verifiers v1 taskset with its data inside. Each has an Inspect
task beside it in `src/earthgym/`, scored by the same contract module. Verifiers defaults to its
null harness here, which runs no code the model writes; its own default, `bash`, would give the
model a shell on the host. [`docs/reproduce.md`](docs/reproduce.md) rebuilds the data, recomputes
every number and runs fresh evals.

## Where things are

- [`SUMMARY.md`](SUMMARY.md): what each phase found, and what it means for RL.
- [`reports/`](reports/): results, per-item files and write-ups.
  [`reports/spend.md`](reports/spend.md) is the ledger of paid runs.
- [`docs/decisions/`](docs/decisions/): why I chose what I chose, in [plain
  words](docs/human-checks/decisions.md) too.
- [`docs/reviews/`](docs/reviews/): one review per phase, written by an AI agent (Claude Fable 5.1,
  and 5.2 from 2026-11-13), not by a person.
- [`docs/how-built.md`](docs/how-built.md): built with Claude Code under my direction, and who
  decided what.
- [`docs/roadmap.md`](docs/roadmap.md), [`docs/log.md`](docs/log.md),
  [`docs/radar.md`](docs/radar.md): what is next, what changed, and which tools I watch.

## License

MIT, copyright 2026 Aswani Kumar Sahoo: see [`LICENSE`](LICENSE). It covers the code in this repo
and in the environment packages. The data they and the reports carry keep their sources' terms:
ClimaQA under Apache-2.0, ERA5 under CC BY 4.0, IBTrACS with "full and open access" and WMO
Resolution 40 for commercial use, and GHCN-Daily, for which NCEI's own pages name no licence
(decision 0027).
[`NOTICE`](NOTICE) says which files carry what, and each package's own `NOTICE` gives the
attribution; `docs/radar.md` and decisions 0008 and 0012 give the sources.
