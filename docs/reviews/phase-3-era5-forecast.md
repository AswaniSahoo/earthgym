# Phase 3 review: ERA5 forecast environment graded by the WeatherBench 2 rules

Reviewed 2026-10-30 against commit `b5c5edf` on `main` (working tree clean). The review started
at `2074d92`; three commits landed while it ran (8427bef, 80784e7, b5c5edf, the reward floor
rule), so every check below was repeated at `b5c5edf`. All findings refer to HEAD. The old
floors (50 Pa, 0.5 K) appear only where this review names them as history; no finding rests on
them. Everything below was run or read during the review; nothing is taken from memory. Where a
claim could not be checked it is marked UNKNOWN.

What was run: `uv run pytest -q` (116 passed at b5c5edf, 113 at 2074d92; the two reproduction
tests ran, the pinned subset is on disk), `uv run ruff check .` (clean), `uv run ruff format
--check .` (62 files clean), `uv lock --check` (clean), `gh run list` (the nine newest runs on
`main` green, newest b5c5edf at 2026-10-30T14:19:32Z; the three floor commits were pushed
together and ran as one), `uv run vf-validate era5-forecast-v1 --only-noop --runtime.type
subprocess` twice (720 of 720 valid, the second run at b5c5edf), the documented
`uv run inspect eval src/rlenv/era5/tasks.py@era5_forecast --model mockllm/model --limit 3` with
`--log-dir` in scratch (status success, the log records revision b5c5edf and `dirty=False`, 3
samples, reward 0.0 each because the default mockllm reply has no answer line), the README
`uv run vf-eval era5-forecast-v1 --dry-run --no-push -m test-model` (exit 0, the resolved config
records `"model": "test-model"`), `uv build environments/era5_forecast_v1` into scratch (the
wheel holds `era5_forecast_v1/era5_forecast_v1.jsonl`; METADATA has `Requires-Python: >=3.12`
and `verifiers<0.5,>=0.4.0`, no license field), `baselines.render(baselines.rows(records),
records)` into scratch (byte-identical to `reports/era5/items_v1_baselines.md`), the expert sheet
rebuilt into scratch with `sheet(records(), flags, EXTRAS)` and `write_once` (byte-identical to
`reports/climaqa/expert_review_v2.csv`; `write_once` on the committed path returns False), and
`uv run --with pytest-cov pytest` over the Phase 3 tests (78 percent of lines in the Phase 3
modules). The published numbers were read at their root: `benchmark_results/hres_vs_era5_64x32_2020.nc`
(1,469,120 bytes, CDF-2, sha256 `eec4fab627a3eac87fbada045bcf3507970a41fb3017c3c8dce7882e37e44947`)
opened with `scipy.io.netcdf_file`; the report had said it did not open the file itself.
Pins verified in `uv.lock`: `numpy 2.5.4`, `zarr 3.4.2`, `numcodecs 0.17.1`, `inspect-ai 0.3.286`,
`verifiers 0.4.0`, `fsspec 2026.6.0`, `aiohttp 3.14.5`, `pytest 9.2.0`, `ruff 0.17.3`. No em or
en dash in any Phase 3 prose file or module; the seven dashed cells in the review CSV are source
text (gold/mcq/210 and gold/mcq/56 option text, the gold/cloze/14 sentence).

Spot checks against the raw data, all at b5c5edf:

- Published scores, global, 72 h, from the score file: `rmse.mean_sea_level_pressure`
  133.89054684361142, `acc` 0.9818776389291946, `bias` -0.40657755779113947, `mse`
  17926.678534081304; `rmse.2m_temperature` 0.881072760502094, `acc` 0.9313474152151214. Ours
  from the pinned subset (`scores.rmse`, `acc`, `bias`, `mse`): 133.8905468754412 (difference
  3.2e-8 Pa), 0.9818776392430146 (3.1e-10), -0.4065775577911383 (1.2e-15 Pa), 17926.67854260472
  (8.5e-6). The grader follows the WB2 rules on this grid to float32 accumulation error.
