# heat-basis-v1

Questions about a parametric heat policy over real station data, with exact answers (decisions 0012
and 0013).

## What an item asks

One season from 2015 to 2024, a cover window of 1 May to 30 September, a whole-degree threshold from
100 to 115 F and one question: the index station's trigger days, the events the policy pays (runs of
at least 2 to 5 consecutive trigger days), or the missed days, when the site was at or above the
threshold and the index was not. That last one is the policyholder's side of basis risk; days the
index paid while the site was not hot are not asked. 100 items per question, seed 2026.

The index stations are two Phoenix-area airports (Scottsdale Municipal and Phoenix Deer Valley
Municipal). The insured sites are in the hotter urban core (Phoenix Sky Harbor and Tempe ASU), 20.7
to 32.3 km away. The prompt shows both stations' daily maxima in whole degrees F, a dash for a
missing value, the year left out, and the rule for the question. The reply must end with `ANSWER:
<number>`.

The held-out split goes by season, so every station's readings for a season fall on one side:
`HeatConfig(split="train")` loads 245 items and `split="test"` 55, the 2017 and 2020 seasons
(decision 0017).

## Reward

`heat_basis_v1/contract.py`: 1 for the exact count, else 0.

## How to run

From the repo root, with a model behind an OpenAI-compatible server for `vf-eval`:

    uv run vf-eval heat-basis-v1 --no-push -m <model> --env.agent.runtime.type subprocess \
      --client.base-url http://127.0.0.1:8080/v1
    uv run inspect eval src/earthgym/heat/tasks.py@heat_basis --model <provider/model>
    uv run vf-validate heat-basis-v1 --runtime.type subprocess   # the gold check
    uv run python -m earthgym.heat.data                          # about 2.9 MB of pinned station files
    uv run python -m earthgym.heat.items                         # rebuild the items

`-T rules=false` shows the policy terms alone. The items' sha256 is in
`reports/heat/items_v1_manifest.json`.

## Data and licence

GHCN-Daily, NOAA NCEI. NOAA's metadata page asks for two citations and disclaims any warranty, and
it names no licence. `heat_basis_v1/NOTICE` carries the citations and that disclaimer. The code is
MIT (`LICENSE`). Whether the items, which show these stations' values, can go public is still my
decision to make (`docs/roadmap.md`).

## Known limits

Saturated for a strong model with the rules shown: I keep that version as the control for the
terms-only ablation and for small-model curricula
(`reports/heat/2026-11-01-rules-shown-vs-terms-only.md`). The missing-value rules change a key only
at Deer Valley in 2019, the one index season with gaps.
