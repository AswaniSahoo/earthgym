# 0014: pin the environment packages' build backend

Date: 2026-11-01. Status: accepted, 2026-11-01, from the Phase 4 review (L6).

Context: the four environment packages (`climaqa-v1`, `era5-forecast-v1`, `ibtracs-storm-v1`,
`heat-basis-v1`) declared `requires = ["hatchling"]`, so each wheel was built with whatever
hatchling was newest at the time, and no decision record named the dependency. CLAUDE.md asks to
pin everything that can move and to record every dependency.

Decision: `hatchling==1.33.0` in each package's `[build-system]`, the newest release on PyPI
(uploaded 2026-10-28). All four wheels build with it (`uv build environments/<name>`), and CI
builds three of them on every push.

Consequences: a wheel rebuilt later uses the same backend. Bumping it is a one-line change per
package with this record updated. The packages carried no `license` field and the repo no
LICENSE file until I chose the MIT License (decision 0015).
