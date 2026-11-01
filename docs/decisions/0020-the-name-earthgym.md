# 0020: the name earthgym

Date: 2026-11-02. Status: accepted, 2026-11-02.

Context: the repository and its Python package were called rlenv. That name is taken on PyPI:
on 2026-11-02 `https://pypi.org/pypi/rlenv/json` returned rlenv 1.1.dev2, "Accenta.AI Gym
Environement", so the package could never be published under it, and the name says nothing
about the subject.

Decision: I renamed the repository and the import package to earthgym. "Gym" is the word the
ecosystem uses for suites of verifiable tasks (reasoning-gym, NeMo Gym, SWE-Gym), and the name is
free: on 2026-11-02 `https://pypi.org/pypi/earthgym/json` and `https://pypi.org/pypi/earth-gym/json`
returned 404 (the JSON API is the reliable check, since the project page answers 200 for any
name), and a GitHub search for "earthgym" found no repository. The nearest names were
seakers/earth-gym (2 stars) and marcgirones/Earth-gym (0 stars).

Consequences:

- Imports, the entry points (`uv run python -m earthgym...`), the root pyproject, CI and the docs
  use the new name. The four environment packages keep theirs, which carry no rlenv prefix.
- The repository stays private. GitHub redirects the old URL, and the `data-v1` release moved
  with the repository.
- The git history is not rewritten, and the reviews in `docs/reviews/` keep the paths they cited
  at the time (`src/rlenv/...`).
- My local working folder keeps its old name.
