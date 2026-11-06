# How this was built

I built this repository with Claude Code, Anthropic's coding agent, as a pair programmer under my
direction, from 2026-10-30. The git history shows the work as it happened, corrections included.

## Who did what

Claude Code wrote the code and the tests, ran the pipelines and the model runs, and drafted the
reports and the decision records. It worked in phases with a fixed loop, written down in
`CLAUDE.md`: a radar of current tools checked at the source, a plan, test-first code, a dated
report, and a review before the phase closed.

These calls I made myself:

- One paid model within a $20 budget, and no Vertex AI or Gemini calls (decision 0010).
- Small open models at no API cost (decision 0022), and all GPU work on Kaggle (decision 0025).
- The MIT License (decision 0015), the name earthgym (decision 0020), and keeping the repository
  private until the work is done.

Claude Code proposed the other design choices and technical details, for example the ERA5 reward and
its floor (decision 0007), no judge model for ClimaQA's cloze answers (decision 0005), ACE at one
decimal (decision 0011), the item draws and the careless-reading baselines. Some were set during
runs I was not watching. The decision records are written in my voice, and where a record shows a
choice was not mine at the time, it says so (the floor, in `docs/log.md`, 2026-10-30).

My review of this work is in progress, so read those records as drafted, not as confirmed. As of
2026-11-06, in the sheets of `docs/human-checks/`, I have answered 0 of the 25 decision records and
checked 0 of the 30 ClimaQA items and 0 of the 56 leak pairs. This page changes as those fill in.

## How it was checked

- The forecast, cyclone and heat graders reproduce published numbers before they pay a reward
  (`reports/*/2026-*-reproduction.md`).
- A separate reviewer agent (Claude Fable 5.1, `.claude/agents/reviewer.md`) reviews each phase
  before it closes: it runs the tests and the pipeline, checks results against the raw data and
  lists what is missing (`docs/reviews/`). Its findings were fixed test-first, except the ones that
  needed my decision, a licence and a data release, which came later (decisions 0015 and 0018).
  Phase 6 stays open until its run finishes.
- On 2026-11-02 Codex, a model from another family, reviewed the whole repository. Each of its 15
  findings was checked against the code (13 confirmed, 2 partly, none wrong). Fix batch 1 acted on
  14 of them (`docs/log.md`); the fifteenth, independent oracles for the bundled keys, is on the
  roadmap.
- Every published number re-renders from the committed per-item results
  (`tests/test_published_numbers.py`, decision 0019), and a weekly CI job rebuilds the items from
  their pinned sources (`docs/reproduce.md`).