- All 720 bundled items: ids unique, 120 per variable and lead, no repeated cell and init
  inside a group, latitude and longitude on the 64x32 grid, the id equal to its fields, valid
  time equal to init plus lead, 13 six-hourly history steps ending at the init, `area_weight`
  equal to `scores.area_weights(latitude)[i]`, every value rounded to the shown decimals, every
  `floor` equal to its variable's rule value, every history value and the climatology present
  in the prompt. The truth and HRES strings are absent from every prompt; the only matches are
  14 substring coincidences (a one-decimal value inside a two-decimal history value, for
  example truth 292.7 inside "292.73") and 31 items where the truth or HRES equals a shown
  value by coincidence (11 and 20), which the prompt cannot avoid and which leaks nothing.
- All 360 MSLP items against the pinned subset (lead 24, 48 and 72 h): 360 truths, 360
  climatologies and 2,495 history values at 00 and 12 UTC equal the subset's ERA5 and aligned
  climatology after rounding, and all 120 HRES values at 72 h equal the subset's forecast.
- Online, with independent index arithmetic over the three stores (about 20 MB of chunk
  reads, 34 s): 7 items recomputed, 0 mismatches. Five 2 m temperature items, one per lead
  plus one whose valid time is 2021-01-01T12 (day of year 1) and one whose history starts
  2019-12-29 (init 2020-01-01T12), matched on all 13 history values, the truth, the HRES
  value and the climatology at the valid hour and day of year; two MSLP items at 24 and 48 h
  matched on history, truth and HRES, which checks the `prediction_timedelta` index for the
  two leads the subset cannot see (its values are hours: 0, 6, 12, 18, ...). The store axes
  are (time, longitude, latitude) and the climatology (hour, dayofyear, longitude, latitude),
  as `items.read_fields` assumes. No bundled item has a valid time on 2020-02-29, so the
  leap-day alignment is covered only by `test_align_picks_the_climatology_of_each_valid_day_of_year_and_hour`
  (day 366) and by the ACC reproduction, whose 732 valid times include that day.
- The reward (`contract.reward`) equals an independent transcription of decision 0007 on 14
  edge cases (both baselines perfect, baseline error under and at the floor, copies of either
  baseline, the mirror of persistence, inf, -inf, nan, -0.0, no answer) and on 20,000 random
  draws. The two harnesses pay the same: 720 (item, reply) pairs on 12 bundled items (six per
  variable), scored through `tasks.forecast_scorer()` on a `TaskState` and through
  `ForecastTask.skill` on a `Trace` stub, equal to each other and to 0007 on every pair.
  Inspect's `generate()` sends only `Sample.input`; verifiers builds the model's view from
  `task.prompt` and `system_prompt` (`verifiers/v1/harness.py:79-82`), so `truth`, `hres`,
  `climatology` and `floor` in the metadata and `TaskData` never reach the model.
- The floor as of HEAD: `np.percentile(b, 10)` over the 360 better-baseline errors per
  variable equals every item's `floor` and the manifest (28.749999999989814 Pa,
  0.06899999999999408 K); it binds (b below the floor) on 36 and 36 items as 0007, the README
  and the manifest say; the old 50 Pa and 0.5 K bind on 65 and 167, as docs/log.md says. Three
  2 m temperature items have b equal to 0.
- The expert sheet against the Gemini logs on this machine (`logs/2026-10-30-gemini-3.8-flash`,
  350 samples read with `inspect_ai.log`): the 20 sampled hits are hits and the 61 misses are
  misses in the logs, 60 of the 61 model answers equal the logged reply (the one exception is
  L2), every key and question equals the bundled clean set v1, the two miss notes parse with a
  constant cell count (6 and 5 columns, 28 and 33 rows), and the `verdict`, `accepted_answers`
  and `expert_note` columns are empty on all 83 rows. The CSV has one commit (d7f320e) and no
  change since.

## 1. Ratings

