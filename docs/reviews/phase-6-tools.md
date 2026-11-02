# Phase 6 review: tools mode for ibtracs-storm-v1, the storm's rows behind one read-only SQL tool

Reviewed 2026-11-02 at HEAD `bc66743` on `main`. At the start the tree held two untracked ClimaQA
results files from another session; while the review ran, `src/earthgym/grpo/` and
`tests/test_grpo.py` appeared untracked. None of these is Phase 6 and none was read. Every check
below describes the fourteen Phase 6 commits, d6513f7 through bc66743, all green in CI. Nothing
below is taken from memory; where a claim could not be checked it is marked UNKNOWN. No paid model
call was made, no GPU was used, no model server was started, and nothing was downloaded.

What was run: `uv run ruff check .` (clean), `uv run ruff format --check .` (176 files, clean),
`uv lock --check` (clean), `uv run pytest -q` (401 passed in 11.24 s), `gh run list` (success on
every Phase 6 commit), `uv run vf-validate ibtracs-storm-v1 --runtime.type subprocess
--taskset.tools true --taskset.split test --only-gold -c 2 -o <scratch>` (67 of 67 valid), the
report pipeline from the logs (`uv run python -m earthgym.ibtracs.report <tools log> --out` and
`... <shown log> --hidden <hidden log> --tools <tools log> --out`: the run report, its JSON and the
three-run report are byte-identical to the committed files), and five scratch scripts in the
session scratchpad: an independent re-score of the three Inspect logs that re-implements the
answer line, the bare-number rule, the ACE rounding and the reward from the prompt text and
decisions 0016 and 0023 without importing `earthgym` or `ibtracs_storm_v1`; a replay of every
logged query against a fresh table built from that sample's own rows, with the reply format
re-implemented; an attack battery of 96 statements against `contract.query` under
`ulimit -v 1200000`; a mockllm check of what tools mode pays a model that never submits; and a
JSON round trip of all 300 `StormData` through the class reference the `/task` channel sends.
Sources read at their root: the installed `verifiers` 0.4.0, `inspect_ai` 0.3.286 and `mcp`
2.0.0 at every line decision 0023 cites, the three logs on this machine, the probe log, the
verifiers rollout's `outputs/ibtracs-storm-v1--qwen3.5-2b-q8_0--ibtracs-storm-v1--3d9fe93e/`
(resolved config and `traces.jsonl`), the bundled items file and the spend ledger. Pins in
`uv.lock`: `verifiers 0.4.0`, `inspect-ai 0.3.286`, `mcp 2.0.0`, `anthropic 2.3.0`; the interpreter
is Python 3.12.13 with SQLite 3.53.1. No em or en dash in any Phase 6 prose file or module.

Spot checks against the raw data:

- The tools log (`2026-11-02T01-45-30-00-00_ibtracs-storm_Ma3MSMWfSxuvErUGwRyohJ.eval`): status
  success, 300 samples, `task_args {'path': None, 'rules': True, 'tools': True}`, commit 987744b
  dirty, `message_limit 30`, `batch 100`. Independent re-score: 0.7467 (stderr 0.0252); ACE
  0.99, peak category 1.00, hours 0.25; 0 errors, 0 samples at a limit, 0 parse failures, at
  most 12 messages in a sample. Every one of the 300 committed rows in
  `reports/ibtracs/results/2026-11-02-claude-sonnet-5-5-tools.jsonl` has the same answer and
  reward; the five token counts in its header equal the log's model usage summed. The two prompt
  logs re-score to 0.7033 and 0.9967, as published.
- Tool use, independently: 645 `query` calls, median 2, maximum 6 (267 items made 2, 23 made
  3, 9 made 4, 1 made 6), 0 items without a query, 0 replies starting `error:`, 0 replies cut,
  253 submissions that are the number alone and 47 that end in an answer line (ACE 97 and 3,
  hours 97 and 3, peak category 59 and 41). 304 of the 341 assistant turns that called a tool
  made two parallel calls; no query was a bare `SELECT * FROM track`, and the two most common
  shapes were `SELECT count(*), min(time), max(time) FROM track` (200) and
  `SELECT * FROM track ORDER BY time LIMIT n` (100).
- Wiring, Inspect: all 645 logged tool replies equal the replay against that sample's own rows,
  0 mismatches; every sample's `metadata["rows"]` equals the bundled item's; 300 of 300 logged
  prompts equal `contract.tools_prompt(item)` at HEAD, and the logged tool description and
  parameter list equal `ToolDef(tasks.query())` at HEAD. Every sample starts system, user,
  assistant, with one system prompt text in all 300 (Inspect's react prompt), and the model was
  offered two tools, `query` and `submit`.
- Wiring, verifiers: the rollout's resolved config has `env.taskset.tools True`,
  `env.taskset.task.tools True`, `env.agent.harness None`, `runtime.type subprocess`,
  `max_turns 14`, `sampling.max_tokens 4096` and `chat_template_kwargs {"enable_thinking":
  false}`; the three traces carry their task's rows (57, 23 and 96 rows for ace/2000255N31289,
  ace/1988221N30270 and ace/1998232N15312), advertise one tool named `query`, and the replies to
  `SELECT COUNT(*) FROM track` are 23 and 96; `PRAGMA table_info(track)` came back
  `error: not authorized`; the first trace made no query at all; every trace stopped on
  `agent_completed` with `exact 0.0` and 4,096, 5,421 and 6,058 output tokens. The JSON round
  trip `ibtracs_storm_v1.taskset:StormData` that `/task` hands a server keeps the rows and
  builds the table on 300 of 300 items.
