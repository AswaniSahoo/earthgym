# 0011: ibtracs-storm-v1, per-storm questions with exact answers

Date: 2026-11-01. Status: accepted, our design under 0009; the Fable review of Phase 4 checks
it.

Context: 0009 chose per-storm analytics with the counting rules in the prompt. The reference
code reproduces NCEI's published North Atlantic numbers (`tests/test_ibtracs_reproduction.py`:
season counts, ACE, and 2024's two category 5 hurricanes from NCEI's 202413 summary table).

Items:

- Storms: North Atlantic storms in the pinned build (sha256 666681be), seasons 1980 to 2025.
  2026 is left out because its rows are PROVISIONAL. Before 1980 many 3-hourly rows have no
  wind or status (4,082 blank winds in the NA rows of named storms over all seasons, 34 blank
  winds or statuses in 40,769 rows from 1980 to 2024), and a blank would need a rule of its
  own.
- Each storm: every row in the NA basin (a storm with any row elsewhere is left out), no spur
  track, no row with a blank wind or status, and named (34 kt as TS, HU or SS).
- Three questions, one per storm, 100 storms each, drawn with a seeded sample (seed 2026): ACE
  over the named storms; peak Saffir-Simpson category and hours at hurricane strength over the
  storms with an HU row at 64 kt or more, since a storm that never was a hurricane answers 0
  to both. ACE is drawn first, from all 613 eligible storms, so its sample keeps the
  population's share of hurricanes (median 56 rows against 53 for all eligible named storms);
  the other two draw from the hurricanes left. Items: 300, sha256 75fe4ff2
  (`reports/ibtracs/items_v1_manifest.json`).
- Prompt: every row of the storm in archive order (the 3-hourly interpolated rows and the
  extra rows at other times, such as landfall, stay in), with time as month, day and UTC
  hour, status, wind (kt) and pressure (mb). No name, year, SID, latitude or longitude, so a
  model has to count rather than recall a published value. Then the rule for the question
  asked, a legend of the statuses, and the answer line 'ANSWER: <number>'.
- Rules in the prompt: ACE squares the wind of each row at exactly 00:00, 06:00, 12:00 or
  18:00 UTC (a row at 12:30 does not count) whose status is TS, HU or SS and whose wind is 34 kt
  or more, sums the squares and divides by 10^4, rounded to one decimal. Peak category is the
  highest wind on any HU row, at any time, on NHC's scale (64 to 82 kt is 1, 83 to 95 is 2, 96
  to 112 is 3, 113 to 136 is 4, 137 or more is 5); a storm with no HU row at 64 kt or more is 0.
  Hours at hurricane strength count 6 for each row at exactly those times with status HU. The
  exact wording landed after the runs (Fable review M1): the runs said "at 00, 06, 12 or 18
  UTC", 9 items turn on rows at a synoptic hour with minutes, and Sonnet 5.5 got all 9 right.
- Reward 1 or 0. ACE is right only at one decimal: the exact value (kept to four decimals)
  rounded, or either neighbour when the exact value ends in 5 at the second decimal and 0 after
  it. Until 2026-11-02 the rule was within 0.05 of the exact value, which also paid two-decimal
  and unrounded answers; re-grading the runs by the new rule changes no score (decision 0016).
  Category and hours must match exactly.
  We keep NOAA's one-decimal format (Fable review M2): it can never pay a wrong choice of rows,
  since the smallest qualifying row adds 0.1156, but a single 5 kt misread of one wind still
  pays on 1,578 of 4,026 such perturbations (39 percent, on 97 of 100 items). Asking for two
  decimals with a tolerance of 0.005 would catch every such misread; it is a one-line change
  if exactness is wanted, and it would make a rerun incomparable with these runs. Kept at
  one decimal by lfx-prep-b7 on 2026-11-01, so the runs stay comparable.
- Answer parser: the last line 'ANSWER: <number>', horizontal space only, an optional full
  stop, as in Phase 3; Markdown emphasis removed and finite numbers only (decision 0016).

Baselines in the report, all exact from the reference code: the most common key per question
(a constant answer), and the careless readings each rule exists to stop: for ACE, every row
(the 3-hourly rows double it), ignoring status (extratropical rows count), and TS and HU only
(no SS); for peak category, ignoring status, synoptic rows only, and NHC's mph thresholds read
as kt; for hours, every HU row, each row's status held until the next row, and the elapsed
time of each hurricane spell. The last three readings came with the Fable review (L3).

Rules-hidden ablation (2026-11-01, asked for by lfx-prep-b7 after the rules-shown run scored
0.997): the same items and prompts without the "Rule." paragraph, so the status legend,
units, rounding and question stay; `-T rules=false` on the Inspect task, `rules: false` in
the taskset config. The two runs are reported side by side (`rlenv.ablation`).

Rules-hidden result (2026-11-01, `reports/ibtracs/2026-11-01-rules-shown-vs-hidden.md`):
0.703 against 0.997. ACE (0.99) and peak category (0.99) stay at the ceiling with the rule
left out, so the model knows those conventions. Hours fall to 0.13, and the misses follow
duration readings ("6 hours per 6-hourly row" is our convention, not a published rule):
most are short by exactly 3 or 6 hours. We report the hidden hours as a convention test, not
a skill test, and do not rerun them with a unit sentence. Neither version gives an RL policy
of this strength a skill signal on ACE or peak category.

Out, for later: ACE to two decimals with a tolerance of 0.005 (the Fable review's M2), a
rapid-intensification question (NHC's glossary definition, tested on
hand-computed tracks first), the 13 storms that cross into another basin (with the rule that
only NA rows count), spur tracks, season-level items, other basins, storms before 1980. The
population carries two of the reproduction's rules, the synoptic hours and the statuses; the
basin and spur rules are exercised by no item and no anchor (Fable review L2).

Consequences: answers are exact, so a reply is right or wrong with no judge. The careless
baselines measure how often each trap changes the answer on these storms. Measured on the
300 items (`rlenv.ibtracs.report.careless`): ACE over every row is right on 0 of 100, ACE
ignoring status on 56, hours over every HU row on 1. For peak category the traps barely
bite: ignoring status is right on all 100, synoptic rows only on 96, so that question is
mostly a control for reading the scale. We keep it (2026-11-01): a rapid-intensification
count, whose careless readings would fail more often, needs its own verified rule and new
items, and goes to the later list. The report says on which questions a careless reading
is right on 90 or more of 100 items. Dropping the name and year does not stop a model from
recognizing a famous track: the report counts the replies that name the storm or its season.
