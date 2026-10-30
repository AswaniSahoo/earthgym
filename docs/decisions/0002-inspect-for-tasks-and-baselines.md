# 0002: Inspect runs the ClimaQA tasks and the baselines

Date: 2026-10-30. Status: accepted.

Context: Phase 2 needs the clean set run against several models with reproducible logs, and a
route to the inspect_evals Register, which asks for an Inspect task and logs from two models.

Decision: `inspect-ai==0.3.286`, pinned, in the `eval` dependency group so the audit stays
standard-library only. Its built-in `multiple_choice()` solver and `choice()` scorer handle MCQ,
with choices shuffled at load time by a fixed seed; `exact()` scores cloze, reported as
accuracy and stderr like the MCQ task. No custom scorer code.

Consequences: Inspect releases every few days, so the pin moves only on purpose. Tests run the
tasks end to end on `mockllm/model`, offline, in CI.
