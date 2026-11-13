# Phase 1 review: ClimaQA audit

Reviewed 2026-10-30 against the repository's working tree (no commits yet, nothing tracked).
Everything below was run or fetched during the review; nothing is taken from memory. Where a
claim could not be checked it is marked unknown.

What was run: `uv run pytest -q` (11 passed), `uv run ruff check .` (clean), `uv run ruff format
--check .` (clean), `uv lock --check` and `uv sync --locked` (clean), the audit twice into a
scratch directory (byte-identical to each other and to `reports/climaqa/`), a fresh `data.fetch`
into an empty directory over the network (all six sha256 match the pin, 7.9 s), and
`pytest --cov` (58 percent line coverage). Spot-checked against the raw CSVs: leak items 61, 112,
139, 158, 163, 191; gold MCQ 227; gold cloze 0, 2, 20, 21, 25; silver duplicate groups 16/102,
30/129, 49/832; gold MCQ 34, 265, 273, 291; gold MCQ 20 and 236; silver cloze 6 and 23.

External facts verified at source: arXiv 2410.16701 v2 (last revised 9 Mar 2025, the current
version) has section "A.3.2 Fine-tuning on ClimaQA-Silver" and says in section 5 "We then
evaluate the impact of this task-specific fine-tuning by assessing the models' performance on the
ClimaQA-Gold dataset"; its Table 2 gives Gold MCQ 126/72/47 and Freeform 54/52/55, Silver MCQ
501/264/235 and Freeform 507/241/252, cloze 160 and 1000, all of which match the inventory. The
pinned revision `3f084a02` is the current HEAD of `Rose-STL-Lab/ClimaQA` (18 commits, newest
2025-03-17), the card license is apache-2.0, and `UCSD-GENIE/ClimaQA` (the name the paper cites)
returns a 307 redirect to it. The authors' `evaluation/mcq_evaluation.ipynb` and
`evaluation/freeform_evaluation.ipynb` in `Rose-STL-Lab/genie-climaqa` filter
`df[df['Validation'] == True]` and load the dataset unpinned with
`load_dataset('UCSD-GENIE/ClimaQA', data_files=...)`. Both CI action SHAs resolve to their stated
tags (v7.0.1, v10.3.3), which are also the latest releases.

## 1. Ratings

| Area | Score | Justification |
|---|---|---|
| Correctness | 7 | Every finding class spot-checked is a true positive, but the "answer differs" detail is textual not semantic (two cases differ only by punctuation), the leak check misses 6 verified cross-task overlaps, and two latent parser edge cases exist. |
| Minimalism and clarity | 9 | 199 statements, zero runtime dependencies, three modules with one job each, names that read as prose. Only `run()` mixes network I/O with logic. |
| Test coverage | 5 | 11 tests, 58 percent lines: `audit.py` is 0 percent, the `fetch` success path never executes, five check branches are untested. |
| Reproducibility | 8 | Revision plus sha256 pin verified live, lockfile, deterministic outputs verified byte-identical, seed recorded. A bad-hash file persists on disk and the sample sheet is overwritten on re-run. |
| CI/CD | 7 | SHA-pinned actions, locked sync, lint, format and tests, least-privilege permissions. No timeout or concurrency, nothing exercises `audit.py`, and the workflow has never run because there is no commit. |
| Research rigor of the findings | 6 | The paper claims are right and now verified at source, but the leak numbers are lower bounds without saying so, "differs" is misread as contradiction, there is no near-duplicate pass, no answer-position table, and no limitations section. |
| Readiness to publish the audit | 4 | Code is close. The audit is not: hand-check sheet empty, no narrative write-up, labels need fixing, no LICENSE, no commit. |

## 2. Issues by severity

### High

**H1. `write_sample` overwrites the human hand-check sheet on every run.**
`src/rlenv/climaqa/audit.py:58` calls `write_sample` unconditionally and `audit.py:114` opens
the file with `"w"`. The sheet is the one artefact a human fills in; one re-run after the
hand-check wipes 30 verdicts. Fix: in `run`, guard with `if not (out / "review_sample.csv").exists():`,
and say in the README that the sheet is generated once.

**H2. The leak check is same-task only and misses verified cross-task leaks.**
`audit.py:38-39` pairs `gold/<task>` with `silver/<task>` only. Exact match under `words()`
finds 2 gold MCQ questions in silver FFQ and 4 gold FFQ questions in silver MCQ (silver MCQ and
silver FFQ share 12 questions between themselves). The paper fine-tunes on all three Silver forms,
so these 6 are leaks of the same kind as the 43 reported. Fix: build `silver_all = sum(rows["silver", t] for t in TASKS)`
once, call `checks.overlap(rows["gold", task], silver_all, f"gold/{task}")`, and include the
silver task in `detail` (add the split to the id string in `overlap`, `checks.py:130`).

