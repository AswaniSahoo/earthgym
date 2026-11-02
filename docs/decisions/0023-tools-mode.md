# 0023: a tools mode for ibtracs-storm-v1, one read-only SQL tool over the storm's rows

Date: 2026-11-02. Status: proposed, 2026-11-02: built and tested. The react version ran on all
300 items; the tool loop's run stopped at 225 when the API's credit ran out
(`reports/ibtracs/2026-11-02-phase-6-writeup.md`).

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
  call. The solver is `use_tools([query()])` and then `generate()`, which runs the model's tool
  calls in a loop until it replies without one; that final reply is scored. There is no system
  prompt and no submit tool, so the conversation is the one verifiers' null harness sends: the
  user prompt and the one tool (`tests/test_ibtracs_harnesses.py`,
  `tests/test_vf_tools_rollout.py`). `turn_limit=14` gives both harnesses the same budget, 14
  model turns whatever the calls in each, as `--env.agent.max-turns 14` does in verifiers, where
  a turn is one sampled reply (`verifiers/v1/trace.py:617-618`).
- A first version ran Inspect's `react()` agent instead, whose system prompt asks the model to
  "Prioritize parallel tool calls" and to report its answer with a submit tool
  (`inspect_ai/agent/_types.py:13-22`). That prompt was a condition of its result that the
  prompt runs and verifiers do not share (`docs/reviews/phase-6-tools.md`, M1), so I replaced it
  with the plain loop and ran the model again. Both runs are below.
- Both harnesses offer the same tool, the name `query`, one string argument `sql` and one
  description, in the same conversation.

The main alternative was a Python or bash tool, so a model could compute the answer in code. That
runs model-written code, which needs a sandbox: Inspect's `local` sandbox and an in-process
`exec` are not one (the hold row in `docs/radar.md`), and a container is a larger step than this
phase. SQL over one table asks for the same reading and filtering with no code run, and the
authorizer keeps it read-only.

Consequences:

- The react version, Claude Sonnet 5.5 on all 300 items (Batch API, $1.7107 in
  `reports/spend.md`), scores 0.747, against 0.703 with the rows in the prompt and the rule left
  out: 0.990 on ACE and 1.000 on peak category, as before, and 0.250 on hurricane hours against
  0.130. On hours, 16 items are right only in that run and 4 only with the rows in the prompt
  (exact two-sided McNemar p 0.012). It made 645 queries, a median of 2 an item and at most 6,
  with no query error and no item at its 30-message limit, and 253 of its 300 submissions were
  the number alone (`reports/ibtracs/2026-11-02-claude-sonnet-5-5-tools-react.md`,
  `reports/ibtracs/2026-11-02-rows-in-prompt-vs-tool-react.md`). Those numbers hold under
  react's prompt, which the prompt runs did not have, so the hours gain is not the tool's alone.
- The tool loop's run (Batch API, from 02:50 UTC) stopped at 225 of 300 items: the API refused
  further batches with "Your credit balance is too low to access the Anthropic API." That text
  is in the run's console output (`logs/2026-11-02-ibtracs-tools-loop-run.out`, not in git); in
  the log the 74 unfinished samples carry `CancelledError`. Its tokens, $1.2735, are in
  `reports/spend.md` and its 299 logged samples in
  `reports/ibtracs/results/2026-11-02-claude-sonnet-5-5-tools-loop-partial.jsonl`. That file is
  skewed: its 225 scored samples are all the ones that took a single tool turn, 100 of peak
  category, 92 of hours and 33 of ACE, so its numbers stand for no question set. The run
  finishes with `inspect eval-retry` on its log once there is credit; no number of it is
  reported before then.