| Area | Score | Justification |
|---|---|---|
| Correctness | 9 | The grader matches the published file at its root to 3e-8 Pa, the 720 items match the pinned subset wherever it can see them (3,335 values) and the stores on the online sample, the reward equals 0007 on every edge case and fuzz draw, the harnesses agree on 720 pairs, nothing leaks, every command in the docs runs. Against that: a latent division by zero in the floor rule (M3), a parser stricter than the repo's own 0004 on a trailing full stop (L1), and one wrong cell in the expert sheet (L2). |
| Minimalism and clarity | 8 | 79, 55, 57, 47 lines for scores, contract, taskset and the Inspect task, one job each, names that read as prose, the WB2 pooling finding written where the code is. Clutter: `HIDDEN` in `tasks.py:16` lists two fields that are in the prompt, `VARIABLES[...][1]` is indexed by position after the floor left the tuple, `rlenv.era5.baselines` imports the environment package so `src/` depends on `environments/` (as in Phase 2), and the subset size is stated three ways (12.0 MB, 18.0 MB, 19 MB). |
| Test coverage | 7 | 48 Phase 3 tests; contract, taskset, Inspect task and scores at 100 percent; the synthetic `make_item` test encodes indices, which is the right idea. Missing: any test that ties the bundled values to source data (M2), the zero-floor guard (M3), `floor_binds`, the MCQ-miss path of the sheet (`expert_sheet.py:50`), `write_once`'s write path (80 to 84), the parser's "last line" and trailing full stop cases, and the harness-equality test covers one sample. |
| Reproducibility | 8 | Store metadata pinned by sha256, the subset by content hash, the jsonl by sha256 in a manifest with seed and floors, every item carrying its floor, byte-identical regeneration of the baseline table and the review sheet, the Inspect log naming a clean commit. Gaps: the reproduction report names a commit whose grader code has since changed (L3), the items rebuild needs a 55 MB read nobody but the build session has done, and the exact float equality on the floor ties the set to numpy's percentile arithmetic (L5). |
| CI/CD | 7 | Green on every push, actions and runner pinned, `--locked --all-groups`. Unchanged from Phase 2: no `vf-validate`, `inspect eval` or wheel smoke, `hatchling` unpinned, and the reproduction never runs in CI because the subset is not there. |
| Research rigor | 7 | Two published numbers reproduced to six decimals and now verified at the root, the ACC pooling finding is real and recorded with its source, decisions dated, the baseline rows include the always-climatology policy as 0007 asked. Against that: the reward's main property is not reported (M1): the baseline is the better of two after seeing the truth, so IFS HRES earns 0 on 136 of 360 temperature items and 0.08 on the lowest quartile; the floor rule was chosen and closed by the build session; the attribution record contradicts itself across two commits; the bias row says UNKNOWN for a number sitting in the same file. |
| Readiness to publish | 6 | Grader, data and both harnesses are sound and documented. Not yet: the floor and its disclosure (M1), no model has produced a non-zero reward (mockllm only), LICENSE still absent, the parser contract differs from 0004, and the sheet needs one cell fixed before an expert opens it. |

## 2. Issues by severity

### High

None found. Nothing changes the two published numbers, the item values or the reward's
agreement with 0007.

### Medium

