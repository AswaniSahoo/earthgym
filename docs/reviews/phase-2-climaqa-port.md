# Phase 2 review: clean ClimaQA port (Inspect tasks and verifiers taskset)

Reviewed 2026-10-30 against commit `5cf7ce1` on `main` (working tree clean). Baselines have not
run, so this review covers the clean set, the two task ports, their tests, docs and CI. Everything
below was run or read during the review; nothing is taken from memory. Where a claim could not be
checked it is marked unknown.

What was run: `uv run pytest -q` (35 passed), `uv run ruff check .` (clean), `uv run ruff format
--check .` (28 files clean), `uv lock --check` (clean), the clean step twice into
`/tmp/rlenv-review-clean` with `--reports` pointed at the same directory so no tracked file was
touched (both runs byte-identical to each other, to `environments/climaqa_v1/climaqa_v1/climaqa_v0.jsonl`,
to `data/clean/climaqa_v0.jsonl` and to `reports/climaqa/clean_v0_manifest.json`; sha256 of the
jsonl `99f1b3893ed050a09e998f897ba58d0ff751fc52103c7ec9dbe5f1cd50211471`), a field by field
cross-check of all 377 kept records against the raw CSVs in `data/climaqa` plus 12 named items
(gold MCQ 0, 1, 20, 34, 157, 236, 291; gold cloze 1, 2, 22, 51, 159), both Inspect tasks and the
verifiers taskset loaded in Python, 38 MCQ replies and 76 cloze replies scored by both frameworks
side by side, the documented `inspect eval` CLI command, the README `vf-eval` command as a
`--dry-run`, `vf-validate climaqa-v1 --only-noop --runtime.type subprocess` (377 of 377 valid), a
wheel build of `environments/climaqa_v1` (the jsonl is inside), `uv run --with pytest-cov pytest`
(84 percent lines) and `gh run list` (the last five CI runs on `main`, all green, newest
2026-10-30T07:22Z). Pins verified in `uv.lock`: `inspect-ai 0.3.286`, `verifiers 0.4.0`,
`pytest 9.2.0`, `ruff 0.17.3`. No em or en dash in any Phase 2 prose file; the 12 inside the jsonl
are source text.

## 1. Ratings

| Area | Score | Justification |
|---|---|---|
| Correctness | 6 | The data transform is exactly right: 377 of 377 records match the raw CSVs (question, option order, uppercase key, complexity, Validation=True, 11 of the 12 trailing-punctuation cloze keys cleaned, the 12th is an excluded leak), and both shuffles keep the key honest on all 226 MCQ items. Against that: the documented Inspect CLI command does not run, the verifiers MCQ reward disagrees with Inspect on 14 of 38 tricky replies including verified false positives, 25 kept items print their answer inside the prompt, and two "All of the above" items are shuffled into nonsense positions. |
| Minimalism and clarity | 8 | 82, 44 and 86 lines for the three new modules, one job each, names that read as prose. Two copies of the clean set (one gitignored), a duplicated `words()`, and a relative dataset path are the only clutter. |
| Test coverage | 5 | 35 tests, 84 percent lines, but the paths that decide the numbers are untested: the default `CLEAN_SET`, the `shuffle=True` default of the MCQ task, `ClimaqaTask.correct` (lines 42 to 43, never executed by a test), `clean.main`, and there is no contract test that the two scorers agree. |
| Reproducibility | 7 | Byte-identical rebuilds from pinned data, fixed seeds, lockfile, SHA-pinned actions. But the manifest does not record the output hash, records carry no dataset revision, the Inspect task reads a gitignored copy, and Inspect's shuffle re-rolls 220 of 225 later items when one earlier item is removed, so the next clean-set version will change nearly every MCQ letter. |
| CI/CD | 8 | Green on GitHub for every Phase 2 push, `--all-groups` so both frameworks are exercised offline, runner and actions pinned. No wheel build, no `vf-eval --dry-run` or `vf-validate` smoke, `hatchling` unpinned. |
| Research rigor | 6 | Decisions recorded and dated, radar entries sourced, the "published scores use the unfiltered file" finding is real and useful, the 12 trailing-punctuation keys are real. But "clean" is overstated (24 giveaways and 24 near matches retained without disclosure), the two frameworks measure different contracts without saying so, nothing documents that `exact()` drops articles and splits hyphens, and the longest option is the key in 89 of 226 MCQ items (39 percent) with no mention anywhere. |
| Readiness to publish | 4 | Code is close, the artefact is not: the CLI recipe fails, the scorers disagree, the content decisions (giveaways, near matches, all-of-the-above) are open, no baseline, no report template, no LICENSE. |

## 2. Issues by severity

### High

