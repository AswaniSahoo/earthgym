# Draft: the four environments on Prime Intellect's Environments Hub

Not pushed. Requirements read on 2026-11-02 from PrimeIntellect-ai/prime at `d7af83a`
(`packages/prime/src/prime_cli/commands/env.py`), verifiers v0.4.0, Prime's docs
(docs.primeintellect.ai/tutorials-environments/create) and the community-environments
repository.

## What `prime env push` needs

- A `pyproject.toml` with `[project] name`, and a root `*.py` or a package with `__init__.py`,
  as a wheel that builds. The push uploads these `[project]` fields: version, description, tags,
  license, dependencies, requires-python.
- The archive leaves out hidden folders, `dist`, `build`, `__pycache__`, `outputs` and anything
  `.gitignore` matches.
- `--visibility` takes PUBLIC or PRIVATE. Pushing unchanged content is rejected, since "The
  content hash is based on your source files (*.py, pyproject.toml, README.md)": bump `version`
  or use `--auto-bump`, `--rc` or `--post`.
- The README is "(displayed on the Environments Hub)"; the CLI checks no sections. The
  community repository's `AGENTS.md` asks for one "covering setup, dependencies, reward rubric,
  configuration knobs, and sample `vf-eval` usage".

## Where each package stands

| package | version | license | README | to do before a push |
|---|---|---|---|---|
| `climaqa-v1` | 0.1.0 | MIT and Apache-2.0 | setup, reward, commands | a GitHub link (the Hub has no repository field), a `tags` field |
| `era5-forecast-v1` | 0.1.0 | MIT | setup, reward, commands, attribution | the same, and a version bump: its items changed on 2026-11-02 (decision 0021) |
| `ibtracs-storm-v1` | 0.1.0 | MIT | setup, reward, commands, data terms | the same |
| `heat-basis-v1` | 0.1.0 | MIT | setup, reward, commands | the same, after the GHCN-Daily question below |

The items are bundled in each package, so the Hub would carry them: the GHCN-Daily values in
the heat items included (`docs/release/dataset-card.md`).

## Open points

- `PrimeIntellect-ai/community-environments` has pull requests disabled
  (`"has_pull_requests": false`, 2026-11-02), so its PR template's bar (an `outputs/` folder with
  "at least 5 examples and 3 rollouts per example" and rewards above 0 some of the time) is a
  quality guide here, not a route. The small-model runs (decision 0022) can supply that sample.
- Prime's docs say "Do **not** use `[tool.uv.sources]`" for URL dependencies, while the
  community `AGENTS.md` says "use `tool.uv.sources`". The packages use no URL dependency.
- The default visibility when `--visibility` is left out is UNKNOWN; pass it explicitly.