**M1. The floor rule was set, applied and closed by the build session, and what it does to the
reward is not reported.**
`docs/decisions/0007-phase-3-task-design.md:28-33` now says the floor "is a technical guard,
not Aswani's decision" and fixes it at the 10th percentile of the better-baseline error
(`src/rlenv/era5/items.py:26,35-41`); `WORKBOARD.md:42-43` marks it done and the open question
that was under "Waiting on Aswani" at 2074d92 is gone. The record contradicts itself: at
1711c1d lines 23 to 28 read "Reward per item, from Aswani: ... Floors start at 50 Pa for MSLP
and 0.5 K", at 80784e7 the same values are "the build session's own guess". Which is true is
UNKNOWN to this review; both versions were written by the build session. The formula itself is
unchanged and equals 0007 everywhere (verified above). What the choice does, from the bundled
items (HRES reward by quartile of the better-baseline error b, this review's computation):

| variable | quartile | n | median b | median HRES error | HRES mean reward | HRES earns 0 | HRES beats b |
|---|---|---|---|---|---|---|---|
| MSLP | Q1 (b under 67.2 Pa) | 90 | 35.8 | 37.8 | 0.184 | 56 | 34 |
| MSLP | Q2 | 90 | 103.8 | 31.8 | 0.612 | 12 | 78 |
| MSLP | Q3 | 90 | 307.3 | 45.1 | 0.775 | 1 | 89 |
| MSLP | Q4 (b over 505 Pa) | 90 | 821.3 | 66.6 | 0.871 | 1 | 89 |
| T2M | Q1 (b under 0.19 K) | 88 | 0.070 | 0.210 | 0.082 | 73 | 15 |
| T2M | Q2 | 92 | 0.360 | 0.260 | 0.327 | 38 | 54 |
| T2M | Q3 | 89 | 0.850 | 0.430 | 0.485 | 19 | 70 |
| T2M | Q4 (b over 1.45 K) | 91 | 2.640 | 0.620 | 0.677 | 6 | 85 |

Over all items HRES beats the better baseline on 290 of 360 MSLP and 224 of 360 temperature
items; a policy answering the midpoint of persistence and climatology earns 0.111 and 0.104.
So on a quarter of the temperature items the best forecast system in the set earns almost
nothing, and under a 0.069 K floor an exact hit on one of them pays up to 1.0 while HRES pays
0.08 on average: on those items the reward measures luck. The old 0.5 K floor capped a
perfect reply on them at b/0.5 (at most 0.38 in that quartile), which is why its binding count
was 167. Neither value is "technical": the floor decides how much of the temperature reward is
noise, and it moved HRES's temperature rows from 0.28 to 0.45 up to 0.30 to 0.49
(`reports/era5/items_v1_baselines.md:22,26,30`). Also undisclosed: 3 temperature items where
b is 0, on which no reply can earn more than 0, and the 36 per variable where a perfect reply
earns at most b/floor. Smallest fix: put the floor back under "Waiting on Aswani" as a yes or
no on the percentile rule, with this table in front of him; add a "Limits" block to
`baselines.render` (`src/rlenv/era5/baselines.py:55`) that prints the table above, the dead
items and the capped items; record his answer in 0007 and stop attributing the old values
either way until he says. The baseline being chosen after seeing the truth is his rule and
binding; it still belongs in `environments/era5_forecast_v1/README.md:10-14` in one sentence.

**M2. No test ties the bundled values to source data.**
`src/rlenv/era5/items.py:100-123` (`read_fields`, the real-store indexing across three stores
with two axis orders and two time origins) is at 0 percent, and `tests/test_era5_items.py:65-68`
checks the jsonl only against a manifest the same run wrote. The synthetic test at lines 36
to 47 is good but cannot see a wrong `prediction_timedelta` index, a climatology day-of-year
off by one, or a swapped axis in a real store. This review found no such error, but it found
it by hand: the pinned subset already on disk is an offline oracle for 360 MSLP truths and
climatologies, 2,495 history values and 120 HRES values. Smallest fix: a
`tests/test_era5_items_subset.py` with the same `skipif` as the reproduction test that loads
`data.load()`, indexes each MSLP item by `init_time`, `valid_time`, `latitude` and `longitude`,
and asserts the four fields after `round(x, 1)`; about 25 lines, no network.

**M3. The floor rule can produce 0, and the reward then divides by zero.**
`items.floors` (`src/rlenv/era5/items.py:41`) returns the 10th percentile of b; if a tenth or
more of a variable's items have b equal to 0 the floor is 0.0, and `contract.reward`
(`environments/era5_forecast_v1/era5_forecast_v1/contract.py:54`) raises `ZeroDivisionError`
for every item with b equal to 0 and a parsed reply (verified: `reward(5.0, 5.0, 5.0, 5.0,
0.0)` raises). v1 cannot trigger it (3 of 360 temperature items have b equal to 0, the floor is
0.069 K), and `vf-validate --only-noop` cannot catch it because a reply without an answer line
returns before the division. A crash inside a reward is the worst failure in an RL loop.
Smallest fix: `max(np.percentile(e, FLOOR_PERCENTILE), 10 ** -DECIMALS[v])` in `floors`, and
in `reward` return 0.0 when `max(baseline, floor) == 0`; tests for both.

### Low

**L1. The parser is stricter than 0004 and looser than its own prompt.**
`contract.py:22-24` rejects a trailing full stop: `ANSWER: 285.5.` and `ANSWER: 285.5 K.` score
None and pay 0, while the Phase 2 contract accepts `\s*\.?\s*$`
(`environments/climaqa_v1/climaqa_v1/contract.py:18`), so the two environments in one repo
treat the same sentence differently. Also None: the Unicode minus sign (U+2212), `285,5`,
`101,325.5`, `~285.5`, a plus-or-minus range. In the other direction the prompt
(`contract.py:19`) says "The last line of your response must be", but `findall` at line 39
accepts an answer line anywhere and takes the last one, so `ANSWER: 285.5\nThat is my final
answer.` scores 285.5 and `ANSWER:\n285.5` (newline inside `\s*`) scores too. Both harnesses
agree, so this is a contract wording issue, not a disagreement. Smallest fix: add `\.?` before
`$` as 0004 does, say "a line" rather than "the last line" in the prompt and docstring (or
anchor the regex to the final line), and add the full stop, Unicode minus and trailing-prose
cases to `test_answer_reads_the_last_answer_line_with_an_optional_unit`.

**L2. One sheet cell shows the note's remark, not the model's answer.**
`reports/climaqa/expert_review_v2.csv:122` (gold/cloze/37) has `model_answer` "Aerosol-cloud
(en dash in the reply)" because `expert_sheet.note_rows` (`src/rlenv/climaqa/expert_sheet.py:36`)
copies the note's reply cell and the note's line 62 holds a remark in that cell; the logged
reply is "Aerosol-cloud" with an en dash (U+2013). The other 60 miss cells equal the logs.
Smallest fix: put the verbatim reply in the note's reply cell and the remark in its note cell,
delete the unfilled CSV and regenerate it (safe now: every expert column is empty), and add an
MCQ row to `NOTE` in `tests/test_expert_sheet.py` so line 50 and the 6-column layout are
tested.

**L3. Report and record drift.**
`reports/era5/2026-10-30-wb2-reproduction.md:3-4` names commit 2d97668 for `scores.py` and
`data.py`, which changed in 3b2a5a7 and 3713c87 (48 insertions; the numbers still hold at
HEAD, verified). Line 12 marks the bias "not checked (UNKNOWN)", yet the same file holds
`bias.mean_sea_level_pressure` -0.40657755779113947 and ours matches to 1.2e-15 Pa. `docs/log.md:10`
and `WORKBOARD.md:30` say "12.0 MB" for a subset that is 17,997,770 bytes (18.0 MB, as the
report's line 39 says) since the climatology joined it in 4501ad1. Smallest fix: name the
commit the numbers were last verified at, fill the bias row with the file's value, and fix the
two sizes.

**L4. CI could catch what this review ran by hand.**
`.github/workflows/ci.yml` runs lint, format and tests only. `uv build
environments/era5_forecast_v1`, `uv run vf-validate era5-forecast-v1 --only-noop --runtime.type
subprocess`, `uv run vf-eval era5-forecast-v1 --dry-run --no-push -m test-model` and the
documented `inspect eval ... --model mockllm/model --limit 3` all run offline in minutes. The
reproduction and M2's test are skipped in CI because the subset is not there (18 MB, outside
the offline rule; leave them local but say so in the README). `hatchling` is still unpinned at
`environments/era5_forecast_v1/pyproject.toml:10` with no `docs/decisions` record and no
`license` field, carried from the Phase 2 review L2.

**L5. Exact float equality couples the bundled floor to numpy's percentile arithmetic.**
`tests/test_era5_items.py:84-88` asserts `r["floor"] == floors[r["variable"]]` and the manifest
equality on 28.749999999989814 and 0.06899999999999408; any change in numpy's interpolation
rounding fails the test on a set that did not change. numpy is pinned, so this holds today.
Smallest fix: round the floor in `floors()` to one decimal more than the shown decimals (28.75
Pa, 0.069 K), which also makes the published number the stored number, and use `pytest.approx`
in the test.

## 3. What is missing to close Phase 3

1. Aswani's answer on the floor rule (M1), with the quartile table and the dead and capped
   item counts in front of him, recorded in 0007; then the one-sentence disclosure of the
   oracle baseline in the environment README and the "Limits" block in the baselines report.
2. M2 and M3 test-first: the subset-backed items test and the zero-floor guard.
3. A first real model log. mockllm proves the plumbing, not that any model can earn a reward
   above 0 or that the `ANSWER:` contract survives a reasoning model's output; 0007 says a
   baseline run needs Aswani's yes. The Phase 2 run config (temperature 0, seed, max tokens,
   clean tree, command in the report) applies as is.
