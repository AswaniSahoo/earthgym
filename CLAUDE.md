# rlenv: how I work with my coding assistant

My instructions to Claude Code for this repository: verifiable evals and RL environments for
climate and earth science.

## Loop for every phase

1. Radar: the `scout` agent refreshes `docs/radar.md` (new and proven tools, benchmarks, papers),
   checked at the source.
2. Plan: a short plan in the phase's decision record: goal, scope, what is out, how it is tested.
3. Build test-first: write the failing test, make it pass with the least code, then refactor.
   No code without a test that needed it.
4. Run: experiments write a dated report under `reports/` with the exact config (model, dataset
   revision, prompt, seed) and results, so each one can become a blog post.
5. Review: the `reviewer` agent, a separate model, writes `docs/reviews/phase-N-<name>.md`:
   ratings, verified issues, what is missing. Fixes land test-first before the phase closes.

## Rules

- Only the code that is needed. Standard library first; every dependency gets a record in
  `docs/decisions/`.
- Pin everything that can move: dataset revision plus sha256, GitHub Actions by commit, `uv.lock`.
- CI must be green: `ruff check`, `ruff format --check`, `pytest`.
- Every claim in a report cites its source (file:line, URL, quote). Unverified means UNKNOWN.
- Commits: one line, imperative, lowercase, no AI trailers. Never commit or push without my yes.
- No em dashes or en dashes in any prose.

## Layout

    src/rlenv/<phase>/   code, one package per phase
    environments/        one verifiers package per environment
    tests/               unit tests, small inline fixtures, no network
    reports/             results of audits and experiments, with per-item results
    docs/decisions/      why I chose what I chose
    docs/reviews/        one review per phase
    docs/log.md          what changed and what I learned, newest first
    docs/roadmap.md      what I plan next
    docs/radar.md        what is new and proven, in adopt / trial / assess / hold rings
