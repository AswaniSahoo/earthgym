# Phase 4 review: ibtracs-storm-v1, per-storm cyclone questions with exact answers from IBTrACS

Reviewed 2026-11-01. The checks started at commit `5c1e85f` on `main` (tree clean apart from an
untracked Phase 5 decision). Twenty-four commits landed while the review ran, most of them
Phase 5; eleven touch Phase 4: 7434a35 (the rules-hidden switch in the contract, taskset and
Inspect task), f494ecd, d14bdf2 and 5cf0bb3 (the side-by-side ablation report, moved to
`rlenv.ablation`), 2200f6b (0011 records the ablation), 3d11eef (the rules-hidden probe's ledger
row), 039dde5 (an elapsed-time careless reading for hours), b44ece2 (workboard), c3a9042 (the
pair report's convention sentence), 01f1074 (the rules-hidden run's ledger row) and ee3b39f (the
rules-hidden and pair reports). So the phase's own answer to the saturation question, the
300-item rules-hidden run, arrived while this review ran and is reviewed below from its log.
HEAD at writing is `ee3b39f`, tree clean. Every check that those files could affect was repeated
at 2200f6b, and the suite and lint again at b44ece2 and ee3b39f; the run first under review (the
rules-shown Sonnet 5.5 log) was made at ba3cf2a and the shown prompt is byte-identical before
and after the switch, verified against the log. Nothing below is taken from memory; where a claim could not be checked it is
marked UNKNOWN. No paid model call was made by this review.

What was run: `uv run pytest -q` (209 passed at 5c1e85f, 232 at 2200f6b and at b44ece2, 233 at
ee3b39f; the reproduction tests ran, the pinned CSV is on disk and its sha256 is the pinned
666681be...),
`uv run ruff check .` (clean), `uv run ruff format --check .` (clean at every commit checked),
`uv lock --check` (clean),
`gh run list` (every Phase 4 commit on `main` with a run is green, from ba3cf2a through 7434a35,
f494ecd, d14bdf2, 5cf0bb3, 2200f6b, 3d11eef, 039dde5, b44ece2 and ee3b39f, checked last after
ee3b39f's run completed),
`uv run vf-validate ibtracs-storm-v1 --only-noop --runtime.type subprocess` twice (300 of 300
valid at 5c1e85f and at 2200f6b), the documented `uv run inspect eval
src/rlenv/ibtracs/tasks.py@ibtracs_storm --model mockllm/model --limit 3` three times with
`--log-dir` in scratch (at 5c1e85f; at 2200f6b with the rules shown and with `-T rules=false`;
all success, revision 2200f6b with `dirty=False`, the "Rule." paragraph present in 3 of 3 and
absent in 3 of 3), `uv build environments/ibtracs_storm_v1` into scratch (the wheel holds the
944,451 byte jsonl; METADATA has `Requires-Python: >=3.12`, `verifiers<0.5,>=0.4.0`, no license
field), `uv run vf-eval ibtracs-storm-v1 --dry-run --no-push -m test-model` (exit 0, output
under the ignored `outputs/`), the items pipeline (`items.eligible`, `plan`, `make_item`,
`write` over the pinned CSV into scratch: 613 eligible storms, the 300 items byte-identical to
the bundled jsonl, the manifest equal field for field), the report pipeline (`uv run python -m
rlenv.ibtracs.report logs/2026-11-01-ibtracs-claude-sonnet-5-5 --out <scratch>`: the markdown
and the JSON byte-identical to the committed report, run at HEAD with the new `--hidden`
option present), `uv run --with pytest-cov pytest` over the Phase 4 tests (88 percent of lines
in the Phase 4 modules, 348 statements, 41 missed; contract, taskset and stats at 100 percent),
and the three logs on this machine read with `inspect_ai.log.read_eval_log`: the full run (300
samples, revision ba3cf2a, `dirty=False`), the probe (6 samples, revision 6bf478e), and the
rules-hidden probe that ran during the review (`logs/2026-11-01-ibtracs-hidden-claude-
sonnet-5-5-probe`, read twice: a header with status `started` and 0 samples at first, then
success, 6 samples, `task_args {'rules': False}`, revision 560448f, `dirty=False`, 4 of 6), and
the 300-item rules-hidden run (`logs/2026-11-01-ibtracs-hidden-claude-sonnet-5-5`, status
success, 300 samples, `task_args {'rules': False}`, revision 3d11eef, `dirty=False`), whose two
reports (`reports/ibtracs/2026-11-01-claude-sonnet-5-5-rules-hidden.md` and
`2026-11-01-rules-shown-vs-hidden.md`) were read as committed at ee3b39f. The keys were
recomputed by a pure
standard library script that reads the CSV and transcribes the three rules from the prompt text,
without importing `stats.py` or `items.py`. Sources read at their root today: Anthropic's
pricing page, models overview, "Steering thinking" (effort) page and prompt caching page
(curl), NHC's `aboutsshws.php` (curl), NCEI's 202413 and 202513 annual reports (Firecrawl; curl
returned a 508,808 byte shell with none of the numbers), and the Inspect 0.3.286 source in the
venv (`model/_providers/anthropic.py`, `model/_generate_config.py`, `_cli/eval.py`). Pins in
`uv.lock`: `anthropic 2.3.0`, `inspect-ai 0.3.286`, `verifiers 0.4.0`, `pytest 9.2.0`, `ruff
0.17.3`; `hatchling` is absent from the lock (an unpinned build requirement, carried from Phase
2). No em or en dash in any Phase 4 prose file or module.

Spot checks against the raw data:

- Keys. The independent recomputation equals the bundled key on 300 of 300 items (ACE to four
  decimals, peak category, hours). Thirty are listed here from a seeded sample, ten per
  question, with the key: ACE BERYL 2000 0.89, FELIX 1989 9.7275, CLAUDETTE 2003 9.24, OTTO
  2010 5.3875, FIONA 2010 3.0775, DEAN 2007 35.2325, PATTY 2012 1.0925, EARL 2010 27.69,
  DANIELLE 1986 1.56, DANNY 2003 4.5575; peak SHARY 2010 1, LILI 1996 3, LEE 2017 3, GASTON
  2004 1, KLAUS 1984 1, GRACE 2021 3, HUMBERTO 2019 3, LILI 2002 4, KYLE 2008 1, LISA 2004 1;
  hours KLAUS 1990 18, PALOMA 2008 54, ISAIAS 2020 54, KATE 1985 138, MARIA 2017 252, IRENE
  1981 150, BRET 1999 60, JEANNE 1980 36, IDALIA 2023 36, DANNY 1997 42. Every item's `rows`
  equal the CSV's rows for its SID in archive order (ISO time, USA_STATUS, USA_WIND, USA_PRES
  or null), and `season` and `name` equal the CSV.
