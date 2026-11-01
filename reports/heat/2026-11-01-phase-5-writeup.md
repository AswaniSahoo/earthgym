# Where a heat policy misses the heat: an exact-answer basis-risk environment

Phase 5 of earthgym, written up on 2026-11-01. Every number below comes from a file in this repo;
the source is named next to it.

## The question

A parametric heat policy pays from one weather station's readings: when the index station's
daily maximum reaches a threshold, the policy pays, whatever the policyholder actually lived
through. The heat the policyholder has and the index does not record is basis risk. Can a
language model read a policy's terms against real station data and count the trigger days,
the payouts, and the days the index missed?

## The published numbers first

The counting code had to reproduce published heat counts before any item was written. From the
pinned GHCN-Daily file for Phoenix Sky Harbor it gives every NWS Phoenix figure I checked on
the live pages: 55 days at 110 F or more in 2023, 133 at 100 F and 185 at 90 F, the 119 F high
on 19, 20 and 25 July, and the 31-day run of 110 F days from 30 June to 30 July; 70 days at
110 F in 2024 and a 113-day run at 100 F; 145 days at 100 F in 2020
(`reports/heat/2026-11-01-nws-phoenix-reproduction.md`).

## The environment

`heat-basis-v1` pairs an index station at a regional airport, Scottsdale Municipal or Phoenix
Deer Valley Municipal, with an insured site in the urban core, Phoenix Sky Harbor or Tempe ASU,
20.7 to 32.3 km apart (decision 0013). Sky Harbor was the first choice for the index, but it is
the hottest station around, so almost nothing was missed against it; with Scottsdale as the
index, Sky Harbor has 7 to 42 days a season at 110 F that the index misses. Each of the 300
items is one season from 2015 to 2024, a cover window of 1 May to 30 September, a threshold
from 100 to 115 F and one question: the index station's trigger days, the payout events (runs
of at least 2 to 5 consecutive trigger days), or the missed days. Answers are exact integers.

How often each careless reading is right (`reports/heat/2026-11-01-claude-sonnet-5-5.md`,
baseline rows): trigger days counted strictly above the threshold, 7 of 100; on the site's
column, 3; events counted as trigger days, 3; as blocks of k days, 38; missed days counted both
ways, 71; every hot site day, 2. Two readings barely bite, because the airport stations have
few gaps: a missing index value changes a key only at Deer Valley in 2019, on 8 missed-days
items and 1 events item.

## Results

Claude Sonnet 5.5, through the Batch API, once with the rules in the prompt (the control) and
once with the policy terms alone, worded as a term sheet would put them
(`reports/heat/2026-11-01-rules-shown-vs-terms-only.md`):

| question | rules shown | terms only |
|---|---|---|
| trigger days | 1.000 | 0.990 |
| events | 1.000 | 1.000 |
| missed days | 0.960 | 0.890 |
| all 300 | 0.987 | 0.960 |

- With the rules shown, all four misses are one extra day on a missed-days count.
- With the terms alone, the model reads "reaches 110 F" as at or above and pays each event once
  without being told. Missed days fall to 0.89, and 7 of the 8 items where a missing index value
  decides the key, all Deer Valley 2019, took the other reading of that missing value: a
  convention the terms leave open, not a counting skill (decision 0013).
- No reply names a season (0 of 600), so the answers were counted, not recalled.

## What this means for RL

As built, the environment is saturated for a model as strong as Sonnet 5.5, with the rules or
with the terms alone, and the one gap that remains sits on one station-season. My untested guess is that
a policy would take that convention from the reward in a few steps. Harder versions are in decision 0013's
later list: an index with gaps in more than one season, the insurer's side of basis risk (days
the index paid while the site was not hot), money amounts and deductibles, heat index triggers,
and other cities.

## Cost

$1.8801 for the rules-shown run and $1.9036 for the terms-only run, 300 items each, at the Batch
API's half price and without prompt caching (`reports/spend.md`).

## Limits

- One run per condition, no seed: the run-to-run spread is not measured.
- Four stations in one metro area, ten seasons, and the policyholder's side of basis risk only.
- NOAA names no licence for GHCN-Daily, and the pinned station files live only on this machine,
  since NCEI rewrites them daily; with the terms unclear they are not published (decision 0018).

## Reproduce

    uv run python -m earthgym.heat.data             # the pinned station files, about 2.9 MB
    uv run pytest tests/test_heat_reproduction.py
    uv run inspect eval src/earthgym/heat/tasks.py@heat_basis \
        --model anthropic/claude-sonnet-5-5 --batch --cache-prompt false [-T rules=false]
    uv run python -m earthgym.heat.report <shown log dir> --hidden <terms log dir> --out <pair>.md

Sources: GHCN-Daily (NOAA NCEI, doi:10.7289/V5D21VHZ); NWS Phoenix's 2023 climate summary and
its extreme temperatures page.
