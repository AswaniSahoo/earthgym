# 0015: the MIT License for earthgym

Date: 2026-11-02. Status: accepted, 2026-11-02: I chose the MIT License.

Status note, 2026-11-19: three statements below no longer hold. `climaqa-v1` declares
`license = "MIT AND Apache-2.0"` (`environments/climaqa_v1/pyproject.toml:5`); the other three
declare `"MIT"`. Each environment package now has a copy of `LICENSE` in its `license-files`, so
every wheel carries the MIT text, and climaqa-v1's the Apache-2.0 text and its `NOTICE` as well
(`tests/test_licences.py`; `.github/workflows/ci.yml:23-27`; all four wheels built and listed on
2026-11-19). The repository is public since 2026-11-13 (decision 0027).

Decision: a `LICENSE` file at the repo root with the MIT License text from GitHub's licenses
API (`gh api /licenses/mit`), copyright 2026 Aswani Kumar Sahoo. Every pyproject declares it as
a PEP 639 expression, `license = "MIT"`; the root one also lists `license-files = ["LICENSE"]`,
so the `earthgym` wheel carries the text. The built wheels show `License-Expression: MIT` (checked
with `uv build`, uv_build for the root and hatchling 1.33.0 for the four environments).

Consequences: the environment wheels carry the expression but not the text, since a
`license-files` path may not point above the package's own directory; a copy of `LICENSE` in
each package would add it. The license covers the code; the bundled and reported data keep their
sources' terms (README, License). The repository stays private: making it public is a
separate decision I have not made yet.