- McNemar, independently from the two logs: ACE 1 right only with the rows in the prompt and 1
  only with the tool, p 1.0; peak category 0 and 1, p 1.0; hours 4 and 16, p 0.01182 (the
  doubled lower binomial tail at one half, as `report.flips` computes it; the chi-square with
  continuity correction is 6.05). The hours misses, independently from the rows: rules hidden,
  87 misses, 48 equal the elapsed-spell reading, 15 the status-held reading, 24 neither; tools,
  75 misses, 25, 38 and 12. All equal the published tables.
- Costs: the probe's tokens price to $0.086193 at standard rates and the full run's to
  $1.710741 through the Batch API ($0.0057025 an item); the probe times 50 at standard rates is
  $4.30965; the ledger's running total from the committed results is $10.926686. All four
  round to the published figures.
- The bundled items: 300 items on 300 distinct storms, the longest table 191 rows and 5,399
  characters as `query` renders it, no storm whose rows cross a calendar year, the rows as JSON
  7,660 bytes at most with a median of 2,862 (the upper median is 2,870, the figure decision
  0023 prints).
- The probe log: six hours items, two queries each; five submissions are the number alone (9,
  129, 75, 60, 24) and one, hurricane_hours/2010293N17277, is a sentence that ends in an answer
  line (24.0, which the old rule parsed); all six are 3 or 6 hours under the key.
- The null default: `loaders._plugin_class` on a module that exports a taskset and no harness
  raises `TypeError` ("exports no Harness subclass"), so `default_harness_id` returns `bash`,
  whose class has `EXECUTES_CODE True`; today all four packages resolve to their own id and
  `NullHarness`.

## 1. Ratings

| Area | Score | Justification |
|---|---|---|
| Correctness | 8 | Every published number reproduces from the logs and the raw rows: 300 rewards, 645 tool replies, the three-way table, both trap tables, the McNemar counts and p, the token counts and costs. The tool refused every write and file operation in 96 statements, interrupted every runaway at 0.50 to 0.52 s, never raised, and never exceeded 177 MB. The bare-number rule reads what the agent submits and still refuses prose. Against that: the run report's template says an item at the message limit scores 0, which the code does not enforce (M2); decision 0023 says every probe reply submitted the number alone where the probe log shows five of six (M3); and `last_line` strips every `*`, so a bare `2*3` reads as 23 (L4). |
| Minimalism and clarity | 8 | Standard library `sqlite3`, one tool in one module shared by both harnesses, 72 added lines in the contract, 50 in the taskset, 57 in the Inspect task, no new dependency. The guards are each one call with a comment that says why. Clutter: `StormTaskConfig` exists only to copy one flag verifiers cannot otherwise see (`taskset.py:43-44, 76-78`, forced by `verifiers/v1/rollout.py:290`), `report.py` has grown to 497 lines across four renderers, and `final_answer` repeats the number regex and the finite check of `answer` (`contract.py:168-176`). |
| Test coverage | 7 | Each guard has a test that fails without it (authorizer, deadline, value limit, row and character cut), the two harnesses are compared on the tool's name, argument and description, the Inspect path is run with mockllm for a right and a wrong submission and for a model that never submits, the toolset is served through a real `MCPServer`, the gold check runs in tools mode on all 300, and both reports re-render byte for byte. Missing: the tool-server launch (`taskset.py:101-102`) and the `/task` round trip are exercised by nothing in the repo (M5); no test says what a sample at the message limit is paid (M2); no test runs two samples concurrently against the store; `tool_use`'s `m.error` branch and `rows`'s key mismatch are untested (L8). |
| Reproducibility | 8 | The run report, its JSON and the three-run report rebuild byte for byte from the logs and, by test, from the committed results; the logged prompts and tool description equal HEAD; `uv.lock` is unchanged and clean; the Qwen rollout's config is resolved and on disk. Gaps: the run's commit is dirty (explained in the write-up, and the prompt and reward at HEAD match the log, so the explanation holds), the verifiers rollout exists only under `outputs/` and not in git, the probe's committed results carry the superseded parse (L7), and Inspect's react prompt is part of the run's conditions without being in the repo (M1). |
| CI/CD | 7 | Green on all fourteen commits, actions pinned by commit, `--locked --all-groups`, `vf-validate` and a mockllm eval for this environment. But no CI step runs tools mode: `ci.yml:28-31` validates and evaluates without `--taskset.tools true` or `-T tools=true`, and the gold check would not launch the tool server anyway (M5). |
| Research rigor | 7 | The comparison is on the same 300 items three ways with an exact paired test, the trap analysis names where the misses go, and the Limits say what one reply per item, Inspect only and the parse rule can and cannot show (the parse rule is shown not to move the comparison: 0 parse failures in both prompt runs). Against that: the Inspect run's agent prompt, its `submit` tool and its hint to prioritize parallel calls are conditions of the result and of every tool-use number, and neither the decision nor the write-up names them as such (M1); 267 of 300 items were one tool turn of two parallel queries and a submit, which the write-up calls a multi-turn rollout; the "13 queries and the submit" budget assumes one call a turn (L6). |
| Readiness to publish | 7 | The environment is sound and both harnesses are wired to one contract. Not yet: `docs/log.md` has no Phase 6 entry, the top-level README's phase table stops at Phase 5 and the roadmap still lists the tool-using environment as future work (M4); decision 0023 carries two sentences the data contradict (M3, L2); the verifiers command in the environment README has never produced a scored answer and its server launch has no committed evidence (M5). |

