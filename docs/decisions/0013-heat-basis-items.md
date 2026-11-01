# 0013: heat-basis-v1, a parametric heat policy's payouts and basis risk, exact answers

Date: 2026-11-01. Status: accepted, our design under 0012; the Fable review of Phase 5 checks
it.

Context: stage 1 reproduces NWS Phoenix's published heat counts from the pinned GHCN-Daily file
(`reports/heat/2026-11-01-nws-phoenix-reproduction.md`). Real heat covers count days at or above
a threshold at one weather station and runs of consecutive such days (docs/radar.md). Basis
risk is the heat the policyholder has that the index does not record.

Stations (GHCN-Daily, pinned in `src/rlenv/heat/data.py`, all with daily TMAX from 2015):

- Index stations, regional airports: Scottsdale Municipal Airport (USW00003192) and Phoenix Deer
  Valley Municipal Airport (USW00003184).
- Insured sites in the urban core: Phoenix Sky Harbor (USW00023183, the reproduced station) and
  Tempe ASU (USC00028499, a cooperative station with gaps, 13 to 39 missing days a season).
- The four pairs are 20.7 to 32.3 km apart (great-circle distance from ghcnd-stations.txt). The
  core is hotter than the airports: with Scottsdale as the index, Sky Harbor has 7 to 42 days a
  season at 110 F or more that the index misses. With Sky Harbor as the index, the airports
  missed almost none, so the airports are the index.
- Every TMAX value in the seasons used is the exact image of a whole degree F
  (`stats.tenths(stats.fahrenheit(v)) == v` for all 5,861 values), so the prompt can show whole
  degrees and the keys can compare in GHCN's unit with the same result.

Items:

- Seasons 2015 to 2024; the cover window is 1 May to 30 September (153 days); thresholds are
  whole degrees from 100 to 115 F; an event needs k of 2 to 5 consecutive trigger days.
- Three questions, 100 items each, drawn without repeats with seed 2026: trigger days (index,
  season, threshold), events (index, season, threshold, k) and missed days (index, site, season,
  threshold). For the first two the site column is shown as well, as a distractor.
- Prompt: both stations' daily maxima in whole degrees F for the window, the date as month and
  day with the year left out, a dash for a missing value; the stations named; then the rules
  and the question, and the answer line 'ANSWER: <number>'.
- Rules in the prompt: a trigger day has the index maximum at or above the threshold; a missing
  value is never a trigger day and ends a run; an event is a run of at least k consecutive
  trigger days and pays once however long it lasts; a missed day has the site at or above the
  threshold while the index is not, a missing index value counting as not, and a missing site
  value is never a missed day.
- Reward 1 for the exact integer, else 0.

Baselines in the report, exact from the reference code: the best constant answer per question,
and careless readings: trigger days strictly above the threshold, or counted on the site's
column; events counted as trigger days, as every run whatever its length, or with missing days
skipped; missed days counted both ways, as every hot site day, or with missing index days left
out.

Terms-only ablation (2026-11-01, asked for by lfx-prep-b7 when the 6-item probe scored 6 of
6): the same items with the policy terms alone, worded as a term sheet would put them ("the
index station's maximum reaches T F", "an event is k or more consecutive trigger days", "the
insured site's maximum reaches T F but the index station's does not"). The threshold and k
stay, since the questions need them; the clarifying rules go: at or above, missing values,
and paying once however long an event lasts. `-T rules=false`, reported side by side.

Out, for later: other cities, heat index or wet-bulb triggers, money amounts and
deductibles.

Consequences: answers are exact, the basis risk is real station data, and the careless
readings measure how often each rule changes the answer. Measured on the 300 items
(`rlenv.heat.report.careless`, items sha256 9d72cd64): strictly above the threshold is
right on 7 of 100 trigger-day items and the site's column on 3; for events, trigger days
on 3, every run on 9, missing days skipped on 99; for missed days, every hot site day on 2,
both ways on 71, missing index days left out on 92. The airport index stations have few
gaps, so the missing-value rules rarely change an answer; the report says so.