- Tested with no model. In Inspect (`mockllm/model`), a scripted query and then the right final
  reply scores 1, a wrong one 0, the conversation holds no system prompt and offers the one tool,
  and a model that never stops querying stops at 14 turns. In verifiers, the toolset serves its
  task's rows through an in-process MCP server; `tests/test_ibtracs_server.py` starts the server
  as verifiers does, as `python -m ibtracs_storm_v1.taskset` fed one task over a stand-in `/task`
  channel, and queries it with verifiers' own MCP client; and `tests/test_vf_tools_rollout.py`
  runs a whole `vf-eval` rollout against a scripted endpoint on 127.0.0.1 that calls the tool
  once and then answers, which checks the tool call's round trip and the reward on the final
  reply. `vf-validate ibtracs-storm-v1 --runtime.type subprocess --taskset.tools true` passes the
  gold check on all 300 items, but it calls each task's reward and starts no tool server. CI runs
  that gold check and an Inspect tool-loop run with `mockllm/model`. The tests import `mcp` 2.0.0,
  verifiers' own dependency, from the lock.
- A verifiers rollout ran on 3 items with Qwen3.5-2B over the local llama-server of decision
  0022 (`vf-eval ... -n 3 -r 1`, 2026-11-02): the tool reached the model as `query`, two of the
  three rollouts queried, each answered from its own storm's rows (the first made no query), and
  `PRAGMA table_info(track)` came back as `error: not authorized`. All 3 replies then ran out of
  tokens while thinking, since `--sampling.chat-template-kwargs` did not turn Qwen's thinking off
  through vf-eval, so none reached an answer; the scripted rollout above checks the reward path.
  That rollout was a smoke test and its traces stay under `outputs/`, out of git. Its three rows:
  ace/2000255N31289 made no query and wrote 4,096 tokens; ace/1988221N30270 made 3 queries and
  wrote 5,421; ace/1998232N15312 made 7 and wrote 6,058; each scored 0.
- A taskset with no harness of its own runs on `bash` (`verifiers/v1/utils/loaders.py:153-161`),
  which offers `bash` and `edit` tools and executes code (`verifiers/v1/harness.py:52`), so on
  `subprocess` the model's commands would run on the host. So every environment package now
  exports verifiers' `NullHarness` in its `__all__`, which makes it the default harness of each
  of the four (`tests/test_vf_harness.py`); naming `--env.agent.harness.id null` still works.
  verifiers has no turn limit unless the run sets one
  (`verifiers/v1/configs/agent.py:45`), so the environment README's command sets
  `--env.agent.max-turns 14`, the budget of Inspect's `turn_limit`.
- In the react version, its system prompt asked the model to report its answer with `submit()`
  (`inspect_ai/agent/_types.py:20-22`). A 6-item probe of the hours question (Claude Sonnet 5.5,
  standard API, 2026-11-02, $0.0862 in `reports/spend.md`) showed what that does: every reply
  made two queries, and five of the six then submitted the number alone ("9", "129", "75", "60",
  "24"), which the answer-line rule scores 0; the sixth ended in an answer line. So tools mode,
  and only tools mode, also accepts a final reply that is the number alone
  (`contract.final_answer`, in both harnesses), with emphasis marks around the number but none
  inside it, so `2*3` is no answer. Re-scored that way all 6 answers parse, and all 6 are short of
  the key by 3 or 6 hours: the convention gap of the rules-hidden run (decision 0011), which the
  tool does not close. That probe's committed results
  (`reports/ibtracs/results/2026-11-02-ibtracs-tools-claude-sonnet-5-5-probe.jsonl`) hold the
  answer-line scoring of the time, with the five bare numbers unparsed; the rewards are the same,
  0 of 6. The tool-loop probe ($0.0792) ended all six replies in an answer line, with the same six
  answers.
- Each tools-mode task carries its rows in its data, a median of 2,862 bytes and 7,660 at most,
  so they are in verifiers' `traces.jsonl` and in Inspect's sample metadata and store.
- The table has no year, so a storm that ran into a new year would sort wrong by time. None of
  the 300 does.
- Besides its rows, a query can read the table's schema (`sqlite_master`, `EXPLAIN`), the SQLite
  version and the clock (`datetime('now')`), none of them another storm's data
  (`docs/reviews/phase-6-tools.md`).