4. L1 to L5, test-first.
5. Still open from earlier phases: LICENSE (now also gates the second environment package),
   the expert's name for the 0005 sheet, `reports/climaqa/leak_review.csv` and
   `reports/climaqa/review_sample.csv`.

## 4. What I would not publish yet, and why

- "IFS HRES earns 0.30 to 0.49" as a property of the environment. It is a property of the
  floor and of a baseline chosen after seeing the truth; the quartile table shows HRES earning
  0.08 on a quarter of the temperature items.
- The sentence that the floor is "a technical choice" (`WORKBOARD.md:42`, 0007 line 28). It
  changes how much of the temperature reward is luck.
- Either attribution of the 50 Pa and 0.5 K floors. The two commits say opposite things and
  this review cannot tell which is right.
- The reproduction report's commit line and its UNKNOWN bias row, as written.
- `reports/climaqa/expert_review_v2.csv` row 122 as the model's answer, until L2 lands.
- Any statement that the task is learnable or that the contract works with a real model. No
  model has run; three items cannot be won at all.
- The environment wheel without a license field and the repo without a LICENSE.

## Author response (2026-10-30)

Code fixes landed test-first. The two tests that check existing behaviour (the subset oracle
and the MCQ sheet row) were each shown to fail on broken input: the subset test on a copy of
the items with one history value moved by 0.1 Pa.

