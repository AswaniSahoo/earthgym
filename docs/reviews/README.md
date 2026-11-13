# Reviews

One review per phase, written before the phase closed by a separate reviewer agent (Claude
Fable 5.1, defined in `.claude/agents/reviewer.md`). Each review ran the tests and the pipeline,
checked results against the raw data, rated the phase and listed what was missing. The issues it
raised were fixed test-first before the phase closed, except the ones that needed my decision (a
licence and a data release, decisions 0015 and 0018), so the ratings describe the state before
those fixes.

`2026-11-13-go-public.md` is not a phase review: it covers the change set that recorded the
repository going public, and its session reported its model as Claude Fable 5.2.

The reviews cite files and line numbers as they were at the time. `WORKBOARD.md`, which several
of them cite, was later removed; its open items are in `docs/roadmap.md`.
