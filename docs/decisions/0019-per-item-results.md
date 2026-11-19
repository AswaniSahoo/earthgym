# 0019: per-item results for every reported run, committed

Date: 2026-11-02. Status: accepted, 2026-11-02. From the Codex review's finding 5, with my aim
for fix batch 1: commit compact per-item results for every reported run, so a stranger can
recompute every published number without new runs, and keep them lean.

Status note, 2026-11-19: the results are now 33 JSONL files, 4,528,573 bytes, under
`reports/<env>/results/`, and three GRPO metrics files, 692,001 bytes, in `reports/grpo/results/`.
Run lines also hold `created`, `status` (the stopped tools-loop run) and `epochs`, which
`src/earthgym/results.py:119` writes for every run line; 15 committed files carry it, the
small-model runs and the four 2026-11-02 tools-mode files. Item lines of the small-model runs also
hold `epoch`. The tools-react run, the tool-loop probe and the stopped tool-loop run add `bare`,
`limit`, `queries` and `query_errors`, and the stopped run also `tool_turns` and `error`;
`2026-11-02-ibtracs-tools-claude-sonnet-5-5-probe.jsonl` has none of these. The Jev file has one
line per call (decision 0008). `tests/test_published_numbers.py` also re-renders the tools-react
run, the three-run report, the Jev report and the GRPO and small-model reports, and checks the
GRPO pick and the heat missing-value counts. The ERA5 baselines, the ClimaQA audit
(`reports/climaqa/findings.json` and `SUMMARY.md`) and the reproductions of published references
are not in it (`docs/reproduce.md`).

Context: the Inspect logs are not in git, so until now no one else could check a published
number short of running the models again.

Decision: one file per run and task, `reports/<env>/results/<name>.jsonl`, named after the
report it feeds (a probe, which has no report, after its log directory). The first line is the
run: the task and its arguments, the model, the sha256 of the bundled items file it was scored
on, the generate settings, the commit, the Inspect version, the start and end times, the token
totals, and the log file and directory. Each further line is one item: its id, the answer the
scorer parsed, the reward, and its tokens (input, cache write, cache read, output, reasoning),
plus the few flags a report reads from the reply text: whether an IBTrACS or heat reply names
the storm, its season or a season (`recognized`); for ClimaQA the item's complexity, for MCQ the
key and whether it is the longest option, for cloze the reply's line count and whether its last
line alone is right. No reply text and no prompts. 17 files, 378,933 bytes: the 9 task runs
behind the reports, the 7 probe logs (one ClimaQA probe holds two tasks), Gemini's ERA5 probe
among them.

`uv run python -m earthgym.results <env> <log dir> <name>` writes a file from the logs. Each report
module builds its summary from these rows, whether they come from a log or from a committed
file, so one code path serves both. `tests/test_published_numbers.py` needs neither the logs nor
the data: it re-renders every report and its JSON from the committed files and compares them
byte for byte (the two ClimaQA run reports and the comparison, ERA5, both IBTrACS runs and
their pair, both heat runs and their pair), checks every row of `reports/spend.md` against the
token totals of its results, and recomputes decision 0010's projection of 1,731,960 tokens from
the Gemini probe. Changing one reward in one file fails two of these tests (checked
2026-11-02).

Consequences:

- `uv run pytest tests/test_published_numbers.py` recomputes the published numbers on any
  clone, with no model call and no download (`docs/reproduce.md`).
- The rewards and answers are the ones each run recorded. Re-grading by the current rules
  changes no reward (decision 0016).
- The flags come from the reply text, which stays in the logs, so they can be recounted from
  these files but not derived again.
- A new reported run adds its file in the same commit as its report.
