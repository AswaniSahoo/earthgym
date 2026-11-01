# Phase 5 review: heat-basis-v1, a parametric heat policy's payouts and basis risk over Phoenix-area stations

Reviewed 2026-11-01. The checks started at commit `87a951a` on `main` (tree clean); one commit
landed while the review ran, c6fd2b2, which adds SUMMARY.md and touches no code, so every check
below describes the same code at both commits. HEAD at writing is `c6fd2b2`, tree clean. Nothing
below is taken from memory; where a claim could not be checked it is marked UNKNOWN. No paid model
call was made by this review.

What was run: `uv run pytest -q` (243 passed at 87a951a and again at c6fd2b2; the data-backed
tests ran, since the four pinned station files are on disk with the pinned sha256 and sizes),
`uv run ruff check .` (clean), `uv run ruff format --check .` (138 files, clean), `uv lock
--check` (clean), `gh run list` (green on every Phase 5 commit from 708dfec through c6fd2b2),
`uv run vf-validate heat-basis-v1 --only-noop --runtime.type subprocess` (300 of 300 valid), the
CI mockllm eval with the rules and with `-T rules=false` (both success, revision c6fd2b2 with
`dirty=False`; the "Rule." paragraph in 3 of 3 prompts of the first, "Policy terms." in 3 of 3 of
the second), `uv build environments/heat_basis_v1` into scratch (the wheel is 74,236 bytes and
holds the 936,981 byte jsonl; METADATA has `Requires-Python: >=3.12` and `verifiers<0.5,>=0.4.0`
and no license field), the report pipeline for both runs and for the pair (`uv run python -m
rlenv.heat.report <log dir> --out <scratch>` and `--hidden`: all three markdown files and both
JSON files byte-identical to the committed reports), `uv run --with pytest-cov pytest` over the
Phase 5 tests (89 percent of lines in the Phase 5 modules, 333 statements, 38 missed; contract,
taskset, policy and stats at 100 percent), and the four logs on this machine read with
`inspect_ai.log.read_eval_log`. The anchors, all 300 keys, the careless readings and the
population claims of 0013 were recomputed by a pure standard library script that reads the four
gz files directly and transcribes the rules from the prompt text, without importing `rlenv.heat`.
Sources read at their root today: weather.gov/psr/yearinreview2023 (curl, and Firecrawl on a
retry; the page's table uses non-breaking spaces, which is why a plain grep for "DAYS MAX" finds
nothing), weather.gov/psr/ExtremeTemps (Firecrawl), NCEI's ghcnd-stations.txt (curl, 11,441,526
bytes), ghcnd-version.txt, an HTTP HEAD of the Sky Harbor by_station file, and Anthropic's
pricing page (curl). Pins in `uv.lock`: `inspect-ai 0.3.286`, `anthropic 2.3.0`, `verifiers
0.4.0`; `hatchling==1.33.0` in the package (0014). No em or en dash in any Phase 5 prose file or
module.

Spot checks against the raw data:

- Anchors, independently from `USW00023183.csv.gz` (32,222 TMAX values, 1933-06-01 to
  2026-10-28, one QC-flagged TMAX row in the whole file, none in 2020, 2023 or 2024, and no
  missing day in those years). 2023: 55 days at 110 F or more, 133 at 100, 185 at 90; the
  highest value is 483 tenths of a degree C, 118.94 F, shown as 119, first on 07-19 and again
  on 07-20 and 07-25; the longest run at 110 is 31 days, 06-30 to 07-30. 2024: 70 days at 110;
  the longest run at 100 is 113 days, 05-27 to 09-16. 2020: 145 days at 100. The radar's
  "DAYS MIN >= 90 35" (not in the report) also reproduces from TMIN. The conversion rule
  matters: rounding gives 55 days at 110 in 2023, flooring 50, ceiling 62; and every 2023 value
  is the image of a whole degree F.
- Live pages today. yearinreview2023, CLIMATE REPORT issued "712 AM MST TUE JAN 02 2024":
  "DAYS MAX >= 90 185", "DAYS MAX >= 100 133", "DAYS MAX >= 110 55", "DAYS MIN >= 90 35",
  "HIGHEST 119 07/19 07/20 07/25", "CLIMATE RECORD PERIOD 1895 TO 2024". ExtremeTemps, Phoenix
  column, "Period of Record (POR) (1896-2025)": "Greatest number of 100° F or greater days 145
  (2020)", "Longest stretch of 100° F or greater days 113 (27 May 2024 - 16 Sep 2024)", "Greatest
  number of 110° F or greater days 70 (2024)", "Longest stretch of 110°F or greater days 31 (30
  Jun 2023 - 30 Jul 2023)". Every published value in 0012 and the reproduction report is there.