### Medium

**M1. "answer differs" compares `norm()` text, so it reports punctuation and paraphrase as disagreement.**
`checks.py:115` and `checks.py:129` compare `answer_text`, which uses `norm` (punctuation kept).
Verified: silver duplicate group 16/102 differs by one trailing full stop; gold/cloze 78 versus
silver 592 is equal under `words()`. The other 30 "differs" cases I read are paraphrases of the
same answer with regenerated distractors (gold 61 "Radiative forcing from aerosol-cloud
interactions (ΔFaci)" versus silver 114 "Radiative forcing from aerosol-cloud interactions"),
with one genuine contradiction in silver (49 "The mass of SO2 emitted, altitude, and eruption
location" versus 832 "The mass of SO2 emitted"). Fix: compare `words(answer_text(row))` at both
sites and rename the detail to `keyed text differs`. The README and the write-up must say the
label means "the keyed option text is not identical", never "the two splits disagree".

**M2. The leak count is a lower bound and nothing says so.**
Exact matching is robust (`words()` adds zero exact matches over `norm()`), but token Jaccard
at or above 0.8 finds 27 further gold-silver near-matches (MCQ 8, cloze 12, FFQ 7; for example
gold cloze 22 versus silver 201 at 0.96, gold MCQ 157 versus silver 657 at 0.90) that nobody has
read. Fix: add one flag check `leak.near_match` in `checks.py` (token-set Jaccard at or above
0.8 against the same silver index, about ten lines) so the pairs land in `findings.json` for the
hand-check, and state in SUMMARY that `leak.gold_in_silver` counts exact matches only.

**M3. `audit.py` has no tests and `run()` cannot be tested offline.**
`run` fetches inside itself (`audit.py:28`), so `render`, `write_sample` and the `rejected`
logic (`audit.py:41-53`) are at 0 percent coverage. `data.fetch` lines 53-54 (the success return)
never execute in tests either, and `checks.py` lines 33, 54, 62, 77, 81, 98, 112 (`kind`, the
unlabelled chunk, `answer_text` for non-MCQ, `empty_option`, `all_or_none`, `cloze.empty_answer`,
the single-row `continue` in `duplicates`) are untested. Fix: split `run(cache, out)` into
`audit(rows) -> report` plus the I/O wrapper; add three tests on the existing inline fixtures
(`audit` returns the expected finding kinds and `rejected` flags, `render` contains the paper
check row with `True`, `write_sample` writes 1 row per level and leaves `verdict` empty); add one
`fetch` success test that writes a file, computes its sha256 in the test and monkeypatches
`data.FILES`.

**M4. A file that fails the hash check is left in place.**
`data.py:45` skips the download when the path exists and `data.py:50-52` raises on mismatch, so
after one bad download every later run fails with the same message and never re-downloads.
Fix: download to `path.with_suffix(".part")`, hash that, rename into place only on a match, and
`unlink` on mismatch. A 404 raises an uncaught `urllib.error.HTTPError` (verified); a one-line
message naming the URL would be enough, retries are not needed.

### Low

**L1. `mcq.answer_in_question` has no token boundary.**
`checks.py:83` tests `key in words(question)` on the joined string, while the cloze check at
`checks.py:99` pads with spaces. No false positive on this data (substring and token tests agree
on all 8 flagged items), but "ice crystal growth" would match inside "device crystal growth".
Fix: `f" {key} " in f" {words(row['Question'])} "`.

**L2. `parse_options` swallows a trailing separator into the last option.**
`checks.py:49` does `raw.strip().split(SEP)`; `strip` removes the final newline of a trailing
separator so it no longer matches `SEP`, and option d becomes `"w\n--------------------"` with no
finding raised (verified). Not present in this data (no option text contains `---`). Fix: split
with `re.split(r"\n-{20}\n?", raw.strip())` and drop empty chunks, and add the case to
`test_parse_options_reads_four_labelled_options`. The other edge cases behave well: `(a)`, `a.`,
digit labels and a 19-dash separator all fail loudly as `mcq.option_labels`.

**L3. The paper check only uses two of the six rows of Table 2.**
`audit.py:21-24` cross-checks Gold MCQ and FFQ. Table 2 also gives Silver MCQ 501/264/235,
Silver FFQ 507/241/252, Gold cloze 160 and Silver cloze 1000, and all four match the inventory.
Fix: add the silver rows to `PAPER` and a `rows` expectation for the cloze splits.

**L4. SUMMARY drops the answer-letter distribution that `findings.json` already holds.**
Gold a 77, b 73, c 80, d 62; silver a 244, b 221, c 279, d 256. Position balance is a standard
MCQ audit line and costs one table in `render` (`audit.py:62`).

**L5. `detail` is truncated to 80 characters.**
`checks.py:84` slices the key; the JSON is the item-level record, so keep the whole key.

**L6. "All of the above" in first position is a broken item, not a judgment call.**
Gold MCQ 236 (Validation=True) has "All of the above" as option a) and as the key; nothing is
above it. Gold 20 (key d) is fine. Either keep the flag and name 236 in the write-up, or raise
the check to a defect when the all/none option is not last.

**L7. `kind` conflates item defects with a split defect.**
`README.md:35` defines a defect as "the item is broken"; `leak.gold_in_silver` is a property of
the split pair, the item itself is a fine question. The label is defensible because the README
explains it, but say "split-level defect" where the leak is counted so no reader concludes the 43
questions are bad questions.

**L8. Packaging and README gaps.**
No LICENSE file and no `license` field in `pyproject.toml`. `README.md:31` lists `docs/reviews/`,
which did not exist before this file. The README does not mention that the paper cites
`UCSD-GENIE/ClimaQA` and that the name now redirects to `Rose-STL-Lab/ClimaQA`, nor that the
dataset is apache-2.0, which is what makes the 30 verbatim items in `review_sample.csv`
redistributable. `data.load` could open with `encoding="utf-8-sig"` for free (no BOM today,
verified; a future revision with one would rename the id column to `﻿`).

**L9. CI hygiene.**
`.github/workflows/ci.yml` has no `timeout-minutes` and no `concurrency` group. A manual
`workflow_dispatch` job that runs `uv run python -m rlenv.climaqa.audit --out /tmp/x` would
prove the pinned URLs and hashes still resolve; keep it off `push` so the default job stays
offline. The workflow has not executed yet (no commits), so "CI green" is currently unknown.

## 3. What is missing to call Phase 1 done

Checks: H2 (cross-task leak), M1 (`words()` for the differs judgment), M2 (near-match flag),
L1, L2, L3. Optional but cheap and standard: mean length of the keyed option versus distractors
per split (longest-option bias).

Report content, in SUMMARY or the write-up: the leak fractions of the validated test set (MCQ
17/245 = 6.9 percent, FFQ 17/161 = 10.6 percent, cloze 9/160 = 5.6 percent; all 34 MCQ and FFQ
leaked items are Validation=True, so they are in the actual test set); that the leak counts are
exact-match lower bounds; what "differs" means; the Validation story (a plain
`load_dataset("Rose-STL-Lab/ClimaQA")` yields 292 MCQ and 181 FFQ rows including 47 and 20
expert-rejected items, the dataset card at the pinned revision does not document the column, and
only the authors' notebooks filter it); the rename; the answer-letter table; the fact that the
paper holds out 13 textbooks for continued pre-training (section 5) but says nothing about
Gold/Silver disjointness (no match for dedup, disjoint, contaminat or leak in the v2 text), which
is exactly the gap the audit found. Also worth one sentence: the paper's prose says "we curated
245 freeform, 161 MCQ, and 160 cloze questions" (section 3.1) while Table 2 and the files say
245 MCQ and 161 freeform.

A precision note that belongs in the write-up because it is evidence the checks work: of the 4
gold `mcq.answer_in_question` flags, 3 (265, 273, 291) are items the experts rejected, and the
one validated item (34, "Which study focuses on modeling the global emission, transport, and
deposition of trace elements..." with that very sentence as option a) is degenerate.

The human hand-check: the 30 MCQ verdicts are empty. Three of the 30 sampled items (158, 163,
240) are leaked items, so the sheet should carry a column listing existing findings per item.
Random sampling is the wrong first use of expert time: the targeted sets are the 15 "differs"
pairs (read both rows, decide same-answer or contradiction), the 27 near-match pairs, the 17
silver `dup.answer_differs` groups, items 227 and 236, and the 24 gold cloze giveaways. FFQ needs
its own sample; free-text keys are the hardest to verify and have none.

Write-up: a narrative in `reports/climaqa/` or `docs/reviews/` with method, numbers, limitations, and
a dated "verified at" line per external claim (paper v2 of 9 Mar 2025, dataset revision
`3f084a02` of 2025-03-17, notebooks at the genie-climaqa push of 2025-03-14).

Packaging: LICENSE plus `license` in `pyproject.toml`, README fixes from L8, the first commit,
and one real CI run.

What Phase 2 needs from this code:

- A loader, not an audit: `load_split(config, task, revision)` that returns validated Gold only,
  with the `Validation=False` filter in the loader (`audit.py:41-44` is the wrong home for it).
- A machine-readable exclusion list written by the audit, for example
  `reports/climaqa/exclude.json` mapping split to ids with the reason (leak, cross-task leak,
  duplicate options, degenerate), so the Inspect task and the verifiers environment import one
  file instead of re-deriving policy from `findings.json`. Today's ids are CSV row positions at
  this revision, so every sample must carry the revision hash in its metadata.
- `parse_options`, `norm` and `words` reused by the MCQ scorer, which is why L2 matters there.
- `data.fetch` taking the file table as a parameter so the port can pin the same revision
  without importing the audit module.
- A decision, recorded, on whether the environment ships the leaked items at all or exposes
  them as a separate `contaminated` tag; the paper's own ft-silver rows in Table 3 are the
  affected results.

## 4. What I would not publish yet, and why

- Any sentence that gold and silver "disagree on the answer" for the 15 "differs" items. The raw
  rows show paraphrase and regenerated distractors, not contradiction, and one of the 15 is
  punctuation only. Publish after a human reads all 15.
- The 17 `dup.answer_differs` silver groups as "contradictory keys". One is punctuation only,
  one I read is a real contradiction (49 versus 832), the rest are unread.
- The leak totals as totals. Publish as "at least 17, 17 and 9 by exact match, plus 6 cross-task
  exact matches, plus up to 27 near-matches pending review", or fix H2 and M2 first and publish
  the new numbers.
- "Defect" wording that implies the 43 leaked questions are bad questions. The leak only matters
  to anyone who fine-tunes on Silver and evaluates on Gold, which is what the paper did and
  recommends; the Gold set remains a fine zero-shot test.
- Any hand-check number. None exists.
- A generalisation from items 20 and 236 about "all of the above" items. 236 is broken by
  position; 20 is not.
- The 16 cloze items where only a plural or singular variant of the answer appears outside the
  mask (for example gold cloze 51 "aerosols"); the matcher is exact-token, so they are not flagged.
  Mention the limitation, do not count them until the matcher is changed and the items read.

## Author response (2026-10-30)

Each fix landed test-first (failing test, then code).

| Issue | Fix | Test |
|---|---|---|
| Re-run overwrote the hand-check sheet | `write_once` never overwrites an existing sheet | `test_write_once_keeps_an_existing_hand_check_sheet` |
| Leak check was same-task only | new defect `leak.gold_in_other_silver_task` (6 items: 2 MCQ, 4 freeform) | `test_overlap_against_another_task_skips_the_answer_comparison`, `test_audit_reports_same_task_and_other_task_leaks_without_io` |
| "answer differs" counted a trailing full stop | `answer_text` drops edge punctuation, keeps operators; detail now reads "answer text same/differs" | `test_answer_text_keeps_operators_but_drops_trailing_punctuation` |
| Exact matches only | `leak.near_match` flag (word-set Jaccard 0.8 or more, 34 items); SUMMARY states exact counts are a lower bound | `test_near_overlap_flags_reworded_questions_only` |
| audit.py untestable offline | pure `audit(rows)` split from I/O in `run` | `test_audit_reports_same_task_and_other_task_leaks_without_io`, `test_render_shows_paper_rows_and_findings` |
| Bad-hash file stayed on disk | `fetch` deletes it before raising; download verified before writing | `test_fetch_deletes_a_file_that_fails_its_pinned_hash`, `test_fetch_downloads_a_missing_file_and_keeps_it` |
| Token boundary in answer_in_question | padded token containment | `test_answer_in_question_respects_word_boundaries` |
| Trailing separator in Options | separator regex, empty chunks dropped | `test_parse_options_ignores_a_trailing_separator` |
| Paper check used 2 of 6 rows | all 6 rows of the statistics table, all match | `test_render_shows_paper_rows_and_findings` |
| Hand-check order | `leak_review.csv` (56 pairs) to be judged before the random MCQ sample | n/a |

Open: LICENSE (owner's choice), the human hand-checks, the write-up.