**H1. The documented Inspect command fails, and the file it reads is not in the repo.**
`src/rlenv/climaqa/tasks.py:11` sets `CLEAN_SET = "data/clean/climaqa_v0.jsonl"`, a relative path.
Inspect runs a task with the task file's directory as working directory
(`inspect_ai/_eval/run.py:251`, `with chdir(task_run_dir(...))`), so
`uv run inspect eval src/rlenv/climaqa/tasks.py@climaqa_mcq --model mockllm/model` from the repo
root raises `FileNotFoundError: /data/rlenv/src/rlenv/climaqa/data/clean/climaqa_v0.jsonl`
(verified for both tasks, and from another directory). The in-process tests never hit this because
both pass an absolute `tmp_path`. Worse, `data/` is gitignored (`.gitignore:13`), so a fresh
clone has no `data/clean/` at all and the only tracked copy is
`environments/climaqa_v1/climaqa_v1/climaqa_v0.jsonl`. Smallest fix: in `tasks.py`,
`CLEAN_SET = str(Path(__file__).resolve().parents[3] / "environments/climaqa_v1/climaqa_v1/climaqa_v0.jsonl")`,
make `--out` in `clean.py:67` default to that package directory so there is one copy, and add a
test that `tasks.climaqa_mcq()` and `tasks.climaqa_cloze()` with no arguments load 226 and 151
samples.

**H2. The verifiers MCQ reward and Inspect's `choice()` disagree, and the reward has false positives.**
`environments/climaqa_v1/climaqa_v1/taskset.py:20-21` takes the last standalone capital letter
A to D. Inspect's `multiple_choice()` template demands `ANSWER: $LETTER`
(`inspect_ai/solver/_multiple_choice.py:17-18`) and `parse_answers` (lines 111 to 121) accepts
only that marker, case-insensitively, with `$A$`, `**A**` and `(A)` wrappers tolerated, taking the
last `ANSWER:` line. Side by side on one item with key A, 14 of 38 replies disagree:

| reply | Inspect | verifiers |
|---|---|---|
| `A`, `A)`, `(A)`, `**A**`, `A) Warm air rises`, `The answer is A.` | 0 (Incorrect) | 1 |
| `answer: a` | 1 | 0 |
| `ANSWER: C. A warm parcel is less dense.` | 0 (parsed C) | 1 (the article "A") |
| `Option C is right. A cold front is irrelevant.` | 0 | 1 |
| `ANSWER: B` then `Actually ANSWER: A` on the next line | 0 (strict regex takes B) | 1 |
| `ANSWER: A`, `ANSWER: A.`, `ANSWER: A)`, `B\nANSWER: A` | 1 | 1 |
| `ANSWER: A, B`, `ANSWER: AB`, `ANSWER: E`, empty, `Warm air rises.` | 0 | 0 |

