# 0015: the MIT License for rlenv

Date: 2026-11-02. Status: accepted, 2026-11-02: I chose the MIT License.

Decision: a `LICENSE` file at the repo root with the MIT License text from GitHub's licenses
API (`gh api /licenses/mit`), copyright 2026 Aswani Kumar Sahoo. Every pyproject declares it as
a PEP 639 expression, `license = "MIT"`; the root one also lists `license-files = ["LICENSE"]`,
so the `rlenv` wheel carries the text. The built wheels show `License-Expression: MIT` (checked
with `uv build`, uv_build for the root and hatchling 1.33.0 for the four environments).

Consequences: the environment wheels carry the expression but not the text, since a
`license-files` path may not point above the package's own directory; a copy of `LICENSE` in
each package would add it. The license covers the code; the bundled and reported data keep their
sources' terms (README, License). The repository stays private: making it public is a
separate decision I have not made yet.
