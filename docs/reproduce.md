# Reproduce earthgym

One path in three parts, in order: rebuild the data from its pinned sources and run the
reproductions of published references on it, recompute the published numbers of the model runs
from the committed per-item results and the ERA5 baselines from the bundled items, and run fresh
evals. Part 2 needs no
download and no API key; part 3 is the only part that calls a model and spends money. Run every
command from the repo root.

Every command below was run from a fresh clone on 2026-11-02, with three differences. The
downloads of part 1 that are not small, `earthgym.era5.data`, `earthgym.era5.items` and the IBTrACS
release asset, ran on a fresh CI runner (the `reproduce` workflow, run 41355534694, uv 0.13.6);
the local clone used uv 0.12.18, and its IBTrACS and GHCN-Daily fetches checked copies of the
pinned files by hash. uv's installer ran once, into a scratch directory. Part 3 ran with
Inspect's mock model only, so without a model call. Two commands were added on 2026-11-19,
`earthgym.climaqa.audit` and `earthgym.era5.baselines`, and checked in a working copy at commit
f784dfc rather than a fresh clone: the baselines rewrote their report byte for byte, and the audit,
run into an empty directory, wrote its four files byte for byte as committed. The ERA5, IBTrACS and
heat data steps of part 1 run again every Monday in CI (`.github/workflows/reproduce.yml`, jobs
`era5`, `ibtracs` and `heat`); the two ClimaQA steps do not run there. The GHCN-Daily step no
longer works for a
stranger: NCEI rewrites its station files, and by 2026-11-02 it served another build of USW00023183,
so the pin refuses it and CI warns (decision 0018).

## Set up

    curl -LsSf https://astral.sh/uv/install.sh | sh      # uv's standalone installer
    git clone https://github.com/AswaniSahoo/earthgym.git
    cd earthgym
    uv python install 3.12            # the version in .python-version
    uv sync --locked --all-groups     # the exact versions in uv.lock; fails if the lock is stale
    uv run pytest -q                  # the tests that need pinned data skip until part 1

## 1. Rebuild the data

Each fetch keeps a file only if its sha256 is the pinned one, and each build writes its bundled
items and manifest byte for byte, so `git status` shows no change at the end.

    uv run python -m earthgym.climaqa.clean   # ClimaQA at its pinned revision, from Hugging Face
    uv run python -m earthgym.climaqa.audit   # rewrites findings.json and SUMMARY.md
    uv run python -m earthgym.era5.data       # the six WeatherBench 2 subsets, about 108 MB written
    uv run python -m earthgym.era5.items      # about 56 MB of WB2 store chunks; checks fields_sha256
    uv run python -m earthgym.ibtracs.data    # IBTrACS, 57.6 MB: the data-v1 release, else NCEI
    uv run python -m earthgym.ibtracs.items
    uv run python -m earthgym.heat.data       # four GHCN-Daily station files, about 2.9 MB, from NCEI
    uv run python -m earthgym.heat.items
    git status --short                     # prints nothing
    uv run pytest -q                       # now also the WB2, NCEI and NWS reproductions

The audit writes its two review sheets, `reports/climaqa/review_sample.csv` and `leak_review.csv`,
only when they are missing, so a re-run never erases a verdict
(`src/earthgym/climaqa/audit.py:76-77,189-192`). To check them, delete them first.

Two limits (decision 0018):

- The `data-v1` release asset needs no account since the repository went public on 2026-11-13
  (decision 0027). The `reproduce` workflow fetches it with `curl` and no token; run 43520032748
  (2026-11-13, commit f5be006) passed all three jobs that way. `earthgym.ibtracs.data` tries it first and falls back to NCEI, which passes the
  hash check only while it still serves the pinned bytes.
- The GHCN-Daily station files come from NCEI alone. Once NCEI serves another build, the hash
  check refuses it and heat-basis-v1 cannot be rebuilt; parts 2 and 3 do not need the files.

## 2. Recompute the published numbers

    uv run pytest -q tests/test_published_numbers.py
    uv run python -m earthgym.era5.baselines   # reports/era5/items_v1_baselines.md
    git status --short                         # prints nothing

`reports/<env>/results/*.jsonl` holds, for every reported run and every probe, one line for the
run (model, settings, tokens, the sha256 of the items it was scored on) and one line per item
(id, parsed answer, reward, tokens), described in decision 0019. The test builds every report
and its JSON from these files alone, with the same code that builds them from the logs, and
compares them byte for byte with the committed ones: the two ClimaQA run reports and their
comparison, ERA5, the three IBTrACS runs (rules shown, rules hidden and tools-react) with their
pair and three-run reports, both heat runs and their pair, the four small-model reports
(decisions 0022 and 0025), and the Jev third-reader report (decision 0008), whose results file
holds one line per Jev call, with its bucket choice and probabilities and no reward. The three
GRPO reports re-render from their metrics files in `reports/grpo/results/` (decision 0024). It
also checks every row of `reports/spend.md` against the tokens in the results, the GRPO run's
choice of task (decision 0024), the heat missing-value counts the Phase 5 write-up gives, and
decision 0010's projection from the Gemini ERA5 probe. `earthgym.era5.baselines` needs no results
file: it scores the baselines on the bundled items, with no model run.

