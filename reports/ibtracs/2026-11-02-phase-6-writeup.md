# Reading the track through a tool: a tools mode for ibtracs-storm-v1

Phase 6 of earthgym, written up on 2026-11-02. Every number below comes from a file in this repo;
the source is named next to it.

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
- One tool, `query(sql)`, over an in-memory SQLite copy of the storm's rows. It runs one SELECT
  statement: an authorizer refuses writes, ATTACH, PRAGMA and the rest, a statement still
  running after 0.5 s stops, no value may pass 8,000 bytes, a reply holds at most 200 rows and
  about 8,000 characters, and every failure comes back as `error: <reason>` text. Each guard has
  a test that fails without it (`tests/test_ibtracs_contract.py`, decision 0023).
- The reward does not change. Inspect's agent asks the model to report its answer with a submit
  tool, and in the probe the model submitted the number alone, so tools mode, and only tools
  mode, also accepts a submission that is the number alone (`contract.final_answer`, decision
  0023).
- No model-written code runs. Every environment package now makes verifiers' null harness its
  default; without it, verifiers would give the model a bash tool on the host
  (`tests/test_vf_harness.py`, decision 0023).
- Inspect stops a sample at 30 messages, room for 13 queries and the submit;
  `--env.agent.max-turns 14` gives verifiers the same budget (decision 0023).

## How it was tested

- Offline, with Inspect's `mockllm/model`: a scripted query and then the right submission scores
  1, a wrong one 0, and a model that never submits stops at 30 messages
  (`tests/test_ibtracs_harnesses.py`). The verifiers toolset serves each task's rows through an
  in-process MCP server, and the gold check passes on all 300 items in tools mode (same file).
- A 6-item probe of the hours question on Claude Sonnet 5.5, standard API, $0.0862
  (`reports/spend.md`). It showed the bare-number submissions above.
- A 3-item verifiers rollout with Qwen3.5-2B over the local llama-server: the tool reached the
  model as `query`, each rollout was served its own storm, and a PRAGMA came back as an error.
  No reply reached an answer, since Qwen's thinking could not be turned off through vf-eval
  (decision 0023).

## Results

Claude Sonnet 5.5 on the same 300 items three ways
(`reports/ibtracs/2026-11-02-rows-in-prompt-vs-tool.md`):

| question | n | rules shown | rules hidden | tools |
|---|---|---|---|---|
| ace | 100 | 0.990 | 0.990 | 0.990 |
| peak_category | 100 | 1.000 | 0.990 | 1.000 |
| hurricane_hours | 100 | 1.000 | 0.130 | 0.250 |
| all | 300 | 0.997 | 0.703 | 0.747 |

- Rules hidden against tools is the comparison that isolates the tool: both leave the rule out,
  and only the place of the rows differs. On ACE and peak category nothing moves: 1 item flips
  each way on ACE, and 1 flips to right on peak category.
- On hurricane hours, 16 items are right only with the tool and 4 only with the rows in the
  prompt, an exact two-sided McNemar p of 0.012 (same file).
- The hours misses still follow a careless reading of the rule: 63 of the 75 with the tool and
  63 of the 87 with the rows in the prompt. With the tool more of them count each row's status
  until the next row (38 against 15), and fewer take the elapsed time of each hurricane spell
  (25 against 48) (same file).
- Tool use: 645 queries, a median of 2 an item and at most 6; no item was submitted without a
  query; no query came back as an error; no item reached the message limit; 253 of the 300
  submissions were the number alone (`reports/ibtracs/2026-11-02-claude-sonnet-5-5-tools.md`).

## What this means for RL

- For a model at this level, tools mode adds no headroom on ACE or peak category: it gets them
  right whether the rows are in the prompt or behind the tool. Hours stays low for the reason it
  was low in Phase 4: without the rule, the counting convention is a guess, and most misses
  follow one of two careless readings (decision 0011). The tool helps on hours without closing
  that gap.
- What tools mode adds is the shape of the task: a multi-turn rollout whose transcript records
  how the model read the data, every query and its reply, on the same items and with the same
  reward as the prompt version, so the two can be compared item by item. How well a small open
  model uses the tool is not measured here.

## Cost

The probe cost $0.0862 at standard prices and the full run $1.7107 through the Batch API at half
price, $0.00570 an item, under half of the probe's projection of $4.31 at standard prices. The
ledger stands at $10.9267 of the $20 budget (`reports/spend.md`).

## Limits

- One reply per item with no seed, as in Phase 4. The McNemar test compares these two runs item
  by item; a rerun would give other replies, and the run-to-run spread is not measured.
- The tools prompt always leaves the rule out, so no run puts a tool beside the rule shown.
- The full run used Inspect only. The verifiers path is tested offline and in a 3-item rollout
  that never reached an answer.
- 253 of the 300 tools-mode submissions were the number alone, which the prompt runs would
  score 0. Every prompt-run reply had an answer line (0 of 300 without one, in both prompt
  reports), so the parse rule does not move the comparison.
- The run's log marks commit 987744b dirty: Inspect sets that for any `git status --porcelain`
  output, untracked files included (`inspect_ai/_util/git.py:56-62`). The scoring code did not
  change after that commit: `git diff 987744b 7f2525c --
  environments/ibtracs_storm_v1/ibtracs_storm_v1/ src/earthgym/ibtracs/tasks.py` is empty.
- North Atlantic storms from 1980 to 2025 only, the 300 items of Phase 4.

## Reproduce

    uv run inspect eval src/earthgym/ibtracs/tasks.py@ibtracs_storm -T tools=true \
        --model anthropic/claude-sonnet-5-5 --batch
    uv run python -m earthgym.results ibtracs <tools log dir> <name>
    uv run python -m earthgym.ibtracs.report <tools log dir> --out <run>.md
    uv run python -m earthgym.ibtracs.report <shown log dir> --hidden <hidden log dir> \
        --tools <tools log dir> --out <three runs>.md
    uv run pytest -q tests/test_published_numbers.py   # both reports, from the committed results

Sources: IBTrACS v04r01 and NCEI's conventions, as in the Phase 4 write-up
(`reports/ibtracs/2026-11-01-phase-4-writeup.md`); the tool, its guards and both harnesses'
wiring, decision 0023; the radar rows the design came from, `docs/radar.md`.
