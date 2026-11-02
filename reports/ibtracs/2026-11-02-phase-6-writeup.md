# Reading the track through a tool: a tools mode for ibtracs-storm-v1

Phase 6 of earthgym, written up on 2026-11-02. Every number below comes from a file in this repo;
the source is named next to it. The phase's main run is not finished: see the status below.

## Status

- The tools mode is built and tested, in both harnesses, as a plain tool loop: the user
  prompt, one `query` tool, and the final reply scored (decision 0023).
- Its run on Claude Sonnet 5.5 stopped at 225 of 300 items, when the API refused further
  requests: "Your credit balance is too low to access the Anthropic API." (`reports/spend.md`).
  It finishes with `inspect eval-retry` once there is credit; until then this write-up reports
  no number of that run.
- The numbers below come from the first version, which ran Inspect's `react()` agent. Its
  system prompt asks the model to "Prioritize parallel tool calls", to "Do some reasoning
  before your actions" and to report its answer with a submit tool
  (`inspect_ai/agent/_types.py:13-22`). The prompt runs it is compared with had no system
  prompt, so that prompt is a second difference between the runs, beside the tool. The review
  of this phase found it (`docs/reviews/phase-6-tools.md`, M1), and the tool loop removes it.

## The question

Every environment so far puts all its data in the prompt and grades one reply. With the rules
shown, Claude Sonnet 5.5 gets 299 of 300 IBTrACS items right
(`reports/ibtracs/2026-11-01-claude-sonnet-5-5.md`). Phase 6 asks what changes when the model
has to fetch the data itself: the same 300 storms and questions, the rule left out as in the
Phase 4 ablation, and each storm's rows behind one read-only SQL tool instead of in the prompt.

## The environment

- Tools mode is `-T tools=true` in Inspect and `--env.taskset.tools true` in verifiers. The
  prompt keeps the question, the units, the status legend and the answer line, names the table
  `track(time, status, wind, pressure)` and the tool, and leaves out the rows and the rule
  (`contract.tools_prompt`, decision 0023).
- One tool, `query(sql)`, over an in-memory SQLite copy of the storm's rows. An authorizer
  refuses every write and every file, a statement still running after 0.5 s stops, no value
  may pass 8,000 bytes, a reply holds at most 200 rows and about 8,000 characters, and every
  failure comes back as `error: <reason>` text. Each guard has a test that fails without it
  (`tests/test_ibtracs_contract.py`). Besides its rows, a query can read only the table's
  schema, the SQLite version and the clock (decision 0023).
- Both harnesses send the same conversation: the user prompt and the one tool, no system
  prompt and no submit tool. The model's tool calls run in a loop until it replies without
  one, and that final reply is scored, within 14 model turns: Inspect's `turn_limit` and
  verifiers' `--env.agent.max-turns 14` (decision 0023).
- The reward does not change, but tools mode also accepts a final reply that is the number
  alone, which the react version's model gave on five of the six probe items
  (`contract.final_answer`, decision 0023).
- No model-written code runs: every environment package makes verifiers' null harness its
  default, where verifiers would otherwise give the model a bash tool on the host
  (`tests/test_vf_harness.py`).

## How it was tested

- With Inspect's `mockllm/model`: a scripted query and then the right final reply scores 1,
  a wrong one 0, the conversation holds no system prompt and offers the one tool, and a model
  that never stops querying stops at 14 turns (`tests/test_ibtracs_harnesses.py`).
- The tool server started as verifiers starts it, fed one task over a stand-in `/task`
  channel and queried with verifiers' own MCP client (`tests/test_ibtracs_server.py`), and a
  whole `vf-eval` rollout against a scripted endpoint that calls the tool once and then
  answers: the tool reply comes from the task's own rows and the reward is the contract's
  (`tests/test_vf_tools_rollout.py`). CI runs the gold check in tools mode and an Inspect run
  of the tool loop with `mockllm/model`.
- Two 6-item probes of the hours question on Claude Sonnet 5.5 at standard prices: $0.0862 for
  the react version and $0.0792 for the tool loop (`reports/spend.md`). Both gave the same six
  answers, every one 3 or 6 hours short of the key.
