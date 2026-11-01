# 0011: ibtracs-storm-v1, per-storm questions with exact answers

Date: 2026-11-01. Status: accepted, our design under 0009; the Fable review of Phase 4 checks
it.

Context: 0009 chose per-storm analytics with the counting rules in the prompt. The reference
code reproduces NCEI's published North Atlantic numbers (`tests/test_ibtracs_reproduction.py`:
season counts, ACE, and 2024's two category 5 hurricanes from NCEI's 202413 summary table).

Items:

- Storms: North Atlantic storms in the pinned build (sha256 666681be), seasons 1980 to 2025.
  2026 is left out because its rows are PROVISIONAL. Before 1980 many 3-hourly rows have no
  wind or status (4,082 blank winds in named storms over all seasons, 34 blank winds or
  statuses in 40,769 rows from 1980 to 2024), and a blank would need a rule of its own.
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
- Rules in the prompt: ACE squares the wind of each row at 00, 06, 12 or 18 UTC whose status
  is TS, HU or SS and whose wind is 34 kt or more, sums the squares and divides by 10^4,
  rounded to one decimal. Peak category is the highest wind on any HU row, at any time, on
  NHC's scale (64 to 82 kt is 1, 83 to 95 is 2, 96 to 112 is 3, 113 to 136 is 4, 137 or more
  is 5). Hours at hurricane strength count 6 for each row at 00, 06, 12 or 18 UTC with status
  HU.
- Reward 1 or 0. ACE is right when the answer is within 0.05 of the exact value (kept to four
  decimals): that accepts either rounding of a value that ends in 5 at the second decimal, and
  the unrounded value, and rejects a wrong rounding. Category and hours must match exactly.
- Answer parser: the last line 'ANSWER: <number>', horizontal space only, an optional full
  stop, as in Phase 3.

Baselines in the report, all exact from the reference code: the most common key per question
(a constant answer), and one careless reading per question that each rule exists to stop:
ACE over every row (the 3-hourly rows double it), ACE ignoring status (extratropical rows
count), category from the highest wind ignoring status, and hours over every HU row.

Out, for later: the "rules hidden" ablation (the same items with the rules left out),
other basins, storms before 1980.

Consequences: answers are exact, so a reply is right or wrong with no judge. The careless
baselines measure how often each trap changes the answer on these storms. Measured on the
300 items (`rlenv.ibtracs.report.careless`): ACE over every row is right on 0 of 100, ACE
ignoring status on 56, hours over every HU row on 1. For peak category the traps barely
bite: ignoring status is right on all 100, synoptic rows only on 96, so that question is
mostly a control for reading the scale. Dropping the year
does not stop a model from recognizing a famous track; Limits will say so.