| Issue | Fix | Commit |
|---|---|---|
| M1 floor rule and its consequence | 0007 now records who did what: the coordinating session suggested the floor; the build session guessed 50 Pa and 0.5 K (1711c1d, worded as if they were Aswani's); the coordinating session set the 10th-percentile rule on 2026-10-30 as decided, without waiting on Aswani, so it stays closed. The Limits block of the baselines report gives HRES's reward per quarter of b (temperature quarter 1: 0.086, 0 on 74 of 90) and the 3 items no reply can win; the README says the baseline is picked with the truth known | cbdafb0, 5ef3497, c4821ea |
| M2 no test ties items to source data | subset-backed test: 360 truths, 360 climatologies, 2,495 history values, 120 HRES values, skipped without the subset | 3c52cc6 |
| M3 a zero floor divides by zero | the floor never drops below the smallest shown unit, and the reward returns 0 when its scale is 0 | f736fdd |
| L1 parser and 0004 | a trailing full stop and the Unicode minus are read; the number must sit on the answer line; the last answer line still counts, as in 0004 | a95e10f, 94adf2e |
| L2 sheet row for cloze 37 | the note's reply cell holds the reply and its remark moved to the note; the sheet shows the logged reply verbatim; the unfilled sheet was regenerated (one row changed) | 37e6636 |
| L3 report and record drift | the published file read at its root (sha256 eec4fab6...): bias matches to 1.2e-15 Pa and is now a reproduction test; the commit line and the subset size fixed | 04a516b, 55fad15, c4821ea |
| L4 CI smoke | vf-validate, the documented inspect eval on mockllm and the wheel build run in CI | b35f148 |
| L5 float equality on the floor | floors stored rounded to one decimal more than shown (28.75 Pa, 0.069 K), tests use approx | f736fdd |

Open: a first real model run (needs Aswani's yes), LICENSE and the package license fields,
`hatchling` unpinned, the expert's name for the 0005 sheet, and the two hand-check sheets.
