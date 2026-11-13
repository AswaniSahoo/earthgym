# Draft: registering ClimaQA in the inspect_evals Register

Not submitted. Requirements read on 2026-11-02 from UKGovernmentBEIS/inspect_evals at
`969e4b2` (`.github/ISSUE_TEMPLATE/register-submission.yml`, `register/README.md`,
`EVALUATION_CHECKLIST.md`).

## What the Register asks

- One issue per task: "If your repo contains multiple tasks, submit a separate issue for each
  one." So two issues, `climaqa_mcq` and `climaqa_cloze`.
- Form fields: an arXiv URL and a source URL (both required), and maintainers (optional).
- The arXiv URL "must point to the paper your eval implements", which "may be the one that
  originally introduced the benchmark, or a separate paper describing the replication". For
  ClimaQA that is https://arxiv.org/abs/2410.16701. A submission is checked by a model for
  correspondence with the paper; one listed failure is "The LLM determined the eval doesn't match
  the paper (correspondence check)".
- The source URL "must point to a specific commit (40-char SHA)"; "tags and branches aren't
  accepted". "The upstream repository must be public", and the submitter needs "at least one
  commit in the repo".
- The repository needs a `pyproject.toml` with `[project]` and `inspect_ai` as a dependency, an
  `@task`, and pinned assets ("explicit `revision=`").
- Logs: "upload the log files of two models doing an evaluation run of all the samples to our
  log store", through https://logfile-upload.generality.workers.dev/ ("2 full evaluation log
  files"), and "These logs may be made public".

## How earthgym meets it

| requirement | earthgym |
|---|---|
| public repository | yes, since 2026-11-13 (decision 0027) |
| a paper | arXiv 2410.16701 (ClimaQA, ICLR 2025) |
| `@task` at a pinned commit | `src/earthgym/climaqa/tasks.py`, `climaqa_mcq` and `climaqa_cloze`, at the release commit's 40-character SHA |
| pinned assets | the clean set is bundled in `climaqa-v1`; the source dataset is pinned at revision `3f084a0202c6260e588fb5b681d2e4ec859a3845` |
| logs of two models over every sample | Gemini 3.8 Flash (2026-10-30) and Claude Sonnet 5.5 (2026-11-01), both over all 350 items of clean set v1 (`reports/climaqa/2026-11-01-sonnet-vs-gemini.md`) |

## What to say in each issue

- The task is ClimaQA's Gold set as the authors evaluate it (`Validation` True), with the items
  found verbatim in Silver and the defective items removed: clean set v1, exact-overlap-filtered,
  with 21 near matches unresolved and a strict variant (`-T strict=true`) without them. That is
  where it differs from the paper, and the correspondence check should hear it from us first.
- Cloze is scored by exact match after normalization, which the checklist calls "a weak proxy";
  say so, with decision 0005's reasons.

## Open points

- ERA5, IBTrACS and heat have no paper, so they cannot be registered as they stand. The schema
  allows `arxiv: None`, but whether a maintainer accepts that is UNKNOWN.
- Any size or format limit on the uploaded logs is UNKNOWN; the README names only "`.eval`
  logs".
