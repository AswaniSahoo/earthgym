# rlenv

Verifiable evals and RL environments for climate and earth science, built phase by phase.

A benchmark is an exam paper. Before anyone is graded on it, someone checks the answer key, the
wording, and that no exam question leaked into the study material. Phase 1 does that check for
ClimaQA. Later phases write new papers (environments) whose answers a program can grade exactly.

## Phases

| Phase | What | Status |
|---|---|---|
| 1 | ClimaQA audit: integrity checks, paper cross-check, human hand-check sample | done; hand-checks wait |
| 2 | Clean ClimaQA port (Inspect task, verifiers environment), Gemini 3.8 Flash baseline | done; v2 waits on the expert review (0005); the Jev third-reader study is built and parked (no key) |
| 3 | ERA5 forecast-score environment, graded against weatherbench2 | done; Claude Sonnet 5.5 earns a mean reward of 0.116, IFS HRES 0.30 to 0.67 per cell (`reports/era5/2026-11-01-claude-sonnet-5-5.md`) |
| 4 | IBTrACS cyclone analytics environment | done: `ibtracs-storm-v1`, 300 per-storm questions with exact answers. With the rules in the prompt (the control) Sonnet 5.5 scores 0.997; with them hidden 0.703, where ACE and peak category stay at 0.99 and hours become a convention test (`reports/ibtracs/2026-11-01-rules-shown-vs-hidden.md`) |
| 5 | Heat-insurance basis-risk environment | done: `heat-basis-v1`, 300 policy questions over Phoenix-area stations, after reproducing NWS Phoenix's heat counts. With the rules shown (the control) Sonnet 5.5 scores 0.987; with the policy terms alone 0.960, where missed days fall to 0.89 on how a missing index value is read (`reports/heat/2026-11-01-rules-shown-vs-terms-only.md`) |

Every model run uses Claude Sonnet 5.5 on the Anthropic key, with $20 in total as a hard cap;
the spend is in `reports/spend.md` (decision 0010). No Vertex AI or Gemini calls are made from
2026-11-01; the earlier Gemini results stay as recorded.

## Environments

| package | phase | what an item asks | reward |
|---|---|---|---|
| `climaqa-v1` | 2 | a clean ClimaQA question, multiple choice or cloze | exact match |
| `era5-forecast-v1` | 3 | a 24 to 72 h point forecast of ERA5 pressure or temperature | skill over persistence and climatology, graded by the WB2 rules |
| `ibtracs-storm-v1` | 4 | a storm's ACE, peak category or hours at hurricane strength | exact answer |
| `heat-basis-v1` | 5 | a heat policy's trigger days, payout events or missed days | exact answer |

Each package is a verifiers v1 taskset; each has an Inspect task beside it in `src/rlenv/`, scored
by the same contract module.

## Run

    uv sync --all-groups
    uv run pytest                                  # no network; the reproduction tests skip without data
    uv run python -m rlenv.climaqa.audit           # Phase 1: pinned CSVs to data/, reports/climaqa/
    uv run python -m rlenv.era5.baselines          # Phase 3: baseline rows
    uv run python -m rlenv.ibtracs.data            # Phase 4: the pinned 57.6 MB IBTrACS CSV
    uv run python -m rlenv.heat.data               # Phase 5: the pinned GHCN-Daily station files

A model run (the key in `.env` as `ANTHROPIC_API_KEY`; decision 0010):

    uv run inspect eval src/rlenv/ibtracs/tasks.py@ibtracs_storm \
        --model anthropic/claude-sonnet-5-5 --batch --cache-prompt false [-T rules=false]
    uv run python -m rlenv.spend "<run>" <log dir> # adds the run to reports/spend.md

## Layout

    src/rlenv/climaqa/    Phases 1 and 2: audit, clean set, Inspect tasks, reports, comparison
    src/rlenv/era5/       Phase 3: WB2 scoring rules, items, baselines, Inspect task, report
    src/rlenv/ibtracs/    Phase 4: pinned IBTrACS, NOAA counts, items, Inspect task, report
    src/rlenv/heat/       Phase 5: pinned GHCN-Daily, NWS counts, policy rules, items, task, report
    src/rlenv/spend.py    the Anthropic spend ledger and its checks
    src/rlenv/ablation.py the rules-shown run beside its ablation
    environments/         one verifiers environment package per phase
    tests/                unit tests on small inline fixtures, no network
    reports/              results per phase, the blog-ready write-ups, spend.md
    reviews/              one Fable review per phase
    docs/radar.md         what is new and proven; docs/decisions/ records each choice

## Phase 1 checks

Defects (the item is broken): option labels other than a) to d), a key that is not an option, empty
or identical options, a cloze item with no `<MASK>`, an empty cloze answer, and a Gold question that
also appears in Silver. Silver is the set the paper fine-tunes on (arXiv 2410.16701v2, A.3.2), so
an overlap is a train/test leak.

Flags (a human decides): the keyed option repeated in the question, a cloze answer repeated outside
the blank, several masks for one answer, "all/none of the above" options, and repeated questions
within a split (noting when the keyed answer text differs).

The Gold MCQ and freeform files also keep the expert-rejected items (`Validation=False`: 47 MCQ,
20 freeform). The authors' evaluation notebooks keep only `Validation=True`, which matches the
paper's counts; any other loader has to filter the same way.

## Hand-check

`reports/climaqa/review_sample.csv` holds 10 validated Gold MCQ items per complexity level
(seed 20261030). Fill `verdict` with one of: ok, wrong_key, ambiguous, multiple_correct,
out_of_scope, and say why in `note`.

## License

MIT, copyright 2026 Aswani Kumar Sahoo: see `LICENSE`. The license covers the code in this repo
and in the environment packages. The data the packages and reports carry keep their sources'
terms: ClimaQA under Apache-2.0, ERA5 under CC BY 4.0, IBTrACS with "full and open access" and
WMO Resolution 40 for commercial use, and GHCN-Daily, for which NOAA names no licence
(`docs/radar.md`, decisions 0008 and 0012).