- The source today. HEAD of the live Sky Harbor file: `Last-Modified: Sun, 01 Nov 2026 00:01:02
  GMT`, `Content-Length: 1479584`, the same as the pin, so the pinned build was still the one
  served at review time. `ghcnd-version.txt` reads "3.35-upd-2026103017" over
  "3.35-por-2026102323"; the radar row quotes 2026102917, so which update built the pinned files
  is UNKNOWN (L5).
- Keys. The independent transcription equals the bundled key on 300 of 300 items; every
  `index_f` and `site_f` list equals the raw file's values in whole degrees F, with None where
  the file has no row or a QC flag; the seeded draw (`random.Random(2026)` over the three grids
  of 320, 1,280 and 640 specs) reproduces the 300 ids in order; the 5,861 values in the 40
  station-seasons are all whole-degree images (0013's number). One QC-flagged TMAX row sits
  inside the windows (Deer Valley, 2017-09-20, 244 tenths, flag S) and is shown as a dash. Key
  ranges: trigger days 1 to 108 (57 distinct values; the best constant 5 is right on 5), events 0
  to 14 (0 on 27), missed days 0 to 47 (3 on 9). Items with any missing index value: 15 trigger,
  11 events, 21 missed days; with a missing site value: 49, 52, 49.
- Population claims in 0013. Tempe ASU's missing days per window, 2015 to 2024: 23, 29, 20, 39,
  36, 18, 13, 17, 23, 18 (the "13 to 39"). The airports: Scottsdale 1 missing day in ten seasons
  (2022-09-12), Deer Valley 1 (2017-09-20, the flagged value) and 21 in 2019 (06-08 to 06-12,
  06-16, 07-20, 07-21, 07-24, 07-26 to 07-29, 08-03, 08-04, 08-06, 08-11, 08-12, 08-16 to
  08-18); Sky Harbor none. Missed days at 110 with Scottsdale as index and Sky Harbor as site:
  11, 18, 11, 12, 16, 25, 7, 9, 25, 42 (the "7 to 42"); with Sky Harbor as index and an airport
  as site, at most 1 missed day over every threshold and season (the "almost none"). Distances
  by haversine from today's ghcnd-stations.txt: Scottsdale to Tempe 20.75 km, to Sky Harbor
  21.82; Deer Valley to Sky Harbor 29.76, to Tempe 32.33 (the "20.7 to 32.3").
- Careless readings, independently: strictly above 7, the site's column 3; trigger days not
  events 3, every run 9, missing days skipped 99; every hot site day 2, both ways 71, missing
  index days left out 92, all equal to 0013 and the reports. The missing-index rule changes the
  key on 8 of the 100 missed-days items, and all eight are Deer Valley 2019; the "missing days
  skipped" reading changes 1 of 100 events keys. Readings the report does not have: events as
  non-overlapping blocks of k days (the floor of run over k) right on 38, runs strictly longer
  than k 50, runs of exactly k 30, every window of k days 30, a missing day bridged as hot 94,
  events on the site's column 26; missed days with the site strictly above the threshold 13, the
  other way round (index hot, site not) 5, days the site was hotter than the index 0; trigger
  days with either station hot 5.
- The rules-shown log against the items and the contract. Status success, 300 samples,
  `task_args {'path': None, 'rules': True}`, revision 6306bf4 with `dirty=False`, config
  `cache_prompt False, batch 100`; the logged request has `max_tokens 32000`, `thinking
  {"type": "adaptive", ...}`, no `cache_control`, and the response says `service_tier batch`.
  All 300 `Sample.input` values equal `contract.prompt(item)`; every metadata key equals the
  bundled key; the logged score equals `contract.reward(contract.answer(completion), key)` on all
  300; 0 parse failures; stop reason `stop` on 300; accuracy 0.986667, stderr 0.006633; per
  question 1.00, 1.00, 0.96. Tokens 625,516 input, 0 cache write, 0 cache read, 250,923 output,
  153,313 reasoning, and the 300 per-sample usages sum to the log totals; cost $1.880131 at the
  ledger's prices with the batch halving ($0.006267 an item). Reasoning tokens on 253 of 300
  replies (79 of 100 trigger days, 78 events, 96 missed days); median output 889.5 tokens,
  maximum 1,678. The contract file last changed at 6e0c48a, before either run, and the jsonl at
  de89c52, so both logs' prompts equal HEAD's contract.
- The terms-only log. Success, 300 samples, `rules False`, revision bb6fd9b `dirty=False`,
  `cache_prompt False, batch 100`; all 300 inputs equal `contract.prompt(item, rules=False)`;
  keys and scores equal the contract on 300; 0 parse failures; accuracy 0.960000, stderr
  0.011333; per question 0.99, 1.00, 0.89. Tokens 618,216 input, 257,075 output, 160,216
  reasoning; cost $1.903591. Reasoning on 267 of 300; median output 895.5, maximum 1,959.
  `report.py` changed by one line after this run (87a951a) and the committed report is the
  re-render (identical today).
- The probes. Rules shown: 6 of 6, revision 708dfec, `batch 100` with Inspect's default caching
  still on (24 input and 12,447 cache-write tokens, as the ledger row says), $0.039403. Terms
  only: 5 of 6, revision b81449e, `cache_prompt False`, $0.035325; the miss is
  `missed_days/USW00003184/USC00028499/2019/107` (key 9, answer 3), which drew 2 in the full run.
- Recall. No reply in any of the four logs contains a four-digit year from 2010 to 2029, and
  every miss shows a day-by-day tally; the station names are in the prompt, so a "Phoenix" is
  not recall.
- Ledger. All twelve rows of `reports/spend.md` recompute from their token columns (the test
  does it; by hand the Phase 5 rows are 0.039403, 1.880131, 0.035325 and 1.903591) and the exact
  running totals are 3.494660, 7.190836, 7.226161 and 9.129752, printed as 3.4947, 7.1908,
  7.2262 and 9.1298. Pricing page today: Claude Sonnet 5.5 "$2 / MTok $10 / MTok $2.50 / MTok
  $4 / MTok $0.10 / MTok", the Batch API "50 percent discount on both input and output tokens",
  and the cache multipliers "stack with other pricing modifiers, including the Batch API
  discount".
- The misses, every one read against the item's rows. Rules shown, 4, all missed days, each
  one day too many, and in every case the extra day has both stations at or above the threshold
  with the site hotter than the index: `missed_days/USW00003184/USC00028499/2015/105` (key 9,
  answer 10; the extra day is 08-29, index 107, site 109, while the same reply says such days
  "are not missed days"); `.../USC00028499/2021/108` (18, 19; 06-13, 111 and 112, written
  "06-13 (112 vs 111)"); `.../USW00023183/2023/104` (32, 33; 08-01, 104 and 109);
  `missed_days/USW00003192/USW00023183/2024/104` (23, 24; 06-05, 106 and 108). Terms only, 12.
  Six equal the "missing index days left out" reading and say so in words: 2019/100 (18, 5),
  2019/106 with Tempe (16, 8), 2019/107 (9, 2), 2019/108 (9, 3), 2019/110 (3, 0) and 2019/113
  with Sky Harbor (8, 6), all Deer Valley 2019, with sentences such as "With no index reading on
  these dates, there is no evidence that the index failed to reach 108 °F. I have not counted
  them" and "Not determinable". A seventh, 2019/106 with Sky Harbor (35, 21), excluded the
  fifteen gap days too ("Fifteen further days have Sky Harbor at 106 F or above but no index
  reading") and added 08-02 (108 and 110), so it matches no reading by value. 2021/108 (18, 21)
  adds 06-13, 06-15 and 06-16 (111 and 112, 113 and 114, 112 and 115): the same item and the
  same 06-13 as in the shown run. 2017/112 (7, 10) adds 06-19, 06-20 and 06-21 (116 and 118, 117
  and 119, 116 and 117), marked "Yes" while 06-24 (113 and 116) is marked "No (index reached
  112)". 2024/104 (23, 24) adds 06-05 again, the same day as in the shown run. 2017/101 (16, 15)
  drops 07-25 (100 and 102). The one trigger-days miss, `trigger_days/USW00003192/USW00023183/
  2019/108` (31, 32), lists July right (1, then 7, then 4 days) and sums it to 13. So of the 16
  misses in the two full runs, 7 exclude the Deer Valley 2019 gap days (one with a slip on top),
  8 add one to three days on which both stations reached the threshold and the site was hotter,
  1 drops a day and 1 adds wrongly. Deer Valley is the index on 3 of the 4 and 11 of the 12. 92
  of the 100 missed-days items contain at least one day of the both-hot, site-hotter kind, so
  the slip has room on nearly every item.

## 1. Ratings

| Area | Score | Justification |
|---|---|---|
| Correctness | 9 | All 300 keys equal an independent transcription of the prompt's rules over the raw files, every shown value equals the archive, the eight anchors reproduce and are on the live pages, the 600 prompts in the two logs equal the contract, the logged scores equal the contract on every sample, the ledger adds up to the cent, and the items and the three reports regenerate byte for byte. The prompt states each rule exactly as the code applies it (at or above, missing never a trigger day and ends a run, one payment per run, a missing index value as not hot, a missing site value never missed, and the window is the rows shown). Against that: both run reports print a Phase 4 sentence ("on these storms ... choice of rows", M2), one trap match is a coincidence (M4), and the pair template's verdict clause does not fit this phase (M1). |
| Minimalism and clarity | 8 | 45, 45, 126, 82 and 68 lines for policy, stats, items, data and the Inspect task, a 79-line contract shared by both harnesses, stdlib only on the data path, the pair report shared with Phase 4 through `rlenv.ablation`. Clutter: `_spec` builds a dict with a pointless union (`items.py:32-36`), `report.careless` re-implements the policy in whole degrees (by design, as an independent check, but unsaid), the `TESTS` dict and Limits sentence are Phase 4 text with the nouns unchanged (`report.py:17-21,226-228`), and `src/` still imports the environment package (`report.py:11-12`, `tasks.py:11-12`). |
| Test coverage | 8 | Nine Phase 5 test files, 89 percent of lines, contract, taskset, policy and stats at 100, hand-computed tracks with every trap (a gap that splits a run, an index gap with a hot site, a flagged value), the bundled items rebuilt from the pinned files (what Phase 4's M4 asked for), both harnesses compared on 900 replies, the terms-only switch tested in the contract and both harnesses. Missing: `summarize`'s error path (`report.py:85,88-90`), the `main` functions, the readings in L1, any test that the rendered Limits name seasons rather than storms (M2), and the CI smoke covers only trigger-days prompts (L4). |
| Reproducibility | 9 | Four files pinned by sha256 with size and Last-Modified, the manifest with the station hashes and the seed, a test that rebuilds the 300 items byte for byte, reports that rebuild byte for byte from the logs, logs that name clean commits, `--cache-prompt false` on both full runs (Phase 4's L1), and the live file still equal to the pin at review time. Gaps: the source files exist only on this machine and NCEI rewrites them daily; the GHCN version string is not recorded beside the pins (L5). |
| CI/CD | 8 | Green on every Phase 5 push, actions pinned by commit, `--locked --all-groups`, `vf-validate`, the mockllm eval and the wheel build for this environment (`ci.yml:31-35`), `hatchling` pinned (0014). Still: no license field, the data-backed tests cannot run in CI by design, and the mockllm step sees only one question's prompts (L4). |
| Research rigor | 7 | Eight published numbers reproduced and verified live, the whole-degree equivalence proved on every value used, the distances and gap counts checked, the trap rates measured and recorded in 0013, the control named as such, the ablation designed and run the same day with the threshold and k kept, every cost setting verified at the source, the Limits honest that two rules rarely bite. Against that: the pair report and SUMMARY read the missed-days gap as a constant offset and neither says it rests on one station-season (M1, M3), 0013 says the missing-value rules "rarely" bite where the data say "only in Deer Valley 2019" (M3), the trap table counts a coincidence and misses the slip signature that explains half the misses (M4), the recall UNKNOWN is answerable from the logs (L2), and the reproduction quotes one of the page's three dates for the 2023 high (L3). |
| Readiness to publish | 7 | The package is sound: 300 of 300 valid, both harnesses on one contract, the wheel builds with its data, both runs done, reported and paired, the spend within the cap. Not yet: M1 and M2 are wrong sentences in published reports, the README's phase row and the workboard are behind the results and docs/log.md has no entry for either run (M5), the environment README does not say that the basis risk is one-sided and the missing-value rules are carried by one season (M3), and LICENSE is still absent. |

## 2. Plain answers to the four questions

**Is the environment saturated for Sonnet 5.5, and what would make it measure something?**
Saturated. With the rules shown, 296 of 300, a stderr of 0.007, no miss on trigger days or
events, and the four misses are each one row too many on the two-column comparison, on a day
when both stations had reached the threshold and the site was hotter than the index. The model
worked rather than recalled: 253 of 300 replies used extended thinking (Phase 4's shown run had
96), the median reply is about 890 output tokens of day-by-day tallies, and no reply names a
year. With the terms alone, 288 of 300: trigger days and events stay at 0.99 and 1.00, so the
model fills in "reaches" as at-or-above and one payment per run by itself, and missed days fall
to 0.89, where 7 of the 11 misses are the model saying in words that a dash is "not
determinable" and 4 are the same kind of slip as the control's. As a reward for this model the
environment returns 1 on almost every rollout; it is a regression check on the keys and the two
harnesses, which it passed. What would make it measure something, in order of how much it would
show: (1) rules the data actually exercise. Today one station-season, Deer Valley 2019 with 21
missing index days, carries the whole missing-value rule (8 of 100 missed-days items, 1 of 100
events items); a third pairing whose index has gaps in several seasons, or a question that asks
how many site-hot days could not be assessed, would test the rule on more than one draw. (2)
The insurer's side and money: days the index paid while the site was not hot (the other-way
count, right on 5 of 100 as a reading and 0 on every Sky Harbor pair at 110 F, so the
environment never asks it), tiers of the VimoSEWA kind (7, 11, 20 or 30 trigger days, not
necessarily consecutive), a payout per event with a cap, a deductible of n days; each is a rule
interaction with an exact integer or money key. (3) Larger counting loads that compound the slip
rate: a whole-year window, two seasons per item, or several sites per index; the 4 percent slip
rate on 153 rows of missed days is the only signal there is now, and it is arithmetic care, not
climate knowledge. (4) Derived questions: the lowest threshold that would have paid k events in
a season, or the share of the site's hot days the index caught. (5) A weaker policy model, the
kind an RL loop would train: whether it is saturated is UNKNOWN, since none has run. The exact
integer reward is right for all of these and should stay.

**Is the terms-only wording a fair ablation, and does its result mean what the pair report
says?** Fair. The threshold and k stay in every term (`contract.py:22-29`;
`tests/test_heat_contract.py:45-52` checks it), the three questions are unchanged, and the rows
still show the dashes. "Reaches T F" is at-or-above in ordinary usage and the model read it so:
no miss matches "above, not at, the threshold". "k or more consecutive trigger days" drops
"pays once, however long it lasts", which leaves the reading "one event per block of k days"
open (right on 38 of 100), and the model took one event per run on 100 of 100, so that clause
cost nothing. The one place the terms are silent is a missing index value: "the index
station's does not [reach T]" when there is no value is genuinely undefined, and there the
model chose the other reading and said so, on 7 of the 8 items where it matters (on the eighth,
2019/114, it gave the key's 7). So the result means: of the three clarifications the terms drop,
the model fills in two exactly as the key does and one the other way, and that one bites on 8
of 100 items, all of them Deer Valley 2019. The pair report's verdict, "a convention gap", is
right. Its clause "which a policy would close as a constant offset rather than learn as a skill"
is Phase 4's hours sentence and is wrong here: the correction is 2 to 15 days and differs per
item (18 to 5, 16 to 8, 9 to 2, 9 to 3, 3 to 0, 8 to 6, 35 to 20); a policy would adopt the
grader's convention from the reward, which is still not a skill, but it is not an offset. "6 of
the 11 misses" undercounts by one, since the 35 to 21 reply excluded the fifteen gap days and
slipped by one on top. And neither the pair report nor SUMMARY says that the whole gap is one
station-season, which another seed might not draw at all.

**Are the careless-reading baselines fair, and which readings that would bite are missing?**
Fair, correctly computed (all eight recomputed independently), and the report says which cannot
bite: "missing days skipped" is right on 99 of 100 and "missing index days left out" on 92,
because the airports have almost no gaps. Missing readings that would bite: for events, the
floor of run over k (right on 38), runs strictly longer than k (50) and runs of exactly k (30),
the first being exactly the reading the terms-only wording invites; for missed days, the site
strictly above the threshold (13) and the other way round (5). None was taken by this model,
but the terms-only trap table could not have classified them. What the actual misses show is
not a whole-item reading at all: "days the site was hotter than the index" is right on 0 of
100, yet 8 of the 16 full-run misses add one to three such days (both stations at or above the
threshold, the site hotter), and two items were missed in both runs with the same extra day
(06-13 in 2021/108, 06-05 in 2024/104). An "off by exactly one" count, as Phase 4 counts "short
by exactly 3 or 6 h", and a count of extra days of this kind would classify them; today the
report shows 0 in every trap row and the misses go unexplained. The best-constant baselines are
right (5 on 5, 0 on 27, 3 on 9). One trap match is a coincidence of value (M4).

**Is anything in the reports unverified or wrong?** No number is wrong: every number in the two
run reports, the pair report, the reproduction report, the manifest, 0012, 0013 and SUMMARY's
Phase 5 section recomputes from the files and the logs, and the eight anchors are on the live
pages today. Wrong text: the Limits of both run reports say "so on these storms the question
mostly tests ..., not the rule's choice of rows" (`report.py:226-228`, printed at lines 62-63 of
both), the pair report's "constant offset" clause (M1), and README.md:17 says "the terms-only
run and the review are next" after the run and its reports landed. Incomplete: "6 of the 11
misses" (7 exclude the gap days); 0013's "rarely change an answer" (only Deer Valley 2019
changes one); the reproduction's "119, 07/19" (the page lists 07/19, 07/20 and 07/25, and the
file has 483 tenths on all three); and "whether any answer was recalled rather than counted is
UNKNOWN" when the 600 replies name no year and every miss shows its tally. UNKNOWN and staying
so: which GHCN update built the pinned files (the radar names 3.35-upd-2026102917, the server
today 3.35-upd-2026103017, the file's Last-Modified is Nov 1 00:01 GMT); the run-to-run spread
(one reply per item, though the evidence in hand is that two items missed in both runs on the
same day and 2019/107 drew 2 and 3); and whether a weaker model is saturated.

## 3. Issues by severity

### High

None found. Nothing changes a key, a score in the log, a published number or a ledger row.

### Medium

**M1. The pair report and SUMMARY read the missed-days gap as a constant offset, and neither
says it sits on one station-season.**
`src/rlenv/ablation.py:55-60` prints "a convention gap, which a policy would close as a
constant offset rather than learn as a skill" for every environment; it lands at
`reports/heat/2026-11-01-rules-shown-vs-terms-only.md:31` and is repeated at `SUMMARY.md:74-77`
("what remains is a matter of convention (hours at hurricane strength, a missing index value),
which a policy would close as a constant offset"). For Phase 4's hours the offset was 3 or 6
hours on every item; here the correction is the number of gap days the site was hot, 2 to 15,
and the 8 items on which the rule changes the key are all Deer Valley 2019 (21 missing index
days). Smallest fix: give `render_pair` the closing clause as a parameter (Phase 4 passes the
offset sentence, Phase 5 "a convention the policy would take from the reward in a few steps,
not a skill it would learn"); in `rlenv.heat.report.render_pair` add one line naming where the
items whose key differs from the matched reading sit (index, season, count), computed from the
items; reword SUMMARY.md:76-77; one test on a pair summary whose explained misses sit on one
season. Then re-render the pair report.

**M2. Phase 4 wording printed in both heat reports.**
`src/rlenv/heat/report.py:226-228`: "so on these storms the question mostly tests
{TESTS[...]}, not the rule's choice of rows", printed at `reports/heat/2026-11-01-claude-sonnet-
5-5.md:62-63` and `reports/heat/2026-11-01-claude-sonnet-5-5-terms-only.md:62-63`. The items
are seasons and the rule chooses days. Smallest fix: "on these seasons" and "choice of days";
an assertion in `tests/test_heat_report.py:86-91` that "storms" is not in the rendered text;
re-render both reports.

**M3. The missing-value rules are carried by one station-season, and the records say
"rarely" where the data say "only there"; the basis risk is one-sided and the README does not
say so.**
`src/rlenv/heat/items.py:14` makes the two airports the only indexes. Their gaps in the ten
windows are one day at Scottsdale (2022-09-12), one at Deer Valley (2017-09-20, a QC-flagged
value) and 21 at Deer Valley in 2019. The missed-days rule "a missing index value counts as not
at or above" changes the key on 8 of 100 items, all Deer Valley 2019; the events rule "a
missing value ends a run" changes 1 of 100. `docs/decisions/0013-heat-basis-items.md:61-64`
says the rules "rarely change an answer"; the Limits of both reports say the same. A different
seed could draw no Deer Valley 2019 item and the rule would be untested. The other direction of
basis risk, days the index paid while the site was not hot, is never asked: as a reading it is
right on 5 of 100, and it is 0 on every Sky Harbor pair at 110 F, since the core is hotter on
every day the airports are. 0013:8-9 defines basis risk as the heat the policyholder has that
the index does not record, which is a legitimate choice, but `environments/heat_basis_v1/
README.md` presents "the basis risk" without the qualification. Smallest fix (record): one
sentence in 0013 and in both reports' Limits naming Deer Valley 2019 as the only place the
missing-index rule bites, and one sentence in the README that the missed-days question is the
policyholder's side only. The design fix is Aswani's: a third pairing whose index has gaps in
more than one season, or a fourth question for the insurer's side, each with its own test.

**M4. The trap table matches by value, so one match is a coincidence and the slip signature
that explains half the misses is not counted.**
`src/rlenv/heat/report.py:113-116` counts a miss as a trap when its answer equals the reading's
value. The shown report's one match (`reports/heat/2026-11-01-claude-sonnet-5-5.md:39`, "both
ways 1") is `missed_days/USW00003184/USC00028499/2015/105`, whose extra day 08-29 has the index
at 107 and the site at 109, not an index-only day; the reply itself says such days "are not
missed days". The 8 full-run misses that add a both-hot, site-hotter day, and the two items
missed in both runs on the same day, appear as 0 in every trap row. Smallest fix: in
`summarize`, count misses off by exactly one (and, for missed days, misses whose difference from
the key equals the number of hot site days with no index value, which catches the 35 to 21
reply); print both under the trap table with a sentence that matches are by value; put the
matched ids in the JSON; a test with one off-by-one mockllm reply.

**M5. Records behind the results.**
`README.md:17`: "the terms-only run and the review are next" (the run, its report and the pair
landed at e3a48a3 and 87a951a). `WORKBOARD.md:100-102`: the baseline and the terms-only
ablation boxes are open after both ran. `docs/log.md`: no entry records the Phase 5 full run
(0.987, $1.8801), the terms-only run (0.960, $1.9036) or the pair; the newest Phase 5 lines are
the build and the trap rates (docs/log.md:33-49) and the pgrep bug (docs/log.md:5-13). Smallest fix: one
line each.

### Low

**L1. The readings the terms-only wording invites are not in `careless`.**
`src/rlenv/heat/report.py:36-65`. Events as non-overlapping blocks of k days (right on 38 of
100), runs strictly longer than k (50), runs of exactly k (30); missed days with the site
strictly above the threshold (13) and the other way round (5). The first is the reading that
"An event is k or more consecutive trigger days" leaves open once "pays once, however long it
lasts" is dropped. Smallest fix: add them with a row each in `tests/test_heat_report.py:36-50`
(the events fixture there has a run of 2 and a run of 2 with k 2, so a run of 4 or 5 is needed
to separate the block reading from the key) and list them in 0013.

**L2. The recall UNKNOWN is answerable from the logs.**
`src/rlenv/heat/report.py:210-211` prints "whether any answer was recalled rather than counted
is UNKNOWN" in both reports. No reply in the 600 contains a four-digit year from 2010 to 2029,
and every miss shows a per-day tally. Smallest fix: count the completions that contain a year
from 2015 to 2024 and print the count in place of UNKNOWN; set `recognized` in the summary so
`ablation.render_pair` (`src/rlenv/ablation.py:63-67`) prints it for both runs as Phase 4's does;
a test on a mockllm reply that names a year.

**L3. The reproduction quotes one of the page's three dates for the 2023 high.**
`reports/heat/2026-11-01-nws-phoenix-reproduction.md:13` gives the published value as "119,
07/19"; the live page lists 07/19, 07/20 and 07/25, and the file has 483 tenths on all three.
`stats.highest` (`src/rlenv/heat/stats.py:40-45`) returns the first date by design and the test
comment at `tests/test_heat_reproduction.py:24` quotes only 07/19. Smallest fix: "119, 07/19
(also 07/20 and 07/25)" in the report and the comment; one line in the report noting the page's
"CLIMATE RECORD PERIOD 1895 TO 2024" beside ExtremeTemps' 1896 to 2025, since the two pages
disagree on the record period.

**L4. Test and CI gaps.**
`summarize`'s error path (`report.py:85,88-90`), `report.main` (242-262), `items.main`
(115-122, where the whole-degree guard at 117-119 lives; the rebuild test covers it only through
the sha256) and `data.main` (76-78) are untested. The CI mockllm step (`ci.yml:32-34`,
`--limit 3`) sees only trigger-days prompts, since the jsonl is in question order; `vf-validate`
builds all 300, so the gap is small. Smallest fix: `--sample-id` with the ids from `uv run
python -m rlenv.heat.tasks`, and a test on a log with one errored sample.

**L5. The source files cannot be re-obtained by anyone else once NCEI rewrites them, and the
version string is not recorded.**
`src/rlenv/heat/data.py:21-42` pins sha256, size and Last-Modified; `data/` is ignored by git.
Today the live Sky Harbor file still carries the pinned Last-Modified and size, so a rebuild
works today; NCEI says the by_station files are rewritten daily, and the server's
`ghcnd-version.txt` today names 3.35-upd-2026103017 where the radar row names 2026102917, so
which update built the pins is UNKNOWN. Smallest fix: attach the four gz files (2.9 MB) as a
release asset with their hashes, as Phase 4's L7 asked for the IBTrACS CSV, and record the
version string beside the pins when the next fetch is made.

**L6. Carried from earlier phases, and small clutter.**
No `license` field in `environments/heat_basis_v1/pyproject.toml` and no LICENSE at the repo
root (0014 says the choice is Aswani's). `src/rlenv/heat/report.py:11-12` and `tasks.py:11-12`
import the environment package, so `src/` depends on `environments/` as in Phases 2 to 4.
`items._spec` (`items.py:32-36`) unions two dicts where one literal would do. `report.careless`
is an independent re-implementation of the rules in whole degrees, which is the right design
for a check and deserves one sentence in its docstring.

## 4. What is missing to close Phase 5

1. M1 and M2 as template fixes, test-first, then the two run reports and the pair re-rendered
   (the pipeline is byte-stable, so the diffs will be the changed sentences only); SUMMARY.md:
   76-77 reworded for the heat case.
2. M3 recorded: one sentence each in 0013, both reports' Limits and the environment README
   naming Deer Valley 2019 as the only season the missing-index rule bites and the missed-days
   question as the policyholder's side of basis risk. The design change (a third pairing with
   gaps, or the insurer's side as a fourth question) is Aswani's call and is recorded either way.
3. M4, L1 and L2 in `summarize` and `careless`, test-first, then re-render.
4. M5: the README phase row, the two workboard boxes, and a LOG entry with both runs' numbers
   and the pair's finding.
5. L3 and L4, a line or two each; L5 and L6 wait for Aswani (release asset, LICENSE).

## 5. What I would not publish yet, and why

- "a convention gap, which a policy would close as a constant offset rather than learn as a
  skill" for missed days (`reports/heat/2026-11-01-rules-shown-vs-terms-only.md:31`,
  `SUMMARY.md:76-77`). The correction is 2 to 15 days and differs per item.
- "6 of the 11 misses follow a careless reading" as the size of the gap, without the sentence
  that 7 exclude the gap days and all sit on Deer Valley 2019.
- "the missing-value rules rarely change an answer" (0013:61-64) without "only Deer Valley
  2019 changes one".
- The two run reports' Limits as written: "on these storms ... the rule's choice of rows".
- "whether any answer was recalled rather than counted is UNKNOWN", when the 600 replies name
  no year and every miss shows its tally.
- "Sonnet 5.5 scores 0.987 on heat-basis-v1" as a result about the model. It is the control:
  the rules are in the prompt and the four misses are one-row slips. Publish it beside the
  terms-only run, as the pair report does, with the Deer Valley 2019 sentence.
- The environment README's "the basis risk" without saying it is the policyholder's side only
  and that the index never under-records the airports (0 missed days the other way on every Sky
  Harbor pair at 110 F).
- The reproduction's "119, 07/19" as the published value, when the page lists three dates.
- README.md:17 and WORKBOARD.md:100-102 as written, and a docs/log.md with no entry for the runs.
- The environment wheel without a license field and the repo without a LICENSE.