## 2. Plain answers to the checks asked

**The SQL tool as an attack surface.** Tested against `contract.query` with the standard library
only, in a fresh empty directory under a 1.2 GB virtual memory cap. Writes: INSERT (with
RETURNING and ON CONFLICT), UPDATE, DELETE, DROP, CREATE TABLE, CREATE TEMP TABLE, CREATE VIEW,
CREATE VIRTUAL TABLE (fts5), ANALYZE, BEGIN, SAVEPOINT, ATTACH (a file and `:memory:`), VACUUM and
VACUUM INTO all come back `error: not authorized` or `error: authorization denied`; no file
appeared and the table still held 191 rows afterwards, with the authorizer still on. Reads
outside the rows: `load_extension`, `readfile` and `writefile` do not exist or are refused;
`PRAGMA`, the `pragma_*` table-valued functions, `pragma_function_list` and `pragma_module_list`
are refused; what a model can read beyond its rows is the schema (`sqlite_master`, `sqlite_schema`,
`dbstat`, `EXPLAIN`, `EXPLAIN QUERY PLAN`), the SQLite version and source id and the wall clock
(`datetime('now')`), none of which is another storm's data. Time: a four-way self-join, a
three-way join with `ORDER BY random()`, `count(DISTINCT ...)` and `GROUP BY` over three-way
joins and a sorted three-way concatenation all stopped at 0.500 to 0.520 s; the pathological
`LIKE` and `GLOB` patterns (60 wildcards over 7,800 characters), `instr` and `replace` on
8,000-byte strings returned at once. Memory: `randomblob(10^7)`, `zeroblob(10^9)`,
`hex(zeroblob(4001))`, `replace` that would grow past 8,000 bytes, `json_each` over a 9,000-byte
document, `group_concat` and `json_group_array` over joins, and every sort or distinct over
7,999-byte blobs fail at once with `string or blob too big` (the length limit also bounds the
sorter's records); peak RSS over the whole battery was 177 MB. Crashes: an empty statement, a
comment, whitespace, a NUL byte, a blob cast to text (`Could not decode to UTF-8`), 1,200 nested
parentheses, 1,200 nested calls (`Recursion limit`), a 200,000-term expression (`Expression tree
is too large`), 600 compound terms, 2,000 columns, `printf` with a 10^9 width (NULL), integer
overflow, division by zero, two statements, and bound parameters all come back as a reply, never
an exception. One figure in decision 0023 is UNKNOWN here: that `randomblob(10^9)` without the
limit ran 1.6 s and took 1 GB; under the RAM cap I ran `randomblob(1.5 * 10^8)` with the deadline
and no limit, which returned in 0.26 s with 317 MB RSS, consistent with a single call the handler
cannot stop. Two harmless gaps in the README's "SELECT statements only": `EXPLAIN` and `EXPLAIN
QUERY PLAN` run, and `REINDEX` on a table with no index returns no error (L3).

**Both harness wirings.** Inspect: `rows_to_store` (`tasks.py:44-52`) puts the rows in the store
that `init_subtask_store(state.store)` binds per sample (`inspect_ai/_eval/task/run.py:2501`),
and `query` rebuilds the table from `store()` on each call (`tasks.py:55-66`). The replay of all
645 logged queries against each sample's own rows matched every reply, so no sample read another
storm. The same `storm_scorer(tools=True)` pays every sample through `contract.reward`, and the
gold check (`validate`) is the taskset's. verifiers: `Task.toolsets` returns one `TrackToolset`
per rollout when `config.tools` (`taskset.py:48-50`); verifiers builds it inside the rollout
(`rollout.py:290`), launches `python -m ibtracs_storm_v1.taskset` (`mcp/launch.py:356`) and the
server fetches `{"cls": "ibtracs_storm_v1.taskset:StormData", "task": <json>}` from `/task`
(`interception/server.py:1023-1029`) and calls `setup_task` on the validated object
(`mcp/server.py:211-212, 217-219`). The round trip keeps the rows on all 300 items, and the
three real rollouts show the tool as `query` with the right counts. The toolset's tools are wrapped
in an `async def` (`mcp/server.py:228-247`), so the MCP server never runs `query` on a worker
thread and the connection made in `setup_task` is used on the thread that made it. The null
default: all four `__init__.py` export `NullHarness`; the loader falls back to `bash` only when a
package exports no harness (`loaders.py:153-161`), and `BashHarness.EXECUTES_CODE` is True. What
differs between the two: Inspect's `react()` adds its own system prompt and a `submit` tool
(`inspect_ai/agent/_types.py:16-22`, seen in all 300 samples), verifiers' null harness sends the
task prompt alone with the one tool (the trace's first message is the user prompt); see M1.

**The full run's numbers.** All reproduce; see the spot checks. `report.flips`
(`report.py:363-378`) computes `2 * sum(C(n, k) for k <= min(a, b)) / 2^n`, capped at 1: the
exact two-sided McNemar p by doubling the smaller tail, which is one of the standard conventions
and the conservative one (the mid-p variant and the chi-square with continuity correction, 6.05
for 4 against 16, p 0.014, would both come out smaller). For a = b the cap makes p 1.0, and for
a = b = 0 it is 1.0 as well. The function raises when the two runs' ids differ and
counts an errored item as wrong, as documented.

**The bare-number rule.** `final_answer` (`contract.py:168-176`) tries the answer line first, then
accepts a reply of exactly one non-empty line that is only a number after `last_line`'s
stripping of `*`, backticks and the Unicode minus; prose such as `I think 9`, `24 hours` or two
lines without an answer line stays unparsed, and `1e999` stays None. It is used only when
`tools` is set in both harnesses (`taskset.py:55`, `tasks.py:83`). It does not open a way to be
paid without the answer: a bare number is the answer, and the key is never in the prompt, the
store or the trace the model sees. Two things it does change. First, with Inspect's react a
model that writes the number as text and never calls `submit` is prompted to continue until the
message limit, and at the limit its last text is scored: with mockllm, a model that replies `6`
hits `limit.type message` at 30 messages and is paid 1.0, as is `ANSWER: 6`; the published
template says such an item scores 0 (M2). Second, `last_line` strips every `*`, so a bare `2*3`
is read as 23 (L4). The write-up's point stands: 0 of 300 prompt-run replies lacked an answer
line, so the rule does not move the comparison.

**Every claim in the write-up and decision 0023.** Supported by the cited file, checked at the
line: the fourteen verifiers and Inspect citations (launch.py:356, interception/server.py:1016-
1029, mcp/server.py:202-219, mcp.py:151, rollout.py:290, env.py:394, loaders.py:153-161,
harness.py:52, configs/agent.py:45, trace.py:617-618, run.py:2501, _react.py:316-317,
_types.py:20-22, git.py:56-62) all say what the decision says they say; the table of three runs;
the flips and p; the trap counts; the tool-use sentence; the costs, projection and ledger total;
the 191 rows, 5,399 characters, 7,660 bytes and no storm across a year; `git diff 987744b 7f2525c`
on the scoring files is empty; Inspect marks any `git status --porcelain` output dirty; the
`-T tools=true` and `--env.taskset.tools true` flags exist (vf-eval's help lists
`--env.taskset.tools {True,False}`); 0 of 300 prompt-run replies without an answer line.
Not supported: "every reply made two queries and then submitted the number alone" (0023:102-104;
five of six did, M3); "each rollout's server answered from its own storm's rows" (0023:86; the
first of three made no query, L2); "a median of 2,870 bytes" (0023:108; that is the upper
median, the median is 2,862, L1); "`vf-validate ... --taskset.tools true` passes the gold check on
all 300 items" (0023:80-81) is true but proves only the reward, since the gold check does not
launch the tool server (M5); "a multi-turn rollout whose transcript records how the model read
the data" (write-up 80-82) describes 33 of 300 items, the other 267 made one tool turn and a
submit; "Both harnesses offer the same tool" (0023:58-59) is true of the tool and not of the
conversation around it (M1).

**The tests.** Each new test fails without the code it covers: the tools prompt test needs
`tools_prompt`; the refusal test's INSERT, UPDATE, DELETE, DROP, CREATE, ATTACH, VACUUM INTO and
PRAGMA rows pass without the authorizer, and ATTACH and VACUUM INTO leave files; the join test
would run far past 2 s without the progress handler; the value test would receive a 100 MB blob
without the limit; the cut test needs both cuts; the bare-number tests need `final_answer`; the
taskset tests need `rows`, `toolsets` and `TOOL_PREFIX`; the Inspect tests need `react`, the
store solver and `message_limit`; the harness test fails on a package that exports no harness
(checked with a module that exports the taskset alone); the report tests pin exact counts and
the exact p. Untested: the server launch and `/task` path, a sample paid at the limit, concurrent
samples against the store, `tool_use`'s `m.error` branch, `rows`'s key mismatch, `main --tools`,
and the `load_extension` and two-statement rows test Python's refusal rather than the
authorizer (fine, but they prove nothing about the guard).

## 3. Issues by severity

### High

None found. The tool wrote nothing and raised nothing in 96 statements, every published number
reproduces, and each rollout and sample reads its own storm's rows.

### Medium

- **M1. Tools mode is not the same task in the two harnesses, and the write-up's tool-use numbers
  are partly Inspect's agent prompt.** `react(tools=[query()], submit=AgentSubmit(answer_only=
  True), attempts=1)` (`src/earthgym/ibtracs/tasks.py:106`) prepends Inspect's default assistant
  prompt and submit prompt (`inspect_ai/agent/_types.py:16-22`): it tells the model to
  "Prioritize parallel tool calls" and to report with `submit()`, and offers a second tool. All
  300 samples in the log begin with that system message; 304 of 341 tool turns made two parallel
  queries, which is why the median is 2 and 267 items needed one tool turn. verifiers' null
  harness sends the contract prompt alone with the one tool (the Qwen trace's first message is
  the user prompt, `tools ['query']`). Decision 0023 names the submit prompt only as the cause of
  bare numbers (0023:100-101) and says "Both harnesses offer the same tool" (0023:58-59); the
  write-up presents the 645 queries, the median and the 253 bare submissions as properties of the
  environment (2026-11-02-phase-6-writeup.md:69-71) and calls the result "a multi-turn rollout"
  (80-82); the README says `--env.agent.max-turns 14` gives verifiers "the same budget"
  (environments/ibtracs_storm_v1/README.md:38-40). Smallest fix: one sentence in 0023, the
  write-up's Tool use bullet and the README that the Inspect run ran under react's system prompt
  and a submit tool, that verifiers does not, and that the parallel-call hint shapes the query
  counts; then, test-first, either pass `react(prompt=AgentPrompt(...))` with a text that names
  only the submit tool and no parallel-call hint, or give the verifiers task the same system
  prompt through `StormData.system_prompt`, so the two harnesses send the same conversation.
- **M2. The run report says an item at the message limit scores 0; the code does not make it
  so.** `src/earthgym/ibtracs/report.py:293-295` renders "{limit} of {n} items hit the
  30-message limit before submitting and score 0". With mockllm, a model that answers `6` as
  text and never submits is continued by react until the limit (30 messages, `limit.type
  message`) and its last text is scored: 1.0, and `ANSWER: 6` likewise. The published sentence
  prints 0 of 300 and is true for this run. Smallest fix: drop "and score 0", or count
  `sum(r["limit"] is not None and r["reward"] == 0 for r in rows)` and print both numbers; add
  the text-only never-submit case to `tests/test_ibtracs_harnesses.py` beside
  `test_inspect_tools_mode_stops_a_model_that_never_submits` (158-166) so the behaviour is
  stated either way.
- **M3. Decision 0023 misreports the probe.** `docs/decisions/0023-tools-mode.md:102-104`: "every
  reply made two queries and then submitted the number alone ("9", "129", "75"), which the
  answer-line rule scores 0." The probe log holds five bare submissions and one sentence ending
  in an answer line (hurricane_hours/2010293N17277, parsed 24.0 under the old rule), and the
  committed probe file `reports/ibtracs/results/2026-11-02-ibtracs-tools-claude-sonnet-5-5-
  probe.jsonl` records that answer as "24.0". Smallest fix: "five of the six replies ... the
  sixth ended in an answer line and was wrong by 6 hours".
- **M4. The repo's own records are behind the phase.** `docs/log.md` has no Phase 6 entry (its
  newest entry, line 5, is "2026-11-02, batch 2: ownership and the name"); the top-level
  `README.md` phase table (11-17) ends at Phase 5 and its environments table (25-30) does not
  say ibtracs-storm-v1 has a tools mode; `docs/roadmap.md:24-26` still lists "A tool-using
  environment ... computes statistics in a sandbox" as future work, which is neither done nor
  what was built. Smallest fix: one log entry with what changed and what was learned, one README
  row for Phase 6 with the 0.747 against 0.703 result, and move the roadmap bullet to done with
  the SQL design named.
- **M5. The tool-server launch path has no test, no CI step and no committed evidence.**
  `environments/ibtracs_storm_v1/ibtracs_storm_v1/taskset.py:101-102` (`TrackToolset.run()`),
  the `/task` fetch and `setup_task` in a launched process are exercised by nothing in the repo:
  `tests/test_ibtracs_harnesses.py:110-123` registers the toolset on an in-process `MCPServer`,
  and `.github/workflows/ci.yml:28-31` validates and evaluates without tools. Decision
  0023:80-81 cites a `vf-validate ... --taskset.tools true` gold check as the offline proof;
  rerun here on the 67-item test split it passed 67 of 67, but every task took 0.0 s and the run
  log has two lines and no launch, so the gold check calls `validate()` on the reward and never
  starts a server. The only end-to-end evidence is the 3-item Qwen rollout under `outputs/`,
  which is not in git and whose per-item results are not under `reports/` (decision 0019 asks for
  per-item results of every run); the "scratch smoke test" of 0023:81-83 is not in the repo.
  Smallest fix: make that smoke test a test, starting `sys.executable -m
  ibtracs_storm_v1.taskset` with `MCP_PORT_FILE` and a stand-in `/task` channel that serves one
  `StormData`, and assert one tool named `query` and a reply from that task's rows; commit the
  rollout's three rows (ids, queries, rewards) as a results file with its config; add
  `--taskset.tools true` to the CI `vf-validate` line for the reward and say in 0023 that the
  gold check does not launch servers.

### Low

- **L1.** `docs/decisions/0023-tools-mode.md:108`: "a median of 2,870 bytes". The median of the
  300 rows arrays as JSON is 2,862 (upper median 2,870, maximum 7,660 as stated). Fix: 2,862, or
  "upper median".
- **L2.** `docs/decisions/0023-tools-mode.md:86`: "each rollout's server answered from its own
  storm's rows". The first of the three traces made no tool call (0 queries, 4,096 output
  tokens); the other two did, with counts 23 and 96 that match their rows. Fix: "two of the three
  rollouts queried, each answered from its own storm's rows".
- **L3.** `environments/ibtracs_storm_v1/README.md:27`: "The tool runs SELECT statements only".
  `EXPLAIN` and `EXPLAIN QUERY PLAN` pass the authorizer (read-only), and `REINDEX` on a table
  with no index returns no error. The contract's docstring (`contract.py:105-107`) is exact.
  Fix: "runs read-only statements" in the README, or add `SQLITE_REINDEX` to the denied set with
  a test row.
- **L4.** `environments/ibtracs_storm_v1/ibtracs_storm_v1/contract.py:155` strips every `*`, so
  a bare submission `2*3` parses as 23.0 (checked with mockllm: answer 23.0, score 0). Harmless
  on this run (0 parse failures, no expression submitted) and older than this phase for the
  answer line, but a bare-number mode makes an expression likelier. Fix: strip only the
  emphasis marks, `re.sub(r"\*\*|\*(?=\S)|(?<=\S)\*", "", ...)` or simply `replace("**", "")`,
  with `2*3` as a test row that must stay None.
- **L5.** `tests/test_ibtracs_harnesses.py:13` imports `mcp.server.mcpserver`, which neither
  `pyproject.toml` (11, 22-26) nor the package (`environments/ibtracs_storm_v1/pyproject.toml:8`)
  declares; it is verifiers' dependency, locked at 2.0.0. The rule in `CLAUDE.md` is a record per
  dependency. Fix: one line in 0023 naming `mcp 2.0.0` as the transitive pin the test relies on,
  or add it to the `env` group.
- **L6.** The "13 queries and the submit" budget (`src/earthgym/ibtracs/tasks.py:23`, README
  38-40, 0023:55-56 and 96-98) counts one call a turn. A turn with two parallel calls costs three
  messages, so the real run's budget was nine such turns; verifiers' `max-turns 14` counts turns
  whatever the calls per turn, so the two budgets agree only for one call a turn. Fix: say
  "turns" and the parallel case, or set Inspect's limit on tool calls rather than messages.
- **L7.** The committed probe results (`reports/ibtracs/results/2026-11-02-ibtracs-tools-claude-
  sonnet-5-5-probe.jsonl`, commit ab25b7a) were scored before 987744b: five answers are "" with
  reward 0, while 0023:105-107 says all six parse once re-scored. The file is what decision 0019
  asks for, but it records a superseded rule without saying so. Fix: a sentence in 0023 that the
  probe file holds the pre-987744b scoring, or regenerate it with a note in the ledger.
- **L8.** Untested branches in `src/earthgym/ibtracs/report.py`: the `m.error is not None` arm
  of `tool_use` (108), the key-mismatch `ValueError` in `rows` (123-124), and `main` with
  `--tools` (478-486). Fix: one test each, or leave them noted; none affects a published number.

## 4. What is missing to close Phase 6

- M1 to M5 fixed test-first: the harness asymmetry named and then closed in code, the limit
  sentence made true, the probe sentence corrected, the log, README and roadmap brought up to the
  phase, and a test that launches the tool server as verifiers does.
- A verifiers rollout that reaches a scored answer. The README's `vf-eval` command has produced
  none: the 3-item Qwen run ended with `exact 0.0` on all three because the replies spent their
  4,096 tokens thinking even with `chat_template_kwargs {"enable_thinking": false}` in the
  resolved config (whether vf-eval forwards that key to llama-server is UNKNOWN; the decision
  says it did not take effect). Either a model that finishes, or a scripted client against the
  interception server, is needed before the verifiers path can be called run.
- The per-item results of that rollout under `reports/ibtracs/results/`, and the L1, L2 and L7
  corrections in decision 0023.
- A sentence in the environment README and the write-up on what the model can see besides its
  rows (the schema, the SQLite version, the wall clock) and on `EXPLAIN`, so "read-only" is
  stated exactly.

## 5. What I would not publish yet, and why

- The write-up's Tool use bullet and the sentence "Both harnesses offer the same tool" as they
  stand: the 645 queries, the median of 2 and the 253 bare submissions were produced under
  Inspect's react prompt, which asks for parallel calls and a submit tool that verifiers never
  shows, so a reader would take an agent-prompt effect for an environment property (M1).
- Decision 0023's probe paragraph and its "each rollout" sentence, until they say five of six
  and two of three (M3, L2).
- The environment README's `vf-eval` command as a tested path: it has never produced a scored
  answer, and nothing in the repo launches the server it depends on (M5).
- The run report's "and score 0" wording in any future run that reaches the limit (M2). For this
  run it prints 0 of 300 and is true.

## Re-review, 2026-11-02

Re-reviewed at HEAD `873b58c`, after the fix commits 088abe6, f414a25, f2c6529, caf98f1, 2d2a03d,
d370473, 541bac8, 61dbcbf, 550202c, 342d9be, eda64cd and 873b58c. The review above is left as it
was written. What was run: `uv run ruff check .` (clean), `uv run ruff format --check .` (188
files, clean), `uv lock --check` (clean), `uv run pytest -q` (423 passed in 21.07 s; the two new
end-to-end tests take 7.04 s and 2.36 s), `gh run list` (success on every fix commit through
873b58c), and scratch scripts over the stopped run's log, its probe log, the committed partial
results, the ledger and the parser's edges, with the parse rule and the reward re-implemented as
before. No paid call was made, no GPU or model server used; the tree holds only the two untracked
ClimaQA files it held at the start. No em or en dash in any changed prose file or module.

### Status of the findings

| Finding | Status | Evidence |
|---|---|---|
| M1, harness asymmetry | fixed | `src/earthgym/ibtracs/tasks.py:106-108`: `solver=[use_tools([query()]), generate()]` with `turn_limit=TURN_LIMIT` (14), no `react`, no `submit`. In the stopped run's log all 299 samples begin user, assistant, no sample has a system message, every model call offered the one tool `query`, and the plan is `rows_to_store`, `use_tools`, `generate` with `turn_limit 14`. `tests/test_ibtracs_harnesses.py` asserts the roles user, assistant, tool, assistant and the tools `[["query"], ["query"]]`; `tests/test_vf_tools_rollout.py:100` asserts verifiers' last request held user, assistant, tool, so the two harnesses now send the same conversation. The react run is kept under `-react` names (its results file is byte-identical to the old one, its report re-rendered by test), and decision 0023:62-68 and 85-86, the write-up's Status (14-19) and Results (85-95), README row 6, SUMMARY and the environment README (27-33, 40-44) name react's prompt as a second difference. The citation `inspect_ai/agent/_types.py:13-22` is right: line 13 is `PARALLEL_TOOLS_PROMPT`, 16-18 the assistant prompt, 20-22 the submit prompt. |
| M2, "and score 0" | fixed | `src/earthgym/ibtracs/report.py:241, 310-311`: `limit_paid` counted, and the sentence reads "stopped at a limit before a final reply; they are scored on their last reply (N right)". `tests/test_ibtracs_report.py` now drives the third sample to the turn limit with `ANSWER: 0.4` on its last reply and asserts reward 1.0 and "(1 right)". The re-rendered react report prints "0 of 300 ... (0 right)". |
| M3, the probe sentence | fixed | decision 0023:121-123: two queries each, five of the six submitted the number alone ("9", "129", "75", "60", "24"), the sixth ended in an answer line. The probe log reads the same: completions 9, 129, 75, 60, 24 and, for hurricane_hours/2010293N17277, a sentence ending in an answer line parsed as 24.0. |
| M4, log, README, roadmap | fixed | `README.md` has a Phase 6 row and lists `ibtracs-storm-v1` under phases 4 and 6; `SUMMARY.md` Phase 6 rewritten; `docs/log.md:5-34` has a Phase 6 entry; `docs/roadmap.md` no longer lists the tool environment as future work; the environment README is rewritten. Nit: `docs/log.md` now has two entries headed "2026-11-02, batch 2" (lines 5 and 36). |
| M5, the server launch path | partly fixed | `tests/test_ibtracs_server.py` starts `python -m ibtracs_storm_v1.taskset` with `VF_STATE_URL`, `VF_STATE_SECRET` and `MCP_PORT_FILE`, serves one task over a stand-in `/task` channel, connects with verifiers' `connect_mcp`, and asserts the one tool `query`, a reply from that task's rows, a refused DELETE and that `/task` was fetched (2.36 s here). `tests/test_vf_tools_rollout.py` runs `vf-eval` against a scripted OpenAI-style endpoint on 127.0.0.1 that calls the tool once and then answers, and asserts the tool reply from the task's rows and the contract's reward on the final reply (7.04 s). `.github/workflows/ci.yml:33-35` adds the tools-mode gold check and a mockllm tool-loop run; decision 0023:101-102 now says the gold check starts no tool server. Both tests pass here and in CI. Still open, and minor: the 3-item Qwen rollout's per-item results are not under `reports/ibtracs/results/` (decision 0019); its traces remain only in `outputs/`. |
| L1, 2,870 | fixed | decision 0023:133 says 2,862. |
| L2, "each rollout" | fixed | decision 0023:106-107: two of the three rollouts queried, the first made no query. |
| L3, "SELECT only" | fixed | environment README 27-30: refuses every write and every file; a query can read only the schema, the SQLite version and the clock; decision 0023:137-139 names `sqlite_master`, `EXPLAIN`, the version and `datetime('now')`. |
| L4, inner asterisks | fixed | `contract.py:174-177`: marks `[ \t*`]*` only around the number, matched against the whole single-line reply. Checked: `2*3`, `1*2`, `6 * 2`, `*`, `**` and `6\n6` give None; `**6**`, `*6*`, `` `6` ``, `6.`, `**6**.`, `-6`, the Unicode minus, `.5` and `1e3` parse; `6*` and `*6` parse as 6 (asymmetric marks, harmless). The answer-line path is unchanged: `ANSWER: 2*3` still reads 23.0 through `last_line` (`contract.py:152-157`, decision 0016, shared by every phase), which was outside L4's scope. |
| L5, `mcp` undeclared | fixed | decision 0023:103-104 records `mcp` 2.0.0 as verifiers' dependency from the lock. |
| L6, budget in turns | fixed | `turn_limit=14` counts model generations (`inspect_ai/_eval/task/task.py:185`, "Limit on total turns (model generations)"); decision 0023:59-61 and the environment README say 14 model turns whatever the calls in each; the test at the limit counts exactly 14 assistant messages. |
| L7, the probe file's scoring | fixed | decision 0023:128-131 says the committed probe results hold the answer-line scoring of the time, five bare numbers unparsed, rewards 0 of 6 either way. |
| L8, untested branches | fixed | `tests/test_ibtracs_report.py`: a `query` call with no `sql` counts as a query error (Inspect's tool error, the `m.error` branch), `rows` refuses a key mismatch, and `main` writes the three-run report from three log directories. |

### The stopped tool-loop run, checked

- The log `2026-11-02T02-50-53-00-00_ibtracs-storm_ctLXiSupdRzDZnkgRVYgvh.eval`: status
  `cancelled`, commit d370473 dirty, `turn_limit 14`, 299 samples, 225 scored and 74 errored; the
  item never logged is ace/1981244N30287. The 225 re-score to the committed partial file row for
  row (0 differences); no scored sample hit a limit, none answered with a bare number, 283
  samples made 2 queries and 16 made 3. Per question the scored set is 33 ACE (33 right), 92
  hours (23 right) and 100 peak category (100 right): not a random 225, and every scored sample
  finished in one tool turn while every errored one had made two, since the API stopped the run
  between the second and third rounds of batch requests. So the write-up's refusal to report any
  number of this run is right, and a mean over the 225 would mislead.
- The ledger row: tokens 1802, 389144, 360009, 153448, 61295 equal the header, which Inspect's
  eval-level usage gives; the per-sample sums are smaller by 8, 2,077, 2,461, 401 and 165, the
  usage of responses whose samples were cancelled. Costs from the committed tokens: the probe
  $0.079150, the run $1.273472, the totals $11.005837 and $12.279309; the four published
  figures round from these. The tool-loop probe's six replies all end in an answer line with the
  same six answers as the react probe (9, 129, 75, 60, 24, 24), as decision 0023:131-132 says.
- Where the refusal is recorded: the log's 74 errored samples all carry
  `CancelledError('Cancelled via cancel scope ...')`, not the API's message. The message is in
  `logs/2026-11-02-ibtracs-tools-loop-run.out` (local, not in git): batches of 300, 286, 14, 1,
  73 and 1 requests were created, then a batch creation raised `anthropic.BadRequestError: Error
  code: 400 ... 'Your credit balance is too low to access the Anthropic API. Please go to Plans &
  Billing to upgrade or purchase credits.'`, and the run was cancelled; the 73-request batch
  msgbatch_01BYbeuUzRq3AN6Z65htBYBp is the one never marked completed, as the ledger says. So the
  write-up (10-13), decision 0023:87-92 and `reports/spend.md:23-29` are exact as far as they go
  (N1 below asks for the source of the quote and the log's own status to be named).
- `inspect eval-retry` as the way to finish: consistent with the source. A retry rebuilds the
  task from the log with its `turn_limit` (`inspect_ai/_eval/eval.py:1863`) and reuses the
  samples the previous log completed (`inspect_ai/_eval/task/run.py:1360-1425`); the special
  recovery path is for `started` logs only (`eval.py:1736`), so a `cancelled` log takes the plain
  retry. Not run here (no credit), so whether it completes cleanly is UNKNOWN until it does.

### New findings

- **N1 (Low).** The record of the stop points at `reports/spend.md` for the API's words, and the
  only artifact that holds them is `logs/2026-11-02-ibtracs-tools-loop-run.out`, outside git;
  the log itself records a cancellation. Smallest fix: one clause in `reports/spend.md:23-29` or
  decision 0023:87-92 naming that file and saying the log's status is `cancelled` with the 74
  unfinished samples marked `CancelledError`.
- **N2 (Low).** The committed partial file is skewed (33 of 100 ACE items, all one-tool-turn
  samples), which nothing in the file says. Smallest fix: a sentence beside it in decision 0023
  or in the ledger note, so no one computes a mean from it before the run finishes.
- **N3 (nit).** `docs/log.md` has two entries headed "2026-11-02, batch 2".

### What remains before Phase 6 can close

- Finish the tool-loop run (the retry), then: its per-item results without `--partial`, its run
  report, the three-run report of shown, hidden and tool loop (the McNemar pairs against rules
  hidden, now a one-difference comparison), the rows in `tests/test_published_numbers.py`, a
  ledger row for the retry's tokens beside the stopped row, and the write-up's Status, Results and
  Cost sections, decision 0023's Consequences, README row 6 and SUMMARY rewritten around that
  run. The report should say which commit scored which samples if the retry runs at a later
  commit than d370473, with `git diff` on the contract and the task as the check.
- The 3-item Qwen rollout's per-item record under `reports/ibtracs/results/`, or one line in
  decision 0023 saying its traces are kept only locally (the rest of M5).
- N1 and N2, one sentence each.