So the reward is too lenient wherever an explanation follows the letter (a sentence-initial "A" or
a "Vitamin D" flips it) and too strict on lowercase. The prompts also differ (`taskset.py:11`
"Answer with only the letter" versus Inspect's template), so a compliant model is scored under two
different contracts. Smallest fix: adopt one contract in both places. Use Inspect's template text
as `MCQ_PROMPT` and `letters = re.findall(r"(?i)answer\s*:\s*\(?([A-D])\)?", reply)` with the
last match, in `mcq_reward`; change the expectation at `tests/test_vf_taskset.py:11` ("It is a B"
becomes 0.0); and add a contract test that runs the same reply list through
`tasks.climaqa_mcq(shuffle=False)` on `mockllm` and through `mcq_reward` and asserts equality.
Record the choice in `docs/decisions/0004`.

**H3. 25 kept items contain their own answer in the prompt.**
`clean.py:20-22` excludes only findings with `kind == "defect"`; `cloze.answer_in_question` and
`mcq.answer_in_question` are flags, so the clean set keeps 23 cloze items whose key appears
verbatim elsewhere in the sentence (gold/cloze/2 key "Stratiform" with "stratiform precipitation"
later in the sentence; gold/cloze/143 key "kriging" in a sentence that begins "Kriging is";
gold/cloze/39 key "extrema" with "finding extrema" later; gold/cloze/21 key "hPa"), plus
gold/mcq/34 whose keyed option is the question's own clause. gold/mcq/173 (key text "organic
molecules" inside the question) sits below the three-word threshold at `checks.py:93` and was
never flagged. That is 15 percent of the cloze split answerable by copying, inside an artefact
named "clean" and used as an RL reward. Smallest fix: in `clean.py` add
`GIVEAWAYS = {"cloze.answer_in_question", "mcq.answer_in_question"}` and change line 21 to
`if f["kind"] == "defect" or f["check"] in GIVEAWAYS:`, lower the MCQ threshold at
`checks.py:93` to two words, bump `VERSION` to `v1`, regenerate, and update the counts in
`environments/climaqa_v1/README.md:3`, `tests/test_vf_taskset.py:30,38` and `WORKBOARD.md:8`.
Test: a row with a giveaway flag is excluded with that reason. If Aswani wants them kept, each
record needs a `flags` list and the README must say so; silence is the bug.

### Medium

**M1. Shuffling breaks the two "All of the above" items.**
gold/mcq/236 (key "All of the above", raw position a) lands at C under the Inspect shuffle and at
C under the verifiers shuffle, with option D printed below it; gold/mcq/20 stays at D in both by
luck. A positional option cannot be shuffled. Smallest fix: exclude `mcq.all_or_none_of_above`
items in `clean.py` (two items; 236 was already degenerate per the Phase 1 review, L6). The
alternative, pinning that option last, cannot be expressed in Inspect's dataset-level shuffle.

**M2. 24 kept items are unreviewed near matches of Silver.**
`leak.near_match` flags (word-set Jaccard at or above 0.8) sit on 12 kept MCQ and 12 kept cloze
items (gold/mcq/32, 63, 117, 157, 169, 183, 187, 200, 213, 234, 263, 286; gold/cloze/1, 18, 22,
88, 91, 95, 99, 106, 137, 152, 155, 157). `reports/climaqa/leak_review.csv` is still unfilled
(`WORKBOARD.md:19`). `environments/climaqa_v1/README.md:3-5` says the verbatim copies were
removed and says nothing about these. Smallest fix: one README sentence now, and a `flags` field
per record so a report can split them; exclude or clear them after the hand-check.

**M3. Inspect's shuffle is position-dependent; the two frameworks show different option orders.**
`Dataset.shuffle_choices` (`inspect_ai/dataset/_dataset.py:346-365`) draws from one
`random.Random(seed)` across the samples in file order. Verified: deleting one MCQ item from the
file changed the option order of 220 of the 225 items after it; cloze rows do not consume draws.
The verifiers taskset seeds per item (`taskset.py:74`), so the same item has a different order
and letter in each framework (gold/mcq/0: Inspect lists the keyed option third, verifiers third
too, but the other three differ). Consequences: per-item results are not comparable across the
two ports, and the v1 set that H3 and M1 force will re-roll almost every Inspect letter. Smallest
fix: shuffle once in `clean.py` with `random.Random(f"{SEED}:{id}")`, store the shuffled options
and remapped key in the jsonl, record the seed in the manifest, pass `shuffle_choices=None` in
`tasks.py:27` and delete lines 72 to 74 and 83 of `taskset.py`. One shuffle, two consumers,
stable per item.

**M4. Cloze normalisation differs between the two scorers.**
Inspect's `exact()` calls `_normalize` (`inspect_ai/scorer/_classification.py:160-192`): split
on space or hyphen, casefold, strip punctuation per token, normalise numbers, remove articles.
The verifiers `words()` (`taskset.py:24-25`) keeps articles and splits "1.5" into "1 5". Verified:
"the evaporation" scores 1.0 in Inspect and 0.0 in verifiers; the other 11 synthetic variants and
all 64 real-key variants agree. No numeric key exists today, so the number difference is latent.
Both scorers accept "ice nucleating" for "ice-nucleating" and "500 hPa" for "500-hPa", and both
reject "icenucleating" and "500hPa", which is a realistic model spelling. Plurals: both reject
"cyclone" for "cyclones"; 24 of 151 keys end in s, and in three kept items the other number of the
key already appears in the sentence (cloze/51 "Aerosols" with "aerosol", 84 the reverse, 108
"feedbacks" with "feedback"), so sentence grammar usually fixes the number and strict matching is
defensible if disclosed. Smallest fix: strip a leading article in `cloze_reward`
(`re.sub(r"^(a|an|the) ", "", words(reply))`), add "the evaporation" to
`test_cloze_reward_ignores_case_and_punctuation_but_not_meaning`, and give the four hyphenated
keys a concatenated alias through Inspect's list target (`exact()` accepts a list) and a list in
`ClimaqaData.answer`. Do not add a stemmer.

**M5. The tests skip the paths that decide the numbers.**
`tests/test_tasks.py:43` passes `shuffle=False`; the task default is `True` and the target remap
after `shuffle_choices` is exactly the thing that could silently break (it is correct today: 0
mismatches on 226 items, verified in this review, not by a test). `taskset.py:42-43`
(`ClimaqaTask.correct`) is at 0 percent; only my `vf-validate --only-noop` run exercised it.
`clean.py:65-77` (`main`, both files written) is untested. Nothing asserts that the bundled jsonl
is the one `clean` produces. Smallest fix: a shuffled-load test that maps each target back to the
original key text, a test that builds a `vf.Trace` (or calls `correct` with a stub exposing
`last_reply`) for one MCQ and one cloze task, a `main` test on `tmp_path` with the inline fixture,
and a manifest `sha256` asserted against the bundled file.

### Low

**L1. The README `vf-eval` recipe records the wrong model.**
`environments/climaqa_v1/README.md:18-19` omits `-m`; the dry run resolved
`model = 'deepseek/deepseek-v4-flash'` and named the run directory after it, so a llama.cpp run
would be logged under that name. Add `-m <served model name>`. The help spells the client flag
`--client.base-url`; `base_url` was accepted, so this is cosmetic.

**L2. Packaging gaps.**
`environments/climaqa_v1/pyproject.toml:9` `hatchling` unpinned (not in `uv.lock`, build
backends are not locked) and without a `docs/decisions` record, which `CLAUDE.md` requires for
every dependency; the root uses `uv_build` with a range. No `license` or `readme` field, so the
wheel METADATA carries neither; the package redistributes Apache-2.0 data and should say so.
`requires-python = ">=3.11"` is wider than anything tested (3.12 only).

**L3. The manifest and records are not self-describing.**
`clean.py:52-61` writes reasons but not the output sha256, the source row counts (292 MCQ, 160
cloze) or the seed; records carry no dataset revision, which the Phase 1 review asked for, and
the wheel ships only the jsonl plus code. Add `sha256`, `source_rows`, `seed` to the manifest and
a `source` field (repo and revision) per record.

**L4. Two normalisers will drift.**
`taskset.py:24-25` duplicates `checks.py:45-47` because the package must be self-contained. Say
so in a comment, or remove the need by moving all text shaping into the jsonl (M3).

**L5. Documentation drift.**
`docs/decisions/0002:10-11` and `docs/radar.md:10` describe `exact()` as normalising without
saying it removes articles and splits on hyphens, which decides cloze scores. `WORKBOARD.md:10`
"no custom code" is true for Inspect only; the RL env has custom rewards (`taskset.py:18-30`).
`tasks.py:40` sends the cloze instruction as a system message with "the climate science
statement", `taskset.py:12-15` puts it in the user turn with "this": unify when fixing M3.

**L6. CI could catch what this review caught.**
`.github/workflows/ci.yml` runs lint, format and tests. `uv build environments/climaqa_v1`,
`uv run vf-eval climaqa-v1 --dry-run --no-push` and `uv run vf-validate climaqa-v1 --only-noop
--runtime.type subprocess` all ran clean offline in under a minute and would catch packaging,
plugin discovery and reward wiring regressions. The documented `inspect eval` command with
`--model mockllm/model --limit 3` would have caught H1.

## 3. What is missing to close Phase 2

Before baselines run, in this order, because every content change re-rolls the numbers:

1. Fix H1 (the CLI must run from a fresh clone), then decide H3, M1 and M2 (what the clean set
   contains) and cut `v1` of the set. Running baselines on v0 and then changing the set means
   running everything twice.
2. Fix H2 and M3 so the Inspect task and the verifiers taskset share one prompt, one option
   order and one parser, and record the contract in `docs/decisions/0004`. Until then an Inspect
   accuracy and a `vf-eval` reward are not the same number and must not be put in one table.
3. Model access (`WORKBOARD.md:21-22`, owner's call). The pipeline needs a first real log more
   than it needs a strong model: the radar's local option (llama.cpp with a Qwen3.5 4B GGUF on
   the RTX 3050) costs nothing and is enough to shake out the run config; add one API model
   (Groq free tier or Vertex from the credit) for the second log the Register asks for.
4. A run config, fixed before the first run and copied into the report: for Inspect,
   `--temperature 0`, an explicit `--max-tokens` large enough for the `ANSWER:` line (reasoning
   models put it after their thinking), `--seed`, `--epochs 1`, `--log-dir logs/<date>`,
   `--log-format eval`, plus the Inspect version, the task file git SHA, the model id and
   provider, and the jsonl sha256; for `vf-eval`, `-m`, `-r 1`, `--no-push`, the sampling
   temperature and `-o`. Report `choice()` reasons separately (empty reply versus wrong format
   versus wrong letter), because the strict `ANSWER:` contract will drive small-model numbers.
5. A report template, `reports/climaqa/baselines_<date>.md`: the config block above, one row per
   model and task with n, accuracy, stderr, format-failure count, cost and log path, the
   letter-balance and longest-option lines (after shuffle: Inspect A 47, B 56, C 58, D 65;
   verifiers A 62, B 51, C 52, D 61; the key is the longest option in 89 of 226 items), and a
   limitations paragraph (exact match, near matches, giveaways if kept).
6. M4, M5 and the Low items, test-first, before the phase closes. LICENSE remains open from
   Phase 1 and now also gates the environment package.

## 4. What I would not publish yet, and why

- The word "clean" or "leak-free" for v0. 25 items hand the answer to the model in the prompt and
  24 are unreviewed near copies of the fine-tuning split.
- Any MCQ reward produced by the current `mcq_reward`. It scores "ANSWER: C. A warm parcel is
  less dense." as correct for key A.
- Any table that puts an Inspect accuracy next to a `vf-eval` reward as the same measurement.
  Different prompt, different option order, different parser, different normaliser.
- The `tasks.py` docstring command and the README `vf-eval` recipe as written. One fails, the
  other records the wrong model name.
- The sentence at `taskset.py:49`, "a policy cannot learn answer positions", without the
  qualifier that the longest option is the key 39 percent of the time and that D is the key in
  29 percent of the Inspect-shuffled items.
- Per-item comparisons across clean-set versions under Inspect's shuffle, until M3 is fixed.
- Anything built on the radar's external numbers (prices, rate limits, the Scientific Agents
  score) without a fresh fetch: this review did not re-verify them. The two framework claims it
  relies on (Inspect never shuffles by itself, verifiers 0.4.0 exposes `verifiers.v1`) are
  confirmed by the installed source.