- Population. 743 storms have SEASON 1980 to 2025; 626 reach 34 kt as TS, HU or SS; 13 of
  those have a row outside the NA basin and are dropped; none has a spur row or a blank wind
  or status; 613 are eligible (the README and manifest value), 306 of them hurricanes. Median
  rows 53 over the eligible storms and 56 over the ACE sample, which holds 58 hurricanes
  (population share 0.499), as 0011 says. The jsonl's sha256 equals the manifest's 75fe4ff2...;
  ids and SIDs unique; 100 items per question; peak keys 35, 20, 19, 17, 9 for categories 1 to
  5; hours keys 6 to 288; ACE keys 0.1225 to 48.9425, 3 of them ending in exactly 5 at the
  second decimal.
- Prompts. None of the 300 shown prompts, and none of the 300 hidden prompts at HEAD, contains
  the storm's name (case-insensitive), its season, its SID, or any four-digit number from 1980
  to 2025. Every status in the items (TD, TS, HU, EX, SD, SS, LO, WV, DB) is in the legend.
  10,874 of the 22,288 rows are 3-hourly, 130 are at other minutes (landfall and peak rows), 17
  of those at a synoptic hour with non-zero minutes (00:30, 06:15, 12:30, 18:45 and so on).
  Prompts run 1,133 to 6,356 characters.
