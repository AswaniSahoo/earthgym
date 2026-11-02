# 0003: verifiers 0.4.0 v1 taskset for the RL environment

Date: 2026-10-30. Status: accepted.

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
