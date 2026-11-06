# ibtracs-storm-v1

Per-storm questions about North Atlantic tropical cyclones from IBTrACS, with exact answers
(decisions 0009 and 0011).

## What an item asks

One storm from the 1980 to 2025 seasons and one question: its accumulated cyclone energy (100
items), its peak Saffir-Simpson category (100) or its hours at hurricane strength (100), drawn with
seed 2026 from 613 eligible storms. The prompt shows every row the archive has for the storm (the
6-hourly rows, the 3-hourly rows between them and extra rows such as landfall), with the time as
month, day and UTC hour, the status, the wind in kt and the pressure in mb; no name, year or storm
id. The rule for the question is in the prompt. The reply must end with a line `ANSWER: <number>`.

The held-out split goes by storm: `StormConfig(split="train")` loads 233 items and `split="test"` 67
(decision 0017).

In tools mode, the first tool-using version in this repo (decision 0023), the prompt leaves out the
rows and the rule. The model reads the rows with one read-only SQL tool, `query(sql)`, over an
in-memory SQLite table `track(time, status, wind, pressure)`. Its authorizer refuses every write and
every file, a statement stops after 0.5 s, and a reply holds at most 200 rows and about 8,000
characters; besides the rows, a query can read only the table's schema, the SQLite version and the
clock. Both harnesses send the user prompt and the one tool, with no system prompt and no submit
tool, run the model's tool calls in a loop and score its final reply, within 14 model turns:
Inspect's `turn_limit`, and `--env.agent.max-turns 14` in verifiers.

## Reward

`ibtracs_storm_v1/contract.py`: 1 for a right answer, else 0. ACE is right only at one decimal, as
the exact value rounded or, when the exact value is a tie, either neighbour; category and hours must
match exactly (decision 0016). Tools mode pays the same, and accepts the number alone as well as the
answer line. The keys come from `src/earthgym/ibtracs/stats.py`.

## How to run

From the repo root, with a model behind an OpenAI-compatible server for `vf-eval`:

    uv run vf-eval ibtracs-storm-v1 --no-push -m <model> --env.agent.runtime.type subprocess \
      --client.base-url http://127.0.0.1:8080/v1
    uv run inspect eval src/earthgym/ibtracs/tasks.py@ibtracs_storm --model <provider/model>
    uv run vf-validate ibtracs-storm-v1 --runtime.type subprocess   # the gold check
    uv run python -m earthgym.ibtracs.data                          # the pinned 57.6 MB CSV
    uv run python -m earthgym.ibtracs.items                         # rebuild the items

`-T rules=false` hides the rule. For tools mode, add `-T tools=true` to Inspect, and
`--env.taskset.tools true --env.agent.max-turns 14` to `vf-eval`; `tests/test_vf_tools_rollout.py`
runs that verifiers command against a scripted endpoint.

The data step fetches the CSV from the repo's `data-v1` release or, failing that, from NCEI while it
still serves the pinned build (decision 0018). The items' sha256 is in
`reports/ibtracs/items_v1_manifest.json`.

## Data and licence

IBTrACS v04r01, "full and open access", with WMO Resolution 40 as the guide for commercial use;
`ibtracs_storm_v1/NOTICE` carries the citations. The code is MIT (`LICENSE`).

## Known limits

Saturated for a strong model with the rules shown: I keep that version as the control for the
rules-hidden ablation and for small-model curricula
(`reports/ibtracs/2026-11-01-rules-shown-vs-hidden.md`). Tools mode's own run is not finished
(`reports/ibtracs/2026-11-02-phase-6-writeup.md`).