- A 3-item verifiers rollout with Qwen3.5-2B over a local llama-server: the tool reached the
  model as `query`, and the two rollouts that queried were answered from their own storms. No
  reply reached an answer, since Qwen's thinking could not be turned off through vf-eval
  (decision 0023).

## Results of the react version

Claude Sonnet 5.5 on the same 300 items three ways
(`reports/ibtracs/2026-11-02-rows-in-prompt-vs-tool-react.md`):

| question | n | rules shown | rules hidden | tools (react) |
|---|---|---|---|---|
| ace | 100 | 0.990 | 0.990 | 0.990 |
| peak_category | 100 | 1.000 | 0.990 | 1.000 |
| hurricane_hours | 100 | 1.000 | 0.130 | 0.250 |
| all | 300 | 0.997 | 0.703 | 0.747 |

- On ACE and peak category nothing moves: 1 item flips each way on ACE, and 1 flips to right
  on peak category.
- On hurricane hours, 16 items are right only in the react run and 4 only with the rows in the
  prompt, an exact two-sided McNemar p of 0.012 (same file). That run differs from the prompt
  run in two ways, the tool and react's system prompt, so the gain cannot be put on the tool.
- The hours misses still follow a careless reading of the rule: 63 of the 75 in the react run
  and 63 of the 87 with the rows in the prompt (same file).
- Tool use, under react's prompt and its call for parallel tool calls: 645 queries, a median of
  2 an item and at most 6, no query error, no item at the 30-message limit of that version, and
  253 of the 300 submissions the number alone
  (`reports/ibtracs/2026-11-02-claude-sonnet-5-5-tools-react.md`). The review counted 304 of
  the 341 tool turns as two parallel queries, and 267 of the 300 items as one tool turn and a
  submission (`docs/reviews/phase-6-tools.md`).

## What this means for RL

- For a model at this level, the react version adds no headroom on ACE or peak category: it
  gets them right whether the rows are in the prompt or behind the tool. Hours stays low for
  the reason it was low in Phase 4: without the rule, the counting convention is a guess
  (decision 0011).
- What tools mode adds is a rollout whose transcript records how the model read the data,
  every query and its reply, on the same items and with the same reward as the prompt version.
  In the react run most items took a single tool turn, so few transcripts were long. How well a
  small open model uses the tool is not measured here.

## Cost

The react version: its probe $0.0862 at standard prices and its run $1.7107 through the Batch
API. The tool loop: its probe $0.0792 and the stopped run $1.2735 for the tokens Inspect
logged. The ledger stands at $12.2793 of the $20 budget. The account ran out of credit during
the tool-loop run, so its bill and this ledger differ by an amount that is UNKNOWN here; the
Console is the authority (`reports/spend.md`).

## Limits

- One reply per item with no seed, as in Phase 4. The McNemar test compares two runs item by
  item; a rerun would give other replies, and the run-to-run spread is not measured.
- The react run's numbers hold for react's prompt only (see Status).
- The tools prompt always leaves the rule out, so no run puts a tool beside the rule shown.
- The react run's log marks commit 987744b dirty: Inspect sets that for any `git status
  --porcelain` output, untracked files included (`inspect_ai/_util/git.py:56-62`). Its scoring
  code did not change after that commit: `git diff 987744b 7f2525c --
  environments/ibtracs_storm_v1/ibtracs_storm_v1/ src/earthgym/ibtracs/tasks.py` is empty.
- North Atlantic storms from 1980 to 2025 only, the 300 items of Phase 4.

## Reproduce

    uv run inspect eval src/earthgym/ibtracs/tasks.py@ibtracs_storm -T tools=true \
        --model anthropic/claude-sonnet-5-5 --batch
    uv run python -m earthgym.results ibtracs <tools log dir> <name>
    uv run python -m earthgym.ibtracs.report <tools log dir> --out <run>.md
    uv run python -m earthgym.ibtracs.report <shown log dir> --hidden <hidden log dir> \
        --tools <tools log dir> --out <three runs>.md
    uv run pytest -q tests/test_published_numbers.py   # the reports, from the committed results

Sources: IBTrACS v04r01 and NCEI's conventions, as in the Phase 4 write-up
(`reports/ibtracs/2026-11-01-phase-4-writeup.md`); the tool, its guards and both harnesses'
wiring, decision 0023; the review, `docs/reviews/phase-6-tools.md`.
