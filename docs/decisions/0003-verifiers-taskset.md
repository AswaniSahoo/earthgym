# 0003: verifiers 0.4.0 v1 taskset for the RL environment

Date: 2026-10-30. Status: accepted.

Status note, 2026-11-19: the `env` group holds `climaqa-v1`, `era5-forecast-v1` and
`verifiers==0.4.0` (`pyproject.toml:22-26`). All four packages are editable workspace members
(`pyproject.toml:50-62`), and the `eval` group lists all four (`pyproject.toml:32-39`). Each reward
is an async `@vf.reward` method of the task class that calls plain functions in the package's
`contract.py` (for example `environments/heat_basis_v1/heat_basis_v1/taskset.py:27-29`), and the
tests call those functions directly (`tests/test_contract.py`, `tests/test_*_contract.py`).

Context: the environments in this repo are meant for RL training and the Prime Intellect Hub.
verifiers 0.4.0 (2026-10-12) replaced its old API with `verifiers.v1` tasksets.

Decision: one self-contained package per environment under `environments/`, scaffolded with
`vf-init`, depending on `verifiers>=0.4.0,<0.5`; the repo installs it editable in the `env`
dependency group, pinned to `verifiers==0.4.0`. Rewards are plain functions so tests call them
directly. The package bundles its data so it runs offline and can be pushed to the Hub.

Consequences: `vf-eval` defaults to Prime's cloud and uploads runs; local runs pass `--no-push`
and point `client.base_url` at a local or chosen server.

Harness (2026-11-02, decision 0023): a taskset that exports no harness runs on verifiers'
`bash` harness, which gives the model a shell. Each package exports `NullHarness`, so the
default runs no model-written code.
