# 0002: Inspect runs the ClimaQA tasks and the baselines

Date: 2026-10-30. Status: accepted; scoring superseded by 0004.

Status note, 2026-11-19: the tasks use Inspect's plain `generate()` solver and a custom scorer
over the contract (`src/earthgym/climaqa/tasks.py:38-58`), not `multiple_choice()` and
`choice()`, and the options are shuffled once at build time, per item id with seed 20261030
(`src/earthgym/climaqa/clean.py:19,58`), not at load time. Decision 0004 records the scorer and
the shuffle.

Context: Phase 2 needs the clean set run against several models with reproducible logs, and a
route to the inspect_evals Register, which asks for an Inspect task and logs from two models.

Decision: `inspect-ai==0.3.286`, pinned, in the `eval` dependency group so the audit stays
standard-library only. Its built-in `multiple_choice()` solver and `choice()` scorer handle MCQ,
with choices shuffled at load time by a fixed seed; `exact()` scores cloze, reported as
accuracy and stderr like the MCQ task. No custom scorer code.

Consequences: Inspect releases every few days, so the pin moves only on purpose. Tests run the
tasks end to end on `mockllm/model`, offline, in CI.