## Author response (2026-10-30)

Each fix landed test-first.

| Issue | Fix | Commit |
|---|---|---|
| H1 default Inspect path broke after Inspect's chdir; two copies of the set | tasks read the bundled set through `climaqa_v1.taskset.records()`; one copy; test runs from another directory | 241f3ff |
| H2 MCQ reward disagreed with Inspect's `choice()` | one contract (`climaqa_v1/contract.py`) imported by both harnesses: last line must be only `ANSWER: X`; decision 0004 | 241f3ff |
| H3 kept items gave their answer away; gold/mcq/173 unflagged | leak rule now flags a key that alone appears in the question at any length; answer-in-question flags exclude | bacba2a, 047f016 |
| M1 "all of the above" moved by the shuffle | all/none items excluded | 047f016 |
| M3 Inspect's shuffle depended on neighbours and differed from verifiers | options shuffled once in `clean.py`, seeded by item id, stored in the set; no harness shuffles | 047f016 |
| M4 cloze normalization differed between harnesses | SQuAD-style rule in the contract for both; plurals still count as wrong (documented) | 241f3ff |
| M5 untested paths and no checksum | tests for the default path, the task reward, `clean.main`, and the bundled set against its manifest sha256 | 241f3ff, d258f01 |
| Missing run config and report template | `rlenv.climaqa.report` turns logs into a dated report with format failures and accuracy by complexity; logs stay out of git | 3c70706 |

