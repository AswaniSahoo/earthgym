# rlenv: how we work

Verifiable evals and RL environments for climate and earth science. Owner: Aswani Kumar Sahoo.

## Loop for every phase

1. Radar: the `scout` agent refreshes `docs/radar.md` (new and proven tools, benchmarks, papers),
   checked at the source.
2. Plan: a short plan in the phase's first PR description: goal, scope, what is out, how we test it.
3. Build test-first: write the failing test, make it pass with the least code, then refactor.
   No code without a test that needed it.
4. Run: experiments write a dated report under `reports/` with the exact config (model, dataset
   revision, prompt, seed) and results, so each one can become a blog post.
5. Review: the `reviewer` agent (Fable) writes `docs/reviews/phase-N-<name>.md`: ratings, verified
   issues, what is missing. Fixes land test-first before the phase closes.

## Rules

- Only the code that is needed. Standard library first; every dependency gets a record in
  `docs/decisions/`.
- Pin everything that can move: dataset revision plus sha256, GitHub Actions by commit, `uv.lock`.
- CI must be green: `ruff check`, `ruff format --check`, `pytest`.
- Every claim in a report cites its source (file:line, URL, quote). Unverified means UNKNOWN.
- Commits: one line, imperative, lowercase, no AI trailers. Never commit or push without
  Aswani's yes.
- No em dashes or en dashes in any prose.

## Layout

    src/rlenv/<phase>/   code, one package per phase
    tests/               unit tests, small inline fixtures, no network
    reports/             results of audits and experiments
    docs/reviews/             one review per phase
    docs/radar.md        what is new and proven, in adopt / trial / assess / hold rings
    docs/decisions/      why we chose what we chose
