# How this was built

I built this repository with Claude Code, Anthropic's coding agent, as a pair programmer under
my direction, between 2026-10-30 and 2026-11-02. The git history shows the work as it happened,
corrections included.

## Who did what

Claude Code wrote the code and the tests, ran the pipelines and the model runs, and drafted the
reports and the decision records. It worked in phases with a fixed loop, written down in
`CLAUDE.md`: a radar of current tools checked at the source, a plan, test-first code, a dated
report, and a review before the phase closed.

The main design calls are mine:

- The ERA5 reward: skill over the better of persistence and climatology, so that copying a
  baseline earns nothing (decision 0007).
- No judge model for ClimaQA's cloze answers; a domain expert's review instead (decision 0005).
- One paid model, Claude Sonnet 5.5, within a $20 budget, and no Vertex AI or Gemini calls
  (decision 0010).
- ACE kept at one decimal, as NOAA reports it, so the runs stay comparable (decision 0011).
- The MIT License (decision 0015), the name earthgym, and keeping the repository private until
  the work is done.

Claude Code proposed most of the other technical details, for example the reward floor in
decision 0007, the item draws and the careless-reading baselines, and some were set during runs
I was not watching. I reviewed each one afterwards; the decision records state them as mine
because I keep them, and where the record shows a choice was not mine at the time, it says so
(the floor, in `docs/log.md`, 2026-10-30).

The checks that need a person's judgment I do myself: the 30-item ClimaQA sample and the 56
Gold and Silver leak pairs, from the sheets in `docs/human-checks/`.

## How it was checked

- The forecast, cyclone and heat graders reproduce published numbers before they pay a reward:
  WeatherBench 2's IFS HRES scores, NOAA NCEI's North Atlantic season figures and NWS Phoenix's
  heat counts (`reports/*/2026-*-reproduction.md`).
- Before each phase closed, a separate reviewer agent (Claude Fable 5.1,
  `.claude/agents/reviewer.md`) ran the tests and the pipeline, checked results against the raw
  data and listed what was missing (`docs/reviews/`). Its findings were fixed test-first before
  the phase closed, except the ones that needed my decision, a licence and a data release, which
  came later (decisions 0015 and 0018).
- On 2026-11-02 Codex, a model from another family, reviewed the whole repository. Each of its
  15 findings was checked against the code (13 confirmed, 2 partly, none wrong). Fix batch 1 acted
  on 14 of them (`docs/log.md`); the fifteenth, independent oracles for the bundled keys, is on
  the roadmap.
- Every published number re-renders from the committed per-item results
  (`tests/test_published_numbers.py`, decision 0019), and a weekly CI job rebuilds the items
  from their pinned sources (`docs/reproduce.md`).
