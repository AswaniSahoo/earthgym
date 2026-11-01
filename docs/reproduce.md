# Reproduce rlenv

One path in three parts, in order: rebuild the data from its pinned sources, recompute every
published number from the committed per-item results, and run fresh evals. Part 2 needs no
download and no API key; part 3 is the only part that calls a model and spends money. Run every
command from the repo root.

Every command below was run from a fresh clone on 2026-11-02, with three differences. The
downloads of part 1 that are not small, `rlenv.era5.data`, `rlenv.era5.items` and the IBTrACS
release asset, ran on a fresh CI runner (the `reproduce` workflow, run 41355534694, uv 0.13.6);
the local clone used uv 0.12.18, and its IBTrACS and GHCN-Daily fetches checked copies of the
pinned files by hash. uv's installer ran once, into a scratch directory. Part 3 ran with
Inspect's mock model only, so without a model call. The data steps of part 1 run again every
Monday in CI (`.github/workflows/reproduce.yml`).

## Set up

    curl -LsSf https://astral.sh/uv/install.sh | sh      # uv's standalone installer
    git clone https://github.com/AswaniSahoo/rlenv.git   # private for now: needs access
    cd rlenv
    uv python install 3.12            # the version in .python-version
    uv sync --locked --all-groups     # the exact versions in uv.lock; fails if the lock is stale
    uv run pytest -q                  # the tests that need pinned data skip until part 1

## 1. Rebuild the data

Each fetch keeps a file only if its sha256 is the pinned one, and each build writes its bundled
items and manifest byte for byte, so `git status` shows no change at the end.

    uv run python -m rlenv.climaqa.clean   # ClimaQA at its pinned revision, from Hugging Face
    uv run python -m rlenv.era5.data       # the WeatherBench 2 subset, about 18 MB
    uv run python -m rlenv.era5.items      # about 56 MB of WB2 store chunks; checks fields_sha256
    uv run python -m rlenv.ibtracs.data    # IBTrACS, 57.6 MB: the data-v1 release, else NCEI
    uv run python -m rlenv.ibtracs.items
    uv run python -m rlenv.heat.data       # four GHCN-Daily station files, about 2.9 MB, from NCEI
    uv run python -m rlenv.heat.items
    git status --short                     # prints nothing
    uv run pytest -q                       # now also the WB2, NCEI and NWS reproductions

Two limits (decision 0018):

- While the repository is private, the `data-v1` release asset needs access to it, and
  `rlenv.ibtracs.data` falls back to NCEI, which passes the hash check only while it still
  serves the pinned bytes. With access, fetch the asset first:
  `gh release download data-v1 -p ibtracs.NA.list.v04r01.csv -D data/ibtracs`.
- The GHCN-Daily station files come from NCEI alone. Once NCEI serves another build, the hash
  check refuses it and heat-basis-v1 cannot be rebuilt; parts 2 and 3 do not need the files.

## 2. Recompute the published numbers

    uv run pytest -q tests/test_published_numbers.py

`reports/<env>/results/*.jsonl` holds, for every reported run and every probe, one line for the
run (model, settings, tokens, the sha256 of the items it was scored on) and one line per item
(id, parsed answer, reward, tokens), described in decision 0019. The test builds every report
and its JSON from these files alone, with the same code that builds them from the logs, and
compares them byte for byte with the committed ones: the two ClimaQA run reports and their
comparison, ERA5, both IBTrACS runs and their pair, and both heat runs and their pair. It also
checks every row of `reports/spend.md` against the tokens in the results.

One number by hand, the heat accuracy with the rules shown:

    uv run python -c "from pathlib import Path; from rlenv import results; \
    head, rows = results.read(Path('reports/heat/results/2026-11-01-claude-sonnet-5-5.jsonl')); \
    print(head['model'], sum(r['reward'] for r in rows) / len(rows))"

prints `anthropic/claude-sonnet-5-5 0.9866666666666667`, the 0.987 in
`reports/heat/2026-11-01-claude-sonnet-5-5.md`.

## 3. Run fresh evals

Put `ANTHROPIC_API_KEY` in `.env` at the repo root; the Inspect CLI loads it (decision 0010).
The published Claude Sonnet 5.5 runs went through the Batch API, and their logs record these
settings: `batch 100` for every run, and `cache_prompt false` as well for the heat runs
(decision 0010 explains the cache setting). The six full runs cost $9.1298 in total
(`reports/spend.md`). Each was preceded by a probe that projected its cost; the probe's items
come from `uv run python -m rlenv.era5.tasks` (likewise `rlenv.ibtracs.tasks` and
`rlenv.heat.tasks`), passed as `--sample-id "$(...)"`.

    M=anthropic/claude-sonnet-5-5
    uv run inspect eval src/rlenv/climaqa/tasks.py@climaqa_mcq \
        src/rlenv/climaqa/tasks.py@climaqa_cloze --model $M --batch --log-dir logs/climaqa-run
    uv run inspect eval src/rlenv/era5/tasks.py@era5_forecast --model $M --batch \
        --log-dir logs/era5-run
    uv run inspect eval src/rlenv/ibtracs/tasks.py@ibtracs_storm --model $M --batch \
        --log-dir logs/ibtracs-run                     # add -T rules=false for the ablation
    uv run inspect eval src/rlenv/heat/tasks.py@heat_basis --model $M --batch \
        --cache-prompt false --log-dir logs/heat-run   # add -T rules=false for terms only

Then, for each run, its report, its per-item results and its ledger row, here for heat:

    uv run python -m rlenv.heat.report logs/heat-run --out reports/heat/<name>.md
    uv run python -m rlenv.results heat logs/heat-run <name>
    uv run python -m rlenv.spend "<run>" logs/heat-run

The other reports: `rlenv.climaqa.report <log dir> --out reports/climaqa/runs/<name>.md` and
`rlenv.climaqa.compare <log dir a> <log dir b> --out <name>.md`, `rlenv.era5.report`, and
`rlenv.ibtracs.report`, whose `--hidden <log dir>` (heat's too) writes the pair report. ClimaQA's
strict variant is `-T strict=true` on both tasks. The held-out split is an option of the
verifiers tasksets only (decision 0017).

To try the commands without a key or any spend, use Inspect's mock model, `--model
mockllm/model --limit 3`; `rlenv.spend` refuses a mock log, since it has no price for it.