Clean set v1: 350 items (222 MCQ, 128 cloze), 102 exclusions with reasons, keys spread A 60, B 51, C 51, D 60.
Open: LICENSE at publish time; a second model's logs for the inspect_evals Register.

## Baseline review (2026-10-30)

Reviewed at commit `121596e` on `main` (tree clean, equal to `origin/main`). Eight commits landed
while this review ran (6c897ac, 770a778, 495063c, c376553, 5a845c5, e44123f, 6ac9c47, 121596e,
all after 7a18923), so every check below was repeated at 121596e. The run itself is recorded at
3c70706 (dirty); its logs sit in `logs/2026-10-30-gemini-3.8-flash/` (gitignored, this machine
only).

What was run: `uv run pytest -q` (60 passed), `uv run ruff check .` (clean), `uv run ruff format
--check .` (37 files clean), `uv lock --check` (clean), `gh run list` (the six newest runs on
`main` green, newest 121596e at 2026-10-30T11:19Z). Both `.eval` files read with
`inspect_ai.log.read_eval_log` (inspect_ai 0.3.286, both `status success`, 128 and 222 samples,
no sample errors, no empty replies). Recomputed from the samples and matched to the report:
correct counts (95 of 128, 194 of 222), accuracy, stderr (from `results`), n and accuracy per
complexity level (BASE 97 of 107, HYPOTHETICAL 39 of 46, REASONING 58 of 69), per-sample token
sums against `stats.model_usage` (equal: 7355 / 93511 / 93278 and 24284 / 121121 / 108017, so
docs/log.md's 89.2 and 99.8 percent reasoning shares are right), MCQ format failures (all 222 replies
end in a line the contract parses), `eval.revision` (3c70706, dirty) and the generate config
(every field None in both `eval.model_generate_config` and `plan.config`). All 350 logged inputs
equal `contract.mcq_prompt` or `contract.cloze_prompt` over the bundled jsonl, all 350 targets
equal the keys, and the contract at 121596e reproduces all 350 verdicts; the jsonl sha256 equals
the manifest and the report (`5f345d8e...`). `uv run python -m rlenv.climaqa.report
logs/2026-10-30-gemini-3.8-flash --out <scratch>` reproduced the committed `.md` and `.json` byte
for byte. A blind sort of the 33 cloze misses was written to
`/tmp/claude-1000/-data-rlenv/4d714d75-e1d0-4566-82bd-f40bd67e6f3a/scratchpad/blind_sort.md`
before the author's note, docs/log.md or WORKBOARD.md were opened; the table below is the durable
record. Six MCQ misses were read by eye against the jsonl (gold/mcq/102, 110, 113, 125, 130, 132).
The AMS Glossary sentence quoted in the note for item 47 is verbatim at
glossary.ametsoc.org/wiki/Coagulation, sense 1. The DOI cited for item 72 resolves (via
link.springer.com) to "On a controversial method for modeling a coregionalization", Mathematical
Geology, 1994; whether that text uses "direct variogram" is UNKNOWN (paywall). Inspect's config
precedence was checked in the installed source (L2).

### 1. Ratings

