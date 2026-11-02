# 0023: a tools mode for ibtracs-storm-v1, one read-only SQL tool over the storm's rows

Date: 2026-11-02. Status: proposed, 2026-11-02: built and tested offline; no model has run it.

Context: every environment so far shows all its data in the prompt and grades one reply. With
the rules shown, Claude Sonnet 5.5 gets 299 of 300 IBTrACS items right, and with the rules
hidden it still gets 0.99 on ACE and on peak category (decision 0011). The radar's three Phase 6
trial rows (`docs/radar.md`, 2026-11-02) found the smallest tool-using design that needs no
Docker in either harness: one SQL tool over the item's rows, in the shape of OpenEnv's
`finqa_env`. The model then has to fetch and filter the rows itself, and every item records how
it used the tool.

Decision:

- Tools mode is `tools=True` in both harnesses: `StormConfig(tools=True)` in verifiers and
  `-T tools=true` in Inspect. The prompt (`contract.tools_prompt`) keeps the question, the units,
  the status legend and the answer line, names the table, its columns and the tool, and leaves
  out every row and, as in the rules-hidden ablation, the rule, whatever `rules` says. It is one
  text for all 100 storms of a question. The answer contract and the reward do not change.
- One tool, `query(sql)`, written once in `contract.py` with the standard library's `sqlite3`.
  `database(rows)` builds an in-memory table `track(time, status, wind, pressure)` with the rows
  as the prompt shows them: the time as month-day hour:minute, so no year, and NULL where the
  archive has no pressure. `query(db, sql)` runs one statement. Its guards, each with a test
  that fails without it:
  - An authorizer that allows only SQLITE_SELECT, SQLITE_READ and SQLITE_FUNCTION, set once the
    load is committed. INSERT, UPDATE, DELETE, DROP, CREATE, ATTACH, VACUUM INTO, PRAGMA and
    recursive queries are refused. Without it, ATTACH and VACUUM INTO each wrote a database file
    to disk. load_extension and a second statement after a semicolon are refused even without
    it, by Python's `sqlite3` itself.
  - A progress handler that interrupts a statement still running after 0.5 s: a four-way
    self-join of 150 rows stops at 0.50 s.
  - A limit of 8,000 bytes on any one value (`SQLITE_LIMIT_LENGTH`). The deadline cannot stop a
    single function call: in a scratch run (Python 3.12.13, SQLite 3.53.1),
    `SELECT length(randomblob(1000000000))` ran for 1.6 s against a 0.5 s deadline and allocated
    1 GB. With the limit it fails at once, "string or blob too big".
  - At most 200 rows and about 8,000 characters in a reply, cut at a whole line, with a note. Rows
    are read one at a time, so a cut also stops the statement. No storm needs a cut: the longest
    whole table is 191 rows and 5,399 characters.
  - Every error comes back as text, `error: <reason>`; nothing is raised to the model.
- verifiers 0.4.0, wired as its `glossary` example at tag v0.4.0: `TrackToolset`, a `vf.Toolset`
  with one `@vf.tool` method, returned by `StormTask.toolsets`. verifiers starts one server per
  rollout as `python -m ibtracs_storm_v1.taskset` (`verifiers/v1/mcp/launch.py:356`) and hands
  it the rollout's task data over its `/task` channel
  (`verifiers/v1/interception/server.py:1016-1029`, `verifiers/v1/mcp/server.py:202-219`), from
  which `setup_task` builds the table. So the rows ride on `StormData.rows`, set in tools mode
  only; the default and rules-hidden tasks keep their hashes (300 of 300 each).
  `TOOL_PREFIX = None`, so the model sees the tool as `query`, not `track_toolset_query`
  (`verifiers/v1/harnesses/utils/mcp.py:151`). `Task.toolsets` reads only the task config
  (`verifiers/v1/rollout.py:290`, `verifiers/v1/env.py:394`), so `StormConfig` copies `tools`
  into `StormTaskConfig`.
- Inspect 0.3.286: a setup solver puts the rows in the sample's store, bound per sample
  (`inspect_ai/_eval/task/run.py:2501`), and the tool builds the table from `store()` on each
  call. The solver is `react(tools=[query()], submit=AgentSubmit(answer_only=True), attempts=1)`
  with `message_limit=30`: room for 13 queries and the submit (with `mockllm/model`, a fourteenth
  query hits the limit). With `answer_only` the scored completion is the submitted string alone
  (`inspect_ai/agent/_react.py:316-317`).
- Both harnesses offer the same tool: the name `query`, one string argument `sql`, and one
  description.

The main alternative was a Python or bash tool, so a model could compute the answer in code. That
runs model-written code, which needs a sandbox: Inspect's `local` sandbox and an in-process
`exec` are not one (the hold row in `docs/radar.md`), and a container is a larger step than this
phase. SQL over one table asks for the same reading and filtering with no code run, and the
authorizer keeps it read-only.

Consequences:

- No model has been run in tools mode yet. The cost per item and how well a model uses the tool
  are UNKNOWN until a probe (decision 0010).
- Tested offline, with no model. In Inspect (`mockllm/model`), a scripted query and then the right
  submitted answer scores 1, a wrong one 0, and a model that never submits stops at 30 messages.
  In verifiers, the toolset serves its task's rows through an in-process MCP server, and
  `vf-validate ibtracs-storm-v1 --runtime.type subprocess --taskset.tools true` passes the gold
  check on all 300 items. A scratch smoke test started the server as verifiers does, gave it one
  task over a stand-in `/task` channel and queried it with verifiers' own MCP client: one tool,
  `query`, answering from that storm's rows. Not run: a verifiers rollout, whose chat loop needs a
  model endpoint.
- A taskset with no harness of its own runs on `bash` (`verifiers/v1/utils/loaders.py:153-161`),
  which offers `bash` and `edit` tools and executes code (`verifiers/v1/harness.py:52`), so on
  `subprocess` the model's commands would run on the host. So every environment package now
  exports verifiers' `NullHarness` in its `__all__`, which makes it the default harness of each
  of the four (`tests/test_vf_harness.py`); naming `--env.agent.harness.id null` still works.
  verifiers has no turn limit unless the run sets one
  (`verifiers/v1/configs/agent.py:45`); `--env.agent.max-turns 14` gives the same 13 queries and
  an answer as Inspect's 30 messages, since a turn is one sampled reply
  (`verifiers/v1/trace.py:617-618`). The command is in the environment's README; a dry run
  resolves it.
- In Inspect, react's own system prompt asks the model to report its answer with `submit()`
  (`inspect_ai/agent/_types.py:20-22`). A 6-item probe of the hours question (Claude Sonnet 5.5,
  standard API, 2026-11-02, $0.0862 in `reports/spend.md`) showed what that does: every reply
  made two queries and then submitted the number alone ("9", "129", "75"), which the answer-line
  rule scores 0. So tools mode, and only tools mode, also accepts a final reply or submission
  that is the number alone (`contract.final_answer`, in both harnesses). Re-scored that way all
  6 answers parse, and all 6 are short of the key by 3 or 6 hours: the convention gap of the
  rules-hidden run (decision 0011), which the tool does not close.
- Each tools-mode task carries its rows in its data, a median of 2,870 bytes and 7,660 at most,
  so they are in verifiers' `traces.jsonl` and in Inspect's sample metadata and store.
- The table has no year, so a storm that ran into a new year would sort wrong by time. None of
  the 300 does.
