# 0005: how clean set v2 handles cloze, and which items reward a policy

Date: 2026-10-30. Status: accepted (Aswani, 2026-10-30). No expert reviewer is named yet: after
Phase 3 stage 2 the build session prepares a review sheet of the flagged items for that
expert, and only the expert writes accepted answers. The v1 contract (0004) and clean set v1
stay as they are until the review is done.

Context: the first baseline (Gemini 3.8 Flash on clean set v1) has two miss notes, each one
reader's sort:

- Cloze (`reports/climaqa/runs/2026-10-30-gemini-3.8-flash-cloze-misses.md`): 33 misses under
  exact match. 25 to 33 are acceptable answers: 8 give the key in another string, and 17 to 25
  are other words that still make a correct sentence. None is clearly wrong. A blind second
  sort matched 31 of 33.
- MCQ (`reports/climaqa/runs/2026-10-30-gemini-3.8-flash-mcq-misses.md`): 28 misses. 7 are model
  errors (3 debatable). The other 21 are item problems: 6 flawed items (2 with a wrong key, 2
  with no fully right option), 3 that test the source document, and 12 with two defensible
  options.

Both splits feed the RL reward (`ClimaqaTask.correct` in
`environments/climaqa_v1/climaqa_v1/taskset.py`), so a policy would be rewarded for guessing the
source's word, and in 2 MCQ items for picking a wrong key. The baseline review
(`reviews/phase-2-climaqa-port.md`, Baseline review, M4) also lists kept items that test the
source document (gold/mcq/56, 132, 215; gold/cloze/59, 144) and the two cloze keys that are a
parenthesised abbreviation (gold/cloze/8, 22). gold/mcq/167 and 207 ask the same question.

Options for cloze:

1. Expert-checked accepted-answer lists. Each cloze record carries an `answers` list, and the
   contract matches any entry exactly. The reward stays exact, cheap and deterministic. But a
   list is never complete: a new model's correct alternative scores 0 until someone reviews it.
2. A judge model decides whether a reply fills the blank correctly. It catches alternatives no
   list foresaw. But the reward stops being exact, costs one call per reply (price UNKNOWN), can
   drift when the provider updates the judge, and moves trust from the key to the judge.
3. MCQ-only rewards. Simple, but the MCQ note shows MCQ is not clean either.

Proposal:

1. Item review before v2. An expert confirms or rejects every item the two notes and the review
   flag, plus a sample of hits, since only misses were read.
2. v2 drops confirmed flawed, source-only and duplicate items, fixes or drops ambiguous MCQ
   items, and gives each remaining cloze item an accepted-answer list (option 1).
3. Two audit checks catch the new defect kinds next time (review M4): questions about the source
   document, and cloze keys that are a parenthesised abbreviation. A near-duplicate check within
   Gold catches pairs like 167 and 207.
4. The reward uses only reviewed items, in both splits. No judge model in the reward, because
   the repo's aim is answers "a program can grade exactly" (`README.md`).
5. If an RL run is needed before the review, it rewards MCQ minus the 9 flawed or source-only
   misses, and cloze stays an eval.

Consequences: v2 changes the bundled set (a new sha256 in the manifest) and the taskset's
default items. The Inspect tasks keep reporting exact-match accuracy, and the reports gain an
accepted-answer column once lists exist. Rescoring the 2026-10-30 logs against v2 needs no paid
run.