One number by hand, the heat accuracy with the rules shown:

    uv run python -c "from pathlib import Path; from earthgym import results; \
    head, rows = results.read(Path('reports/heat/results/2026-11-01-claude-sonnet-5-5.jsonl')); \
    print(head['model'], sum(r['reward'] for r in rows) / len(rows))"

prints `anthropic/claude-sonnet-5-5 0.9866666666666667`, the 0.987 in
`reports/heat/2026-11-01-claude-sonnet-5-5.md`.

## 3. Run fresh evals

Put `ANTHROPIC_API_KEY` in `.env` at the repo root; the Inspect CLI loads it (decision 0010).
The published Claude Sonnet 5.5 runs went through the Batch API, and their logs record these
settings: `batch 100` for every run, and `cache_prompt false` as well for the heat runs
(decision 0010 explains the cache setting). The eight runs and their eight probes, one run stopped
at 225 of 300 items, cost $12.2793 in total (`reports/spend.md`). Each was preceded by a probe that
projected its cost; the probe's items come from `uv run python -m earthgym.era5.tasks` (likewise
`earthgym.ibtracs.tasks` and `earthgym.heat.tasks`), passed as `--sample-id "$(...)"`. ClimaQA's
probe has no such helper: it took 8 items of each task with `--limit 8 --sample-shuffle 2026`, as
its logs record (`logs/` is not committed), and on 2026-11-19 those flags with the mock model
picked the same 16 ids as `reports/climaqa/results/2026-11-01-climaqa-claude-sonnet-5-5-probe-*`.

    M=anthropic/claude-sonnet-5-5
    uv run inspect eval src/earthgym/climaqa/tasks.py@climaqa_mcq \
        src/earthgym/climaqa/tasks.py@climaqa_cloze --model $M --batch --log-dir logs/climaqa-run
    uv run inspect eval src/earthgym/era5/tasks.py@era5_forecast --model $M --batch \
        --log-dir logs/era5-run
    uv run inspect eval src/earthgym/ibtracs/tasks.py@ibtracs_storm --model $M --batch \
        --log-dir logs/ibtracs-run                     # add -T rules=false for the ablation
    uv run inspect eval src/earthgym/ibtracs/tasks.py@ibtracs_storm --model $M --batch \
        -T tools=true --log-dir logs/ibtracs-tools-run  # the rows behind a query tool
    uv run inspect eval src/earthgym/heat/tasks.py@heat_basis --model $M --batch \
        --cache-prompt false --log-dir logs/heat-run   # add -T rules=false for terms only

Then, for each run, its report, its per-item results and its ledger row, here for heat:

    uv run python -m earthgym.heat.report logs/heat-run --out reports/heat/<name>.md
    uv run python -m earthgym.results heat logs/heat-run <name>
    uv run python -m earthgym.spend "<run>" logs/heat-run

The other reports: `earthgym.climaqa.report <log dir> --out reports/climaqa/runs/<name>.md` and
`earthgym.climaqa.compare <log dir a> <log dir b> --out <name>.md`, `earthgym.era5.report`, and
`earthgym.ibtracs.report`, whose `--hidden <log dir>` (heat's too) writes the pair report, and
with `--tools <log dir>` as well the three-run report (decision 0023); the committed one also
names a second difference between the runs, `--also "react's system prompt and submit tool, which
the prompt run did not have (decision 0023)"` (`tests/test_published_numbers.py:65-68`). ClimaQA's
strict variant is `-T strict=true` on both tasks. The held-out split is an option of the
verifiers tasksets only (decision 0017).

To try the commands without a key or any spend, use Inspect's mock model, `--model
mockllm/model --limit 3`; `earthgym.spend` refuses a mock log, since it has no price for it.

## The small models and the GRPO run, on Kaggle

These ran on private Kaggle kernels, not from a fresh clone, and need a Kaggle account (decisions
0024 and 0025). The small-model runs, from a bundle of the commit in a private dataset:

    uv run python -m earthgym.kaggle.samples_kernel source <folder> --user <kaggle user>
    kaggle datasets create -p <folder>
    uv run python -m earthgym.kaggle.samples_kernel kernel <kernel folder> --user <kaggle user> \
        --commit <the bundle's commit>
    kaggle kernels push -p <kernel folder> -t 43200
    kaggle kernels output <kaggle user>/earthgym-small-models -p <dir>
    uv run python -m earthgym.results heat <dir>/logs/<log dir> <name>   # --partial for a stopped run
    uv run python -m earthgym.samples heat <results files> --out reports/heat/<date>-small-models.md

The first session used the default plan. Sessions 2 and 3 added `--plan qwen-rest` to the kernel
command, which runs Qwen3.5-2B's heat and its ERA5 in two parts over both GPUs (decision 0025,
`src/earthgym/kaggle/samples_kernel.py:118-147`). A session that stops at its deadline resumes
when the next one mounts its logs: `--resume` on the kernel, with the logs as `logs.tar.gz` in the
`earthgym-small-models-logs` dataset. The GRPO run's
commands are in `reports/grpo/2026-11-02-phase-7-writeup.md`.
