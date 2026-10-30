# rlenv

Verifiable evals and RL environments for climate and earth science, built phase by phase.

A benchmark is an exam paper. Before anyone is graded on it, someone checks the answer key, the
wording, and that no exam question leaked into the study material. Phase 1 does that check for
ClimaQA. Later phases write new papers (environments) whose answers a program can grade exactly.

## Phases

| Phase | What | Status |
|---|---|---|
| 1 | ClimaQA audit: integrity checks, paper cross-check, human hand-check sample | in progress |
| 2 | Clean ClimaQA port (Inspect task, verifiers environment) | next |
| 3 | ERA5 forecast-score environment, graded against weatherbench2 | planned |
| 4 | IBTrACS cyclone analytics environment | planned |
| 5 | Heat-insurance basis-risk environment | planned |

## Run

    uv sync
    uv run python -m rlenv.climaqa.audit   # downloads the pinned CSVs to data/, writes reports/climaqa/
    uv run pytest

## Layout

    src/rlenv/climaqa/data.py     pinned download (revision + sha256) and CSV loading
    src/rlenv/climaqa/checks.py   pure integrity checks: rows in, findings out
    src/rlenv/climaqa/audit.py    runs the checks, writes findings.json, SUMMARY.md, review_sample.csv
    tests/                        unit tests on small inline fixtures, no network
    reviews/                      one review per phase: rating, gaps, decisions

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