| Area | Baseline report | Cloze note | Justification |
|---|---|---|---|
| Correctness | 9 | 8 | Every number in `reports/climaqa/runs/2026-10-30-gemini-3.8-flash.md` reproduces from the logs and the bundled set. The note agrees with a blind sort on 31 of 33 buckets; its one firm claim, a "clear model error" at 157, is asserted, not shown (M1). |
| Minimalism and clarity | 8 | 8 | 122 lines of code, one table per concern; the "Runs ... at" line prints the same creation time for both tasks (L1). The note states its bucket rules, gives a reason per item and an accuracy-under-each-reading table, which is the right artefact. |
| Test coverage | 7 | n/a | Eight tests cover counts, n per level, n/a for cloze, the config string, tokens, the log name and the unknown case. Not covered: an eval setting overriding the model's own on the same key (L2), `main()` (L5). |
| Reproducibility | 6 | 7 | Dirty tree, provider defaults, no seed, no command line in the report (M3); the logs are gitignored so only this machine can regenerate. Mitigated: HEAD reproduces every prompt and verdict. The note is one reader's sort with explicit rules; a blind second reader reproduced 31 of 33. |
| CI/CD | 8 | n/a | Green on every commit. CI never runs `rlenv.climaqa.report` on a real log; a two-sample mockllm fixture would close that. |
| Research rigor | 7 | 8 | The report has no limitations paragraph, no letter balance or longest-option line (section 3 item 5 above), and no link to the miss note. The note hedges well ("25 to 32") but decision 0005 rests on it without an equivalent read of the 28 MCQ misses (M2). |
| Readiness to publish | 6 | 7 | A sound first log, not yet a benchmark number. The note is publishable once 157 is relabelled and the expert check is stated as open. |

### 2. Issues by severity

No High. Nothing found changes the two headline numbers.

#### Medium

**M1. gold/cloze/157 is labelled "model error" without evidence.**
`reports/climaqa/runs/2026-10-30-gemini-3.8-flash-cloze-misses.md:84` says "names a different
curve for a specific study", but the sentence names no study and the note cites none. The note's
own rule for sentences about a specific paper or book is "other, debatable": 101 (line 72, the
Brenguier et al. 1994 review), 59 (line 64) and 144 (line 82, the geostatistics book). "A time
series analysis was conducted to fit a sinusoidal curve to the seasonal variation" is a standard
method and nothing in the sentence rules it out, so by the note's definitions it is "other
correct word, debatable" until the study's method is cited. The label propagates to line 31,
line 43 ("1 clear"), docs/log.md:21 ("1 is a clear model error (157)"), WORKBOARD.md:16 and
`docs/decisions/0005-cloze-in-clean-set-v2.md:10` ("Only 1 to 8 are wrong"). Smallest fix:
relabel 157 "other, debatable" (or cite the source that shows a spline fit and keep it), and
change the five counts to 0 to 8 wrong, 25 other correct words (8 debatable).

