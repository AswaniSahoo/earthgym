# 0009: what a Phase 4 task asks

Date: 2026-11-01. Status: accepted 2026-11-01: option 1, for three reasons: a distinct skill
from Phase 3, an exact verifier, and real traps.

Context: stage 1 gave reference code that reproduces NCEI's published North Atlantic season
numbers from a pinned IBTrACS file (`reports/ibtracs/2026-11-01-ncei-reproduction.md`). The
radar found no environment that grades exact answers computed from IBTrACS; the nearest
(ClimateAgent's cyclone tasks) grades written reports with a judge model (`docs/radar.md`).
The traps that break exact answers are domain rules: only 00, 06, 12 and 18 UTC rows count
for ACE (summing the 3-hourly interpolated rows doubles it), only some statuses count, and
spur tracks and provisional seasons are left out.

Options:

1. Per-storm analytics. A prompt gives one storm's IBTrACS rows (time, position, USA status,
   wind and pressure), with the 3-hourly rows left in as the archive has them, and asks one
   question: its ACE, its peak Saffir-Simpson category, its hours at hurricane strength, or
   whether it reached major hurricane strength. The answer key comes from the stage 1 code;
   the reward is 1 for an exact answer (ACE to one decimal), else 0. This tests the NOAA
   rules and careful counting on real tracks.
2. Intensity forecasts. A prompt gives a storm's track up to a time and asks for its wind 24
   or 48 hours later, rewarded by skill over persistence as in Phase 3 (0007). This repeats
   Phase 3's design on another variable.

Proposal: option 1, North Atlantic storms from final (non-provisional) seasons, a few hundred
items drawn by a seeded sample, every answer rule written in the prompt or left to the model
by question type (to be fixed with the first tests). A verifiers taskset and an Inspect task,
tested on mockllm only; no paid run without a yes.

Decision: option 1. The counting rules go in the prompt: only the synoptic rows at 00, 06,
12 and 18 UTC count, which statuses count, the units (knots), ACE as the sum of
(v/10^4) * v over the qualifying rows, and rounding to one decimal, with a tolerance I choose
and test in stage 2. The same items with the rules left out ("rules hidden") are a later
ablation.

Consequences: each question type needs its rule tested against hand-computed tracks first,
and against NCEI where a published number exists.