- The log against the items and the contract. All 300 `Sample.input` values equal
  `contract.prompt(item)` at ba3cf2a and at 2200f6b; every sample's metadata key and target
  equal the bundled key; Inspect's logged score equals `contract.reward(question,
  contract.answer(completion), key)` on all 300; 0 parse failures; stop reason `stop` on 300;
  accuracy 0.996667, stderr 0.003333; per question 0.99, 1.00, 1.00; no wrong answer equals any
  careless reading (0 on all five, as the report's trap table says). Tokens 1,685 input,
  539,944 cache write, 2,137 cache read, 137,181 output, 48,487 reasoning, and the 300
  per-sample usages sum to the log totals; cost $1.36262685 at the 0010 prices with the batch
  halving, $0.004542 an item; the 300 `item_costs` in the JSON sum to the same. The probe: 6 of
  6, $0.024585. Only 96 of the 300 replies used any reasoning tokens (ACE 56 of 100, hours 38,
  peak 2); median output 282 tokens, maximum 2,146. The 0010 claims about the request are in
  the logged call: `max_tokens 32000`, `thinking {"type": "adaptive", "block_binding": ...}`,
  no temperature, no effort, `service_tier` `batch` in the response.
- The miss. `ace/2007255N13316` (INGRID, 2007): key 1.3 from ten qualifying rows (eight at 35
  kt, two at 40 kt, 13,000 kt squared), answer 1.2. The completion lists all ten rows
  correctly, then writes "Seven rows at 35 kt: 7 x 1225 = 8575 ... Total: 8575 + 3200 = 11775
  ... 1.1775, which rounds to 1.2". A counting slip over its own list, one 35 kt row short; it
  matches no careless reading (every row 2.4838, ignoring status 1.3, TS and HU only 1.3). The
  reply used 0 reasoning tokens and 448 output tokens.
- The rules-hidden probe (the same six ids as the shown probe, prompts equal to
  `contract.prompt(item, rules=False)` on all six). 4 of 6, mean 0.6667, stderr 0.2108. Both
  ACE items right (1.1 for key 1.05, 8.5 for 8.49), the model stating the convention itself:
  "computed only from the synoptic fixes (00, 06, 12 and 18 UTC), and only while the storm is
  at tropical-storm strength (wind >= 34 kt)". Both peak items right (Andrew 1992 and Wilma
  2005, "137 kt or above"); the Wilma reply says "This storm looks like Hurricane Wilma (2005),
  whose official peak was 160 kt at 882 mb". Both hours items wrong by exactly 3 h: 75 for key
  78 (Keith 2000) and 63 for 66 (Olga 2001), under the reading the model names, "each row's
  status holds until the next row". That reading (the sum of the gaps from every HU row to the
  row after it) reproduces both answers and is right on 36 of the 100 hours items; the reading
  added in 039dde5, "elapsed time, first to last HU row", gives 126 and 60 for these two items
  and is right on 1 of 100. Five of the six replies used reasoning (2,826 tokens in all; output
  223 to 1,435 tokens, about twice the shown probe's). Cost $0.036053, the ledger's 0.0361.
- The 300-item rules-hidden run. All 300 inputs equal `contract.prompt(item, rules=False)`;
  0 parse failures; the logged score equals the contract on all 300. Accuracy 0.703333 (stderr
  0.026417): ACE 0.99, peak 0.99, hours 0.13, as the committed reports say. Tokens 2,090 input,
  512,499 cache write, 2,077 cache read, 227,435 output, 124,643 reasoning; cost $1.779993,
  the ledger's 1.7800, running total $5.3107. Reasoning on 99 of 100 ACE replies, 92 of 100
  hours, 10 of 100 peak; median output 718 tokens. The 89 misses: 87 hours, 1 ACE
  (`ace/2012255N16322`, Nadine 2012: 26.1 for 26.34, no careless reading matches), 1 peak
  (`peak_category/2015229N10331`, Danny 2015: 4 for 3). Of the 87 hours misses, 57 are short
  by exactly 3 h (27) or 6 h (30), the two elapsed-time conventions; 41 equal "elapsed time,
  first to last HU row" as the pair report says, 15 equal "status holds until the next row", 13
  equal "3 h per HU row" (the sets overlap), 30 equal none of the readings tried. Keith 2000
  got 75 in the probe and 71 in the run: two conventions from one model on one item. All 100
  hidden ACE replies state the synoptic-hours and 34 kt convention unprompted, and 28 mention
  subtropical status. Four replies name their own storm or its season (Humberto 2025, Wilma
  2005, Ernesto 2012, Matthew 2016).
- Ledger. The eight rows of `reports/spend.md` and their running totals recompute from the
  token columns at the 0010 prices (the test does this; the four Phase 4 rows were also done
  by hand: 0.024585, 1.362627, 0.036053 and 1.779993). Total $5.3107 after the Phase 5 probe,
  the rules-hidden probe and the rules-hidden run rows that landed during the review.
- Pricing and settings at the source (pricing page, fetched today): Claude Sonnet 5.5 "$2 /
  MTok $10 / MTok $2.50 / MTok $4 / MTok $0.10 / MTok" (input, output, 5-minute write, 1-hour
  write, read; the read is "0.05x on Claude Opus 5.5 and Claude Sonnet 5.5"), "a 50 percent
  discount on both input and output tokens" for the Batch API, and the cache multipliers
  "stack with other pricing modifiers, including the Batch API discount". The logged response
  usage puts every cache write under `ephemeral_5m_input_tokens`, so $2.50 is the right tier.
  Models overview: Claude API ID `claude-sonnet-5-5`, "Default effort ... high" for Sonnet
  5.5; the effort page: "Claude Sonnet 5.5 supports all five effort levels, and high is the
  default on the Claude API". Prompt caching page: "the minimum cacheable prompt length is: 512
  tokens for ... Claude Sonnet 5.5", which is why this run alone shows cache writes (its
  prompts average about 1,800 tokens; ERA5's were about 450 and ClimaQA's about 150; the one
  ibtracs sample with 489 input tokens was not cached).
- NCEI anchors at the live pages (Firecrawl, today). 202413, North Atlantic table: Tropical
  Storm 18 (record "30 (2020)"), Hurricane 11 (record "15 (2005)"), Major Hurricane 5 (record
  "7 (2005, 2020)"), ACE 161.6 (record "258.6 (1933)"); summary table "North Atlantic | 18+ |
  11+ | 5+ | 2++ | 162" (the Category 5 cell is 2); the text "only include 6-hourly storm
  fixes" and "derived from NCEI's IBTrACS dataset" is there as the radar quotes it. 202513: 13
  named, "Five of those were hurricanes, including four major hurricanes", ACE 132.6, "Three
  Category 5 hurricanes". NHC `aboutsshws.php`: 64-82 kt, 83-95 kt, 96-112 kt, 113-136 kt,
  "137 kt or higher", as `stats.CATEGORIES` and the prompt state.
- Reproduction, independently: 1933 ACE 258.57; 2005 named 28, hurricanes 15, major 7,
  category 5 count 4; 2020 30, 14, 7, 0; 2024 18, 11, 5, 2 and ACE 161.58; 2025 ACE 130.77.
  Sensitivity: the SS rule is needed (2024 gives 158.32 without SS, 161.58 with it; 1933 has
  no SS row, so it says nothing about SS); the basin rule and the spur rule change nothing on
  any anchored season (identical numbers with every row of every storm counted, and with spur
  tracks kept), so no published number exercises either.
- Recognition. Two of the 300 replies name the storm: `peak_category/2004223N11301` ("This is
  the Charley 2004 track, which peaked at 130 kt at landfall") and `peak_category/2005289N18282`
  ("This is Hurricane Wilma (2005), which was category 5"). Both also compute the answer from
  the rows (they name the peak wind and its row). No other reply contains its item's season or
  a storm name; the sixty replies with a four-digit "year" are 45 squared, 2025.
- Careless readings, independently: ACE over every row right on 0 of 100, ACE ignoring status
  56, peak ignoring status 100, peak from synoptic rows only 96, hours over every HU row 1,
  matching the report and 0011. Readings the report does not have: ACE from TS and HU only
  (no SS) 91, ACE with "more than 34 kt" 100 (no qualifying row sits at exactly 34 kt, and
  every qualifying wind is a multiple of 5), ACE with TD rows at 34 kt or more 100, peak by the
  mph thresholds applied to kt 30, hours as the span from the first to the last synoptic HU row
  86, hours from any synoptic row at 64 kt or more regardless of status 80. On 0 of the 100
  peak items does a non-HU row hold the highest wind, though 25 have a non-HU row at 64 kt or
  more.
- Tolerance. Dropping or adding one qualifying row is never paid (the smallest row is 34
  squared, 0.1156, more than twice the tolerance). A single 5 kt misread of one qualifying
  wind, answered to one decimal, is still paid on 1,578 of 4,026 such perturbations (39
  percent), on 97 of the 100 ACE items; the items have 1 to 83 qualifying rows, median 15.5.

## 1. Ratings

| Area | Score | Justification |
|---|---|---|
| Correctness | 9 | All 300 keys equal an independent transcription of the prompt's rules over the raw CSV, every row in every item equals the archive, the 300 prompts in the log equal the contract, the logged scores equal the contract on every sample, no name, year or SID leaks, the ledger adds up, and the items and the report regenerate byte for byte. Against that: the prompt says "at 00, 06, 12 or 18 UTC" where the code means "at exactly :00" and 9 items turn on it (M1), and the one-decimal format pays 39 percent of single 5 kt misreads (M2). |
| Minimalism and clarity | 8 | 67, 108, 68 and 76 lines for stats, items, the Inspect task and the contract, stdlib only on the data path, one job each, names that read as prose, the two harnesses sharing one 76-line contract. Clutter: `report._category` repeats `stats.category`'s lookup (`report.py:25-26`), `rlenv.ibtracs.report` and `tasks` import the environment package so `src/` depends on `environments/` (as in Phases 2 and 3), and `render`'s Limits block prints the same sentence twice for peak category. |
| Test coverage | 7 | Eight Phase 4 test files, 88 percent of lines, contract, taskset and stats at 100, the stats and items tests encode hand-computed tracks with every trap (3-hourly row, off-hour landfall row, EX row above the HU peak). Missing: any test that ties the bundled 300 items to the CSV (M4), the error-sample path of `summarize` (`report.py:72,75-77`), a row at a synoptic hour with non-zero minutes (M1), a two-period track for the hours readings (L3), and a harness-equality test over more than one reply. |
| Reproducibility | 8 | The CSV pinned by sha256 with size and Last-Modified, the jsonl by sha256 in a manifest with seed and population, the seeded draw rebuilds the items byte for byte, the report rebuilds byte for byte from the log, the log names a clean commit, the ledger is checked by a test. Gaps: the rebuild is not a test (M4); the source file exists only on this machine and NCEI rewrites it in place, so once the build changes nobody else can rebuild from source (L7). |
| CI/CD | 8 | Green on every Phase 4 push, actions pinned by commit, `--locked --all-groups`, and for this environment `vf-validate`, the mockllm eval and the wheel build run in CI (`ci.yml:26-30`), which Phase 3's review had to ask for. Still: `hatchling` unpinned and no license field (carried), and the data-backed tests cannot run in CI by design. |
| Research rigor | 7 | Six published numbers reproduced and now verified at the live NCEI pages, the SS rule shown to matter by 2024, the trap rates measured and recorded in 0011, the Limits honest about one reply per item and the famous-track channel, the cost settings all verified at Anthropic's pages today, and the ablation the design called for was run the same day. Against that: the shown run is called a baseline though it is a saturated control (M3), the reports' UNKNOWN on recall is answerable from their own logs (two and four replies name the storm), the hidden report says of itself that the hidden ablation "is not run here" and the pair report's headline reads the hours convention gap as room to learn (M5), the tolerance's slack is unreported (M2), the basin and spur rules are exercised by no anchor and 0011 does not say so (L2), and Inspect's default prompt caching added about ten percent to each run's cost without a word in 0010 (L1). |
| Readiness to publish | 6 | The package is sound: 300 of 300 valid, both harnesses on one contract, the wheel builds with its data, the data terms recorded. Not yet: the only version that can measure a frontier model (rules hidden) has not run, the prompt wording in M1, the format decision in M2, LICENSE still absent, and the README's phase row still says the baseline is next. |

## 2. Plain answers to the four questions

**Is the environment saturated for Sonnet 5.5 with the rules in the prompt?** Yes. 299 of
300, a stderr of 0.003, no miss that matches any trap, and 204 of the 300 replies did not use
extended thinking at all (98 of 100 peak replies, 62 of 100 hours replies, 44 of 100 ACE
replies). The one miss is a bookkeeping slip, not a rule error. As a reward for this model the
environment returns 1 on almost every rollout and carries no gradient; it is a regression check
on the keys and the contract, which it passed. The rules-hidden run, which 0011 listed as the
ablation and which ran during this review, does not change that for two of the three
questions: with the rule left out, ACE stays at 0.99 (all 100 replies state the synoptic-hours
and 34 kt convention unprompted; the "TS and HU only" reading that is wrong on 9 of 100 and
the "every row" reading wrong on 100 of 100 caught nobody) and peak category stays at 0.99
(the mph thresholds applied to kt, right on 30 of 100, caught nobody). Only hours fell, to 0.13,
and not for lack of skill: "6 hours per 6-hourly row" is our convention and not a published
rule, and 57 of the 87 hours misses are short by exactly 3 or 6 hours, the two elapsed-time
readings; the same storm (Keith 2000) drew 75 in the probe and 71 in the run from one model.
So the hidden version's 0.703 is a convention gap on one question, which an RL policy would
close as a constant offset in a few steps, not a skill it would learn. What should change so
the environment measures something, in order of how much it would show: (1) decide the hours
convention: keep one sentence of unit for hours in the hidden prompt ("count 6 hours for each
6-hourly row"), or leave hours out of the hidden comparison and say why, and report the hidden
run as "ACE and peak saturated, hours a convention test". (2) Make ACE exact (M2). (3) Put the
dropped
rules back into the data instead of filtering them out: the 13 crossing storms with a basin
column and the rule "only NA rows count", and items with spur tracks, would test rules the
reproduction cannot. (4) Larger counting loads that compound the slip rate: season items
(every storm of one season in the prompt, the season's ACE or hurricane count as the key) are
what NCEI publishes and would need tens of rows summed per item. (5) The rapid-intensification
count that 0011 lists for later, once its rule is tested on hand-computed tracks. Whether a
small or no-thinking policy, the kind an RL loop would train, is also saturated is UNKNOWN:
no such model has run.

**Is the ACE tolerance right?** For the format chosen, yes, and it is the tightest possible:
a correctly rounded one-decimal answer sits at most 0.05 from the exact value, so 0.05 accepts
every correct rounding and both roundings of the 3 tie items, rejects every wrong rounding, and
can never accept a row-selection error, because the smallest qualifying row adds 0.1156. The
weak point is the format, not the tolerance: because the answer is one decimal, a 5 kt misread
of a single wind (the pairs 34 to 39, 35 to 40, 40 to 45, 45 to 50 change the sum by 365 to
475 kt squared, under the 500 the tolerance covers) is still paid 39 percent of the time, on
97 of the 100 items. If exactness is wanted, ask for two decimals with a tolerance of 0.005
(a 5 kt misread then always fails, since it moves the value by at least 0.0365) or for the
integer sum of squares; keep NOAA's one decimal in the report by rounding. Either changes the
prompt, so the 0.997 would not be comparable with a rerun; that is a decision for Aswani, not a
bug.

**Are the careless-reading baselines fair?** Fair, and correctly computed (all five recomputed
independently), but two of the five cannot bite by construction. "Category ignoring status" is
right on 100 of 100 because NHC's HU status is defined by the wind, so no non-HU row ever holds
a storm's peak in this basin; "category from synoptic rows only" misses only the 4 storms whose
peak is a landfall row. 0011 and the report say so and keep the question as a control, which is
honest. Two readings that would bite are not in the report: "ACE from TS and HU only" (right
on 91) is the reading a model that knows CPC's words "tropical storm or greater" and not
NCEI's practice would take, and "category by the mph thresholds" (right on 30) is the reading a
model recalling the scale in the wrong unit would take. Both belong in `careless` so the
hidden run's misses can be classified. The best-constant baselines are right (0.5 on 5, 1 on
35, 12 on 12).

**Is anything in the reports unverified or wrong?** Nothing in the two reports is wrong.
Every number in `2026-11-01-claude-sonnet-5-5.md` recomputes from the log, and the report
rebuilds byte for byte; every number in `2026-11-01-ncei-reproduction.md` recomputes from the
CSV and the published values are on NCEI's pages today. Three things are incomplete rather than
wrong: the Limits line "whether any answer was recalled rather than counted is UNKNOWN" is
answerable from the same log (two replies identify the storm and year, both also compute); the
reproduction says the basin rule is not exercised by the anchors but not that the spur rule is
not either; and `LOG.md:8` and `WORKBOARD.md:86` give the run as $1.3627 where the ledger and
the report give $1.3626 (the difference of two rounded running totals). 0011's "4,082 blank
winds in named storms over all seasons" counts NA rows only (4,084 over all rows); the
sentence does not say which. `WORKBOARD.md:88-90` still says the 300-item hidden run is
"running" after its reports landed at ee3b39f. Two things in the new reports are wrong. The
hidden report (`reports/ibtracs/2026-11-01-claude-sonnet-5-5-rules-hidden.md`, Limits) says
"with the rules in the prompt; the rules-hidden ablation is not run here", which is false for
that file: `render` prints a fixed sentence (`report.py:204-205`) whatever the log's
`task_args`, and neither the title nor the first line says the rules were hidden; only the
filename does. The pair report's headline sentence, "accuracy falls to 0.703: the gap is what
the left-out rules carry, so the rules hidden version has room to learn", reads a convention
gap on one question as room to learn, while ACE and peak did not move; the paragraph under it
(c3a9042) says the right thing about hours and should be the conclusion (M5). Every number in
both new reports recomputes from the hidden log.

## 3. Issues by severity

### High

None found. Nothing changes a key, a score in the log, a published number or a ledger row.

### Medium

**M1. The synoptic rule is stated less exactly than the code applies it, and 9 items turn on
the difference.**
`contract.py:14-16` and `26-27` say "every row at 00, 06, 12 or 18 UTC"; `stats.py:13,31,40`
count a row only when its time is exactly `HH:00:00`. Seventeen rows in 16 items sit at a
synoptic hour with non-zero minutes (`1996-09-06 00:30`, `2019-09-06 12:30`, `2005-07-08
18:45`, `2022-09-30 18:05`, `1999-09-16 06:30` and so on; landfall and peak rows). On 3 ACE
items that row is a named row at 34 kt or more (it would add 1.0000, 0.7225 and 0.2025 ACE,
each more than the tolerance) and on 6 hours items it is an HU row (it would add 6 h), so a
model that reads "at 12 UTC" as "hour 12" is marked wrong on 9 of 200 items while following
the prompt. Sonnet read it as the code does (all 9 right) and the preamble's "extra rows at
other times" helps, but the prompt should not leave it to inference. Smallest fix: "every row
at exactly 00:00, 06:00, 12:00 or 18:00 UTC (a row at 12:30 does not count)" in both rules, the
same words in 0011, and a `12:30` HU row added to `test_keys_follow_the_reference_rules`
(`tests/test_ibtracs_items.py:41-49`) and to `test_each_question_carries_its_own_rule`.

**M2. The one-decimal ACE format pays 39 percent of single 5 kt misreads.**
`contract.py:12-13,49` and `0011` ("rounded to one decimal", tolerance 0.05). Measured above:
1,578 of 4,026 single-wind perturbations by 5 kt still pay 1, on 97 of 100 items; a dropped or
added row never pays. 0011 states what the tolerance accepts (either rounding of a tie, the
unrounded value) and not this. Smallest fix if exactness is wanted: ask for two decimals and
set `TOLERANCE = 0.005` (keys are already kept to four decimals, so nothing else moves), update
the README and 0011, and add a test that a 5 kt misread on a 35 kt row fails; if the NOAA
format is wanted instead, add one sentence to 0011 and to the report's Limits with the 39
percent. Both change what the reward measures, so the choice is Aswani's (0011 says the Fable
review checks the design).

**M3. The saturated run is recorded as the baseline, and the recall question it leaves UNKNOWN
is answered by its own log.**
`WORKBOARD.md:86` ("Sonnet 5.5 baseline ... Saturated with the rules in the prompt"),
`LOG.md:7-10`, and the report's Limits (`report.py:196-197`: "whether any answer was recalled
rather than counted is UNKNOWN"). The run proves the keys, the contract and both harnesses on a
real model, which is worth having, and it measures nothing about the model (section 2). The
log shows two replies naming the storm and year (Charley 2004, Wilma 2005), both peak items,
both also computed from the rows; the famous-track channel 0011 warned about is real, and it
matters more for the hidden run, where a model that recognizes Wilma can answer 5 without
knowing a threshold. The hidden run shows it live: four of its 300 replies name their storm or
its season (Humberto 2025, Wilma 2005, Ernesto 2012, Matthew 2016), and the probe's Wilma
reply says "This storm looks like Hurricane Wilma (2005), whose official peak was 160 kt at
882 mb" before placing 160 kt on the scale. The same UNKNOWN sentence is printed in the hidden
report. Smallest fix: in `summarize`, count the replies whose completion contains
the item's name or season (two lines over `s.output.completion`, the fields are in the
metadata) and print the count in Limits in place of UNKNOWN, with a test on a mockllm reply
that names a storm; in the pair report (`rlenv/ablation.py`) print the same count for the
hidden run; call the shown run the control in WORKBOARD, LOG and the README's phase row.

**M4. No test ties the bundled 300 items to the source data.**
`tests/test_ibtracs_items.py` checks `eligible`, `plan`, `make_item` and `write` on synthetic
rows; the manifest's sha256 was written by the same run it describes. This review rebuilt the
items from the CSV and found them byte-identical, but it did so by hand, as the Phase 3 review
did for ERA5 (its M2). The rebuild is deterministic (`random.Random(2026)` over sorted SIDs) and
takes seconds. Smallest fix: `tests/test_ibtracs_items_data.py` with the reproduction test's
`skipif`, which runs `eligible`, `plan` and `make_item` over `data.read(columns=items.COLUMNS)`
and asserts the jsonl text's sha256 equals the manifest's and `len(storms) == manifest["storms"]`;
about 15 lines, no network, skipped in CI like the reproduction.

**M5. The rules-hidden report misdescribes its own run, and the pair report's headline reads a
convention gap as room to learn.**
`report.py:204-205` prints "with the rules in the prompt; the rules-hidden ablation is not run
here" in every report, so `reports/ibtracs/2026-11-01-claude-sonnet-5-5-rules-hidden.md` says
it of itself; its title ("ibtracs-storm-v1 on claude-sonnet-5-5") and first line are the shown
report's, and a reader learns that the rules were hidden only from the filename. The hidden
log carries `task_args {'rules': False}`, so the report has the fact in hand. In
`rlenv/ablation.py:38-42` the branch on the overall gap writes "the gap is what the left-out
rules carry, so the rules hidden version has room to learn" although ACE and peak did not move
(0.99 and 0.99) and hours fell by convention (section 2); the sentence c3a9042 added under it
is the right reading and is contradicted by the headline above it. Smallest fix: `summarize`
puts `log.eval.task_args.get("rules", True)` into the summary; `render` switches the title
suffix, the first line and the Limits sentence on it; `render_pair` decides per question
(a gap of 0.1 or more on a question whose careless readings explain most of its misses is a
convention gap, named as such) and prints the recognition count from M3 for both runs; one
test each on a hidden mockllm log (`tasks.ibtracs_storm(path, rules=False)`) and on a pair
summary where only one question moves. Then re-render the two reports.

### Low

**L1. Inspect's default prompt caching added about ten percent to the run's cost for no reuse,
and 0010 does not mention it.**
The logged request carries a top-level `"cache_control": {"type": "ephemeral"}` because
`GenerateConfig.cache_prompt` is "Enabled by default" (`inspect_ai/model/_generate_config.py:
153-154`; sent at `model/_providers/anthropic.py:886-887`), and every prompt over Sonnet 5.5's
512-token minimum was billed as a cache write at 1.25x: 539,944 tokens at $1.25 instead of
$1.00 per million under batch is $0.135 more, against $0.002 saved by the 2,137 cached tokens,
so about $0.133 of the $1.3626. The ledger prices it correctly (the cache write column), and
0010's "Generate settings: none but `--batch`" reads as if nothing else was in play. Smallest
fix: one sentence in 0010 under "How we run it", and `--cache-prompt false` on single-turn runs
whose prompts are all different (the CLI flag at `_cli/eval.py:879`).

**L2. The basin and spur rules are exercised by no published anchor and by no item, and only
one of the two is disclosed.**
`reports/ibtracs/2026-11-01-ncei-reproduction.md:37-38` says counting every row of each storm
gives the same numbers; keeping spur tracks does too (checked on 1933, 2005, 2020, 2024 and
2025), and the report does not say so. `items.eligible` (`items.py:30`) drops the 13 storms
with a row outside the basin and would drop spur rows, so the environment cannot test either
rule. Smallest fix: one sentence on spurs in the reproduction's Limits, one in 0011 saying the
population carries two of the five rules (synoptic hours, status) and the 34 kt threshold
(which no item reaches at exactly 34 kt), and the crossing storms as a later item type.

**L3. The peak baselines cannot bite, and the two readings that would are missing.**
`report.py:40-46`. "Category ignoring status" is right on 100 of 100 by construction (no
non-HU row holds any peak); the report says the question is "mostly a control", which is fair.
"ACE from TS and HU only" (right on 91) and "category by the mph thresholds applied to kt"
(right on 30) are the readings a model that knows the words but not the practice would take,
and they are the ones the hidden run needs for its trap table. The hours reading added in
039dde5 ("elapsed time, first to last HU row", `report.py:48-53`) does not catch the misses
the hidden probe produced: for Keith and Olga it gives 126 and 60 against the model's 75 and
63, and it is right on 1 of the 100 items, so the hidden run's trap table will show 0 for it
while every hours miss of this kind goes unclassified. The reading the model used, "each row's
status holds until the next row" (the sum of the gaps from every HU row to the row after it),
reproduces both answers exactly and is right on 36 of 100. Smallest fix: add the TS-and-HU-only
ACE reading, the mph-threshold peak reading and the holds-until-next-row hours reading to
`careless`, each with a test row (`tests/test_ibtracs_report.py:31-42`; the hours one on a
two-period track), replace or keep the first-to-last reading, and list them in 0011.

**L4. Two prompt sentences are looser than the code on cases the population cannot produce.**
`contract.py:22` "A storm with no HU row is 0" where `stats.category` returns 0 for any peak
under 64 kt (an HU row at 60 kt would be category 0 by the code and undefined by the prompt);
no such row exists among the 613 storms. Smallest fix: "A storm with no HU row at 64 kt or
more is 0". And the legend lists nine statuses while IBTrACS USA_STATUS has others (NR, MX, PT
and more); none appears in the items, and the eligibility test guards it only indirectly, so a
one-line assertion in the items test that every status in the 300 items is in the legend would
hold the line.

**L5. Record drift.**
`README.md:16` says "the Sonnet 5.5 baseline is next" after the run and its report landed
(20ae417). `LOG.md:8` and `WORKBOARD.md:86` say $1.3627; the ledger and the report say $1.3626
(1.36262685), the 0.0001 being the difference of two rounded running totals. 0011 line 20:
"4,082 blank winds in named storms over all seasons" is the count over NA rows (4,084 over all
rows of those storms); say "NA rows". The reproduction report names commit e640dc7 for
`stats.py`, which changed in 2a9802f (`category`) and whose numbers still hold at HEAD
(verified). Smallest fix: one line each.

**L6. Carried from earlier phases, and small test gaps.**
`hatchling` unpinned at `environments/ibtracs_storm_v1/pyproject.toml:10` with no
`docs/decisions` record and no `license` field; LICENSE absent at the repo root (the third
environment wheel now ships without one). `summarize`'s error path (`report.py:72,75-77`) and
the empty-group `continue` (line 86) are untested; `report._category` (`report.py:25-26`)
duplicates `stats.category`'s lookup and could call it on a one-row list. The harness-equality
check (`tests/test_ibtracs_harnesses.py:42-50`) covers one task and three replies; the Phase 3
review's 720-pair test is the pattern.

**L7. The source file cannot be re-obtained by anyone else once NCEI rewrites it.**
`data.py:5-6,22-24`: the pin is "our own sha256 of the build we fetched, and the copy under
data/ is the one we keep". `data/` is ignored by git and NCEI "overwrites its files in place"
(verified in the radar at the listing level). The environment itself is safe, since the jsonl
is in git with its sha256, but M4's test and any rebuild from source will fail for every other
machine as soon as NCEI publishes a new build, and nobody can then check that the 300 items
came from a real archive. Smallest fix: attach the pinned CSV (57.6 MB) or the 613 eligible
tracks as a GitHub release asset with the sha256, and name it in `data.py` and the README.

## 4. What is missing to close Phase 4

1. The rules-hidden result read for what it is. The run is done (0.703, $1.7800, ledger row at
   01f1074, reports at ee3b39f): M5's template fix and the two reports re-rendered, with the
   recognition count (M3) and the extra careless readings (L3) in the trap tables; one
   paragraph in 0011 saying that ACE and peak are saturated with the rules hidden too and that
   hours hidden is a convention test (57 of 87 misses short by exactly 3 or 6 hours), with the
   decision on the hours convention from section 2; WORKBOARD and LOG brought up to the
   result. The ablation answered its question within $1.78; the answer is that this
   environment, shown or hidden, does not grade Sonnet 5.5's skill on two of its three
   questions, and that is the finding to publish.
2. M1 and M4 test-first; M2 as a recorded decision (two decimals, or the 39 percent stated in
   0011 and the report).
3. M3's record changes: the shown run named as the control in WORKBOARD, LOG and the README's
   phase row; the Limits line replaced by the count.
4. L1 to L7, each a line or two.
5. Still open from earlier phases: LICENSE and the package license fields, `hatchling`.

## 5. What I would not publish yet, and why

- "Sonnet 5.5 scores 0.997 on ibtracs-storm-v1" as a result about the model. It is a result
  about the paper: the rules are in the prompt, 204 of 300 replies did not think, and the
  one miss is a counting slip. Publish it as the rules-shown control beside the hidden run.
- "whether any answer was recalled rather than counted is UNKNOWN". Two replies say "This is
  Hurricane Wilma (2005)" and "This is the Charley 2004 track"; the count is in the log.
- "exact answers" for ACE without the qualification: the format pays 39 percent of single 5
  kt misreads.
- The reproduction's rule list as verified: the SS rule is verified by 2024, the synoptic rule
  by every season, the basin and spur rules by nothing.
- "The rules hidden version has room to learn" (`reports/ibtracs/2026-11-01-rules-shown-vs-
  hidden.md`). The room is one question's convention: ACE and peak are at 0.99 with the rules
  hidden, and 57 of the 87 hours misses are short by exactly 3 or 6 hours.
- The hidden report's Limits as written: "the rules-hidden ablation is not run here" in the
  report of the rules-hidden run.
- The hours question with the rules hidden as a knowledge test. It is a convention test.
- The environment wheel without a license field and the repo without a LICENSE.
- The README's phase row and the $1.3627 in LOG and WORKBOARD, as written.
