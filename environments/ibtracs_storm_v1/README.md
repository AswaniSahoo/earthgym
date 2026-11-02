# ibtracs-storm-v1

Saturated for a frontier model with the rules shown: Claude Sonnet 5.5 gets 299 of 300 items
right (0.997). I keep this version as the control for the rules-hidden ablation (0.703) and for
small-model curricula (`reports/ibtracs/2026-11-01-rules-shown-vs-hidden.md`).

Per-storm questions about North Atlantic tropical cyclones from IBTrACS, with exact answers
(decisions 0009 and 0011). Each of the 300 items is one storm from the 1980 to 2025 seasons and
one question: its accumulated cyclone energy (100 items), its peak Saffir-Simpson category (100)
or its hours at hurricane strength (100), drawn with seed 2026 from 613 eligible storms. The
prompt shows every row the archive has for the storm (the 6-hourly rows, the 3-hourly rows
between them and extra rows such as landfall), with the time as month, day and UTC hour, the
status, the wind in kt and the pressure in mb; no name, year or storm id. The rule for the
question is in the prompt. The reply must end with a line `ANSWER: <number>`.

Reward per item, from `ibtracs_storm_v1/contract.py`: 1 for a right answer, else 0. ACE is
right only at one decimal, as the exact value rounded or, when the exact value is a tie, either
neighbour; category and hours must match exactly (decision 0016).

A held-out split by storm: `StormConfig(split="train")` loads 233 items and `split="test"` 67
(decision 0017).

Tools mode, the first tool-using version in this repo (decision 0023): the prompt leaves out the
rows and the rule, and the model reads the storm's rows with one read-only SQL tool,
`query(sql)`, over an in-memory SQLite table `track(time, status, wind, pressure)`, then
answers with the same `ANSWER: <number>` line or, in this mode only, the number alone, paid by
the same reward. Its authorizer refuses every write and every file, a statement stops after
0.5 s, and a reply holds at most 200 rows and about 8,000 characters; besides the rows, a query
can read only the table's schema, the SQLite version and the clock. A first version, under
Inspect's `react()` agent, scored 0.747 on Claude Sonnet 5.5 against 0.703 with the rows in the
prompt (`reports/ibtracs/2026-11-02-rows-in-prompt-vs-tool-react.md`), but react's system prompt
is a second difference from the prompt runs; the tool loop's own run is not finished (decision
0023).

    uv run vf-eval ibtracs-storm-v1 --no-push -m <model> --env.taskset.tools true \
      --env.agent.harness.id null --env.agent.runtime.type subprocess --env.agent.max-turns 14
    uv run inspect eval src/earthgym/ibtracs/tasks.py@ibtracs_storm -T tools=true \
      --model <provider/model>

Every environment here defaults to verifiers' null harness, which runs no model-written code;
verifiers' own default, `bash`, would give the model a shell on the host. Both harnesses send the
user prompt and the one tool, with no system prompt and no submit tool, run the model's tool
calls in a loop and score its final reply, within 14 model turns: Inspect's `turn_limit`, and
`--env.agent.max-turns 14` in verifiers. `tests/test_vf_tools_rollout.py` runs the verifiers
command against a scripted endpoint.

The keys come from `src/earthgym/ibtracs/stats.py`, which reproduces NCEI's published North
Atlantic season numbers (`reports/ibtracs/2026-11-01-ncei-reproduction.md`).

Rebuild the items from the repo root, after `uv run python -m earthgym.ibtracs.data` has fetched
the pinned 57.6 MB CSV, from the repo's `data-v1` release or, failing that, from NCEI while it
still serves the pinned build (decision 0018; the items' sha256 is in
`reports/ibtracs/items_v1_manifest.json`):

    uv run python -m earthgym.ibtracs.items

Data: IBTrACS v04r01 (Knapp, Kruk, Levinson, Diamond and Neumann 2010, BAMS 91,
doi:10.1175/2009BAMS2755.1; Gahtan et al. 2024, NOAA NCEI, doi:10.25921/82ty-9e16), "full and
open access", with WMO Resolution 40 as the guide for commercial use.