**M2. Decision 0005 moves the RL reward to MCQ on the strength of the cloze sort alone.**
`docs/decisions/0005-cloze-in-clean-set-v2.md:6-12` cites only the cloze misses; the 28 MCQ
misses have had no equivalent read. Of the six I read against the jsonl, my reading is: two keys I
would dispute (gold/mcq/125, key C says Lagrangian models "focus on modeling large-scale climate
processes" while the model's D, tracking air parcels, is the defining property; gold/mcq/102, a
HYPOTHETICAL item where C and D both follow from the premise), one item that is not a science
question (gold/mcq/132, which person is absent from a book's acknowledgments), and three where
the key is defensible and the model is wrong (110, 113, 130). If 2 of 6 holds across 28, the MCQ
reward carries key errors of the same order as the cloze reward carries alternative answers.
Smallest fix: a second note that sorts the 28 MCQ misses into key wrong / ambiguous / model
error, cited from 0005 before Aswani decides it.

**M3. The run is not reproducible as recorded, and the report does not say so.**
`2026-10-30-gemini-3.8-flash.md:25-26` records `3c70706 (dirty)` and `provider defaults`; the
report says nothing about what either means. docs/log.md:14-16 does ("a rerun need not match") but a
reader of the report alone cannot know that no temperature, seed or max_tokens was set, which
section 3 item 4 above asked for before the first run. What the dirty state could have touched is
UNKNOWN (inspect records only the flag); what it did not change is verified: `environments/` and
`src/rlenv/climaqa/tasks.py` are identical between 3c70706 and 121596e (`git diff --stat`), and
HEAD's contract and set reproduce all 350 prompts and verdicts. Smallest fix: in `render()`
(`src/rlenv/climaqa/report.py:83-84`) add one sentence when any commit ends in "(dirty)" or any
config is "provider defaults": "uncommitted changes at run time, contents unknown; sampling
settings were the provider's defaults, a rerun need not match". Run the second model from a clean
tree with `--temperature 0 --seed <n> --max-tokens <m>` and keep the command in the report.

**M4. Seven kept items test the source document, not climate science, and all feed the reward.**
A grep of the bundled jsonl for acknowledgments, chapter and book terms returns five items:
gold/mcq/56 ("Which publication ... is referenced in the"), gold/mcq/132 (acknowledgments),
gold/mcq/215 ("What is the focus of the book Geostatistics for Environmental Scientists"),
gold/cloze/59 ("supported by the theoretical framework provided in each chapter") and
gold/cloze/144 ("The focus of the book remains on"). The note (lines 98 to 100) already flags the
two cloze keys that are a parenthesised acronym of the words before the mask (gold/cloze/8, 22;
verified as the only two of 128). Smallest fix: two checks in the Phase 1 audit, `source_metadata`
(question or options mention the book, a chapter, acknowledgments or a referenced publication)
and `cloze.key_is_parenthesised_acronym`, both excluded in v2 and counted in the manifest.

#### Low

**L1. The "Runs" line prints the eval creation time, not the run time.**
`2026-10-30-gemini-3.8-flash.md:28` shows both tasks "at 2026-10-30T09:02:52+00:00" because
`report.py:32,95` use `log.eval.created`, which is the same for every task of one `inspect eval`
call. `log.stats.started_at` and `completed_at` say MCQ ran 09:02:52 to 09:21:32 and cloze
09:21:32 to 09:33:14. Smallest fix: record `started_at` and `completed_at` in `summarize` and
print those.

**L2. The config precedence is right but untested on a shared key.**
`report.py:26-27` composes `model_generate_config.merge(plan.config)`. Verified in the installed
inspect_ai 0.3.286: `_eval/task/run.py:767` builds the eval-level config, `run.py:1125` stores it
as `plan.config`, `run.py:1135` applies `model.config.merge(generate_config)` to the model,
`_eval/task/log.py:301` stores `model.config` as `model_generate_config`, and
`GenerateConfig.merge` (`model/_generate_config.py:379-398`) lets the argument's non-None fields
win. `tests/test_report.py:86-91` sets `max_tokens` on the model and `temperature` on the eval,
so it tests the union, not the override. Smallest fix: `GenerateConfig(temperature=0.5)` on the
model, `temperature=0.0` on the eval, assert `"temperature 0.0"`.

**L3. The report names the log file but not its directory.**
`report.py:48` keeps `Path(log.location).name`; `logs/2026-10-30-gemini-3.8-flash/` appears only
in the miss note (line 4). Smallest fix: print the log directory once in `main()` or store the
path relative to the repo root.

**L4. No limitations paragraph, no link to the miss note.**
The report does not mention exact match, the near matches kept in v1, provider-default sampling,
or the letter balance (A 60, B 51, C 51, D 60, author response above, verified from the jsonl)
and longest-option share that section 3 item 5 asked for. The miss note links to the report; the
report does not link back. Smallest fix: a fixed "Limits" paragraph in `render()` with those
sentences and a relative link to any `*-cloze-misses.md` beside the report.

**L5. `main()` is untested.**
`report.py:104-118` (argparse, the `status == "success"` filter, the manifest read, the json dump
with `default=str`) only ran by hand. Smallest fix: a test that writes a mockllm log and a
manifest under `tmp_path`, calls `main()` with patched `sys.argv`, and asserts both output files
exist and carry the manifest sha256.

**L6. One citation in the note cannot be checked.**
`2026-10-30-gemini-3.8-flash-cloze-misses.md:66` cites "pygeostat variogram docs" and doi
10.1007/BF02082763 for "direct variogram" meaning "autovariogram". The DOI resolves to a 1994
Mathematical Geology paper on coregionalization, which is the right literature, but the usage
inside it is UNKNOWN. Smallest fix: quote the sentence from the paper or the docs page, or drop
the DOI and keep the usage claim as the reader's.

### 3. Blind sort against the author's sort

Same three buckets and definitions as the note. Counts: the author has strictness 8, other correct
word 24 (17 clear, 7 debatable), model error 1; the blind sort has strictness 7 (1 debatable),
other correct word 26 (17 clear, 9 debatable), model error 0. Buckets match on 31 of 33 items.
Debatable flags: author 7 (4, 14, 26, 66, 76, 101, 144), blind 10 (26, 47, 59, 66, 76, 83, 101,
111, 142, 157), shared on 4 (26, 66, 76, 101).

Disagreements:

- gold/cloze/142, key "signal", reply "radiance". Author: strictness, synonym ("the signal a
  satellite radiometer receives is radiance"). Blind: other correct word, debatable (same
  referent, but not a string variant of the key; only a per-item alias would catch it). The
  author's reading fits the bucket definition better, since the two words name the same quantity
  in this sentence; it is the weakest of the eight synonym calls because no general rule
  (plural, word order, symbol) recovers it, so it should keep a debatable mark.
- gold/cloze/157, key "spline", reply "sinusoidal". Author: model error ("names a different curve
  for a specific study"). Blind: other correct word, debatable (fitting a sinusoid to a seasonal
  cycle is a standard method; the sentence names no study and nothing in it rules the reply out).
  The blind reading is the supportable one by the note's own treatment of 101, 59 and 144, and by
  the repo rule that an unverified claim is UNKNOWN; the author's label needs a citation of the
  study's method to stand (M1).

Accuracy on the same logs under each reading, author versus blind: exact match 95 of 128 (0.742)
for both; plus the same-meaning replies 103 (0.805) versus 102 (0.797); plus the clear other
correct words 120 (0.938) versus 119 (0.930); plus the debatable ones 127 (0.992) versus 128
(1.000). The note's conclusion holds under both sorts: for this model the cloze score measures
whether it picks the source's word, and at most 1 of the 33 misses is a wrong statement that
either reader will call clear.

| N | key | reply | author | blind | match |
|---|---|---|---|---|---|
| 4 | density | temperature | other, debatable | other | yes |
| 8 | (REML) | variogram | other | other | yes |
| 14 | fluxes | forcing | other, debatable | other | yes |
| 16 | aerosol | baseline | other | other | yes |
| 19 | radiative | direct | other | other | yes |
| 22 | (τa) | (AOD) | strictness | strictness | yes |
| 26 | aerosol | hydrometeor | other, debatable | other, debatable | yes |
| 34 | ice-nucleating | aerosol | other | other | yes |
| 37 | Cloud-aerosol | Aerosol-cloud (en dash in the reply) | strictness | strictness | yes |
| 47 | coagulation | collision-coalescence | strictness | strictness, debatable | yes |
| 49 | aerosol | hygroscopic | other | other | yes |
| 56 | stratus | stratocumulus | other | other | yes |
| 59 | variances | algorithms | other | other, debatable | yes |
| 66 | anthropogenic | biomass burning | other, debatable | other, debatable | yes |
| 72 | autovariograms | direct variograms | strictness | strictness | yes |
| 74 | microphysics | condensation nuclei | other | other | yes |
| 76 | convective | both | other, debatable | other, debatable | yes |
| 83 | troposphere | atmosphere | other | other, debatable | yes |
| 84 | aerosol | SO2 | other | other | yes |
| 85 | growth | size | other | other | yes |
| 101 | concentration | droplet | other, debatable | other, debatable | yes |
| 102 | upwelling | rain | other | other | yes |
| 105 | SO2 | sulfur dioxide | strictness | strictness | yes |
| 107 | concentrations | size | other | other | yes |
| 109 | simulate | fit | other | other | yes |
| 111 | CO2 | greenhouse gas | other | other, debatable | yes |
| 114 | oceans | ocean | strictness | strictness | yes |
| 136 | altitudes | height | strictness | strictness | yes |
| 139 | density | design | other | other | yes |
| 142 | signal | radiance | strictness | other, debatable | no |
| 144 | least-squares | kriging | other, debatable | other | yes |
| 153 | emissions | volatile organic compounds | other | other | yes |
| 157 | spline | sinusoidal | model error | other, debatable | no |

### 4. What is missing before Phase 2 can close

1. M1 and M2 before the decision: relabel 157 and sort the 28 MCQ misses, so that 0005 and the
   alias question (WORKBOARD.md:27-28) rest on both splits.
2. The second model's logs for the Register (WORKBOARD.md:26), run from a clean tree with a fixed
   sampling config (M3), so the report shows a clean commit and a rerun can be compared.
3. A domain expert's pass over the 24 to 26 other-correct-word items, or at minimum the written
   reconciliation of 142 and 157 above adopted into the note.
4. Report fixes L1, L3, L4 and tests L2, L5, test-first.
5. Still open from Phase 1 and the first Phase 2 review: `reports/climaqa/leak_review.csv`,
   `reports/climaqa/review_sample.csv` (WORKBOARD.md:24-25) and LICENSE.

### 5. What I would not publish yet, and why

- "1 clear model error" (note line 31, 43; docs/log.md:21; WORKBOARD.md:16; 0005 line 10). The
  supportable sentence is "0 to 1 clear, up to 9 debatable".
- 0.805 as a rescored cloze accuracy. It depends on eight aliases no expert has approved and on
  142 counting as a synonym.
- The MCQ reward as the clean alternative (0005). Two of six MCQ misses I read have keys I would
  dispute; that is one reader on six items, which is why M2 asks for the full sort rather than
  asserting a rate.
- The baseline numbers as a benchmark result. As the first log of the pipeline they are sound and
  fully reproduced here; as a number to compare against, a dirty commit and provider-default
  sampling are not enough.

### Author response (2026-10-30)

Code fixes landed test-first; each new test was also run against a broken version of the code
(merge order flipped, note glob broken) to see it fail.

| Issue | Fix | Commit |
|---|---|---|
| M1 157 labelled a model error without evidence | relabelled "other, debatable"; the note now says 0 to 8 wrong and 25 other correct words (8 debatable), and records the blind sort | cad05a9, 5c56b90 |
| M2 0005 rested on the cloze sort alone | the 28 MCQ misses sorted: 7 model errors (3 debatable), 12 ambiguous, 6 flawed (keys wrong in 232 and 247), 3 source only; 0005 rewritten on both sorts | f8e9675, 1b656ef |
| M3 report silent on the dirty tree and provider defaults | a Limits section warns when either applies | 8765095 |
| M4 items that test the source document | carried into the 0005 proposal (two audit checks, exclusion in v2); not implemented until Aswani says yes | 1b656ef |
| L1 Runs line showed the eval creation time | start and end per task from `log.stats` | 196989b |
| L2 config precedence untested on a shared key | test with temperature on both levels | 96de4db |
| L3 no log directory | a "Logs:" line | 5cb35b1 |
| L4 no limits and no link to the notes | Limits: 21 kept near matches, exact match, key letters, the key is the strictly longest option in 82 of 222, links to both miss notes | 8f71163, 72c43ac |
| L5 `main()` untested | end-to-end test | 97d7d39 |
| L6 a citation that cannot be checked | DOI dropped; the usage claim is marked as the reader's | cad05a9 |

Open: the second model's run from a clean tree with a fixed sampling config (needs an account or
key), the domain expert's pass over both notes, LICENSE, and the two hand-check sheets.
