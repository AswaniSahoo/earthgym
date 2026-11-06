# 0013: heat-basis-v1, a parametric heat policy's payouts and basis risk, exact answers

Date: 2026-11-01. Status: accepted, 2026-11-01: my design under decision 0012, checked by the
Phase 5 review.

Context: stage 1 reproduces NWS Phoenix's published heat counts from the pinned GHCN-Daily file
(`reports/heat/2026-11-01-nws-phoenix-reproduction.md`). Real heat covers count days at or above
a threshold at one weather station and runs of consecutive such days (docs/radar.md). Basis
risk is the heat the policyholder has that the index does not record.

Stations (GHCN-Daily, pinned in `src/earthgym/heat/data.py`, all with daily TMAX from 2015):

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
out. The Phase 5 review (L1) added the readings the terms-only wording leaves open: events as
blocks of k days, runs longer than k, runs of exactly k; missed days with the site strictly
above the threshold, and the other way round (the index hot while a site value is present and
below the threshold).

Terms-only ablation (2026-11-01, which I asked for when the 6-item probe scored 6 of 6): the same
items with the policy terms alone, worded as a term sheet would put them ("the index station's
maximum reaches T F", "an event is k or more consecutive trigger days", "the insured site's maximum
reaches T F but the index station's does not"). The threshold and k stay, since the questions need
them; the clarifying rules go: at or above, missing values, and paying once however long an event
lasts. `-T rules=false`, reported side by side.

Terms-only result (2026-11-01, `reports/heat/2026-11-01-rules-shown-vs-terms-only.md`): 0.960
against the control's 0.987. Trigger days (0.99) and events (1.00) stay at the ceiling;
missed days fall from 0.96 to 0.89. The model misses 7 of the 8 items where a missing index value
decides the key, all Deer Valley 2019: on 6 its answer is the other reading, on the seventh one
day from it.

Out, for later: other cities, heat index or wet-bulb triggers, money amounts and
deductibles, a pairing whose index has gaps in more than one season, and the insurer's side
of basis risk (days the index paid while the site was not hot) as a fourth question; the last
two change the design (Phase 5 review, M3).

Consequences: answers are exact, the basis risk is real station data, and the careless
readings measure how often each rule changes the answer. Measured on the 300 items
(`earthgym.heat.report.careless`, items sha256 9d72cd64): strictly above the threshold is
right on 7 of 100 trigger-day items and the site's column on 3; for events, trigger days
on 3, every run on 9, missing days skipped on 99; for missed days, every hot site day on 2,
both ways on 71, missing index days left out on 92. The airport index stations have few
gaps: in the ten windows one day at Scottsdale (2022-09-12), one at Deer Valley (2017-09-20)
and 21 at Deer Valley in 2019. So the missing-index rule changes 8 of the 100 missed-days keys
and the missing-day rule 1 of the 100 events keys, all Deer Valley 2019, and another seed
could draw none; the reports name the place. The missed-days question asks the
policyholder's side of basis risk only.
