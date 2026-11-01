# Counting hurricanes by NOAA's rules: an exact-answer environment from IBTrACS

Phase 4 of earthgym, written up on 2026-11-01. Every number below comes from a file in this repo;
the source is named next to it.

## The question

Season totals of hurricane activity rest on counting conventions: accumulated cyclone energy
(ACE) sums squared winds only at the four synoptic hours and only while a storm is a tropical
or subtropical storm or a hurricane; the Saffir-Simpson category comes from the peak wind; and
hours at hurricane strength are counted in 6-hourly steps. The IBTrACS archive holds every
storm's track with 3-hourly interpolated rows and extra rows, such as landfall, in between, so
a careless count goes wrong in known ways. Can a language model apply the conventions to raw
archive rows?

## The reference code, checked first

Before any item was written, the counting code had to reproduce published numbers. From the
pinned North Atlantic IBTrACS file it gives NCEI's 1933 ACE of 258.6, 15 hurricanes and 7 major
in 2005, 30 named storms and 7 major in 2020, and 2024's 18 named storms, 11 hurricanes, 5
major, ACE 161.6 and 2 category 5 hurricanes (`reports/ibtracs/2026-11-01-ncei-reproduction.md`).

## The environment

`ibtracs-storm-v1` has 300 items from 613 eligible North Atlantic storms of 1980 to 2025, drawn
with seed 2026 (decision 0011): 100 ask a storm's ACE, 100 its peak category, and 100 its hours
at hurricane strength. The prompt shows every row the archive has for the storm, with no name
or year, then the rule for the question. Answers are exact: ACE at one decimal (scored within
0.05 of the exact value at the time; the stricter rounding rule of decision 0016 gives the same
scores), category and hours to the integer.

How often each careless reading gets an item right (`reports/ibtracs/2026-11-01-claude-sonnet-5-5.md`,
baseline rows): ACE summed over every row, 0 of 100 (the 3-hourly rows double it); ACE
ignoring status, 56; hours counted over every HU row, 1; hours with each row's status held
until the next row, 36. Two readings cannot bite on these storms: peak category ignoring
status is right on all 100, since a hurricane's status follows its wind.

## Results

Claude Sonnet 5.5, through the Batch API, once with the rules in the prompt (the control) and
once with them left out (`reports/ibtracs/2026-11-01-rules-shown-vs-hidden.md`):

| question | rules shown | rules hidden |
|---|---|---|
| ACE | 0.990 | 0.990 |
| peak category | 1.000 | 0.990 |
| hours at hurricane strength | 1.000 | 0.130 |
| all 300 | 0.997 | 0.703 |

- Told the rules, the model counts storm tracks almost perfectly; its one miss is a slip in
  the arithmetic (`docs/reviews/phase-4-ibtracs-storms.md`).
- Not told them, it still applies NOAA's ACE convention and the Saffir-Simpson scale: ACE and
  category stay at 0.99.
- Only hours fall, and 63 of the 87 misses follow a duration reading instead of my 6 hours per
  6-hourly row: the elapsed time of each hurricane spell, or each row's status held until the
  next row. That is a convention the question does not state, not a missing skill; the same
  storm, Keith in 2000, drew 75 hours in the probe and 71 in the full run.
- 2 of the 300 rules-shown replies and 4 of the rules-hidden ones name the storm or its
  season, so a famous track can be recognized even without its name.

## What this means for RL

As built, the environment gives a policy as strong as Sonnet 5.5 almost no signal: nearly
every rollout earns the same reward, with the rules shown or, for ACE and category, hidden.
It works as a regression check, and for weaker models. Harder versions are listed in decision
0011: season-level items with many storms to sum, storms that cross into another basin, spur
tracks, and a rapid-intensification count.

## Cost

$1.3626 for the rules-shown run and $1.7800 for the rules-hidden run, 300 items each, at the
Batch API's half price (`reports/spend.md`).

## Limits

- One run per condition, no seed: the run-to-run spread is not measured, and the Keith example
  shows it is not zero.
- The one-decimal ACE format pays 39 percent of single 5 kt misreads; two decimals would catch
  them and would make a rerun incomparable (decision 0011).
- The rule wording was made exact after the runs; 9 items turn on rows at a synoptic hour with
  minutes, and the model got all 9 right with the earlier wording.
- No item exercises the rules for other basins or spur tracks.

## Reproduce

    uv run python -m earthgym.ibtracs.data          # the pinned 57.6 MB CSV
    uv run pytest tests/test_ibtracs_reproduction.py
    uv run inspect eval src/earthgym/ibtracs/tasks.py@ibtracs_storm \
        --model anthropic/claude-sonnet-5-5 --batch [-T rules=false]
    uv run python -m earthgym.ibtracs.report <shown log dir> --hidden <hidden log dir> --out <pair>.md

Sources: IBTrACS v04r01 (Knapp, Kruk, Levinson, Diamond and Neumann 2010, BAMS 91,
doi:10.1175/2009BAMS2755.1; Gahtan et al. 2024, NOAA NCEI, doi:10.25921/82ty-9e16); NCEI's
annual tropical cyclone reports; NHC's Saffir-Simpson scale.
