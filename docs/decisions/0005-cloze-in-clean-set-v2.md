# 0005: how clean set v2 handles cloze

Date: 2026-10-30. Status: proposed. Nothing is implemented until Aswani says yes; the v1
contract (0004) stays unchanged until then.

Context: the first baseline (Gemini 3.8 Flash on clean set v1) missed 33 of 128 cloze items
under exact match. By one reader's sort
(`reports/climaqa/runs/2026-10-30-gemini-3.8-flash-cloze-misses.md`), 25 to 32 of the 33 are
acceptable answers: 8 give the key in another string, and 17 to 24 are other words that still
make a correct sentence. Only 1 to 8 are wrong. The verifiers taskset uses the same exact match
as its RL reward (`ClimaqaTask.correct` in `environments/climaqa_v1/climaqa_v1/taskset.py`), so a
policy would be rewarded for guessing the source's word more than for knowing the science.

Options:

1. Expert-checked accepted-answer lists. Each cloze record carries an `answers` list, and the
   contract matches any entry exactly. The reward stays exact, cheap and deterministic. But a
   list is never complete: a new model's correct alternative scores 0 until someone reviews it,
   and each review cuts a new set version.
2. A judge model decides whether a reply fills the blank correctly. It catches alternatives no
   list foresaw. But the reward stops being exact, costs one call per reply (price UNKNOWN), can
   drift when the provider updates the judge, and moves trust from the key to the judge.
3. MCQ-only rewards. The RL taskset rewards MCQ only; cloze stays an eval, reported as
   exact-word accuracy with the miss sort beside it. Nothing new to build, but RL loses the 128
   cloze items.

Proposal: option 3 now and option 1 as the way back. In v2 the reward comes from MCQ only. An
expert reviews the cloze misses, the 33 from this run first, and approves `answers` lists;
cloze returns to the reward once its lists are checked. No judge model in the reward, because
the repo's aim is answers "a program can grade exactly" (`README.md`). Rescoring old logs
against new lists needs no paid run.

Consequences: v2 changes the bundled set (a new sha256 in the manifest) and the taskset's
default kinds. The Inspect cloze task keeps reporting exact-word accuracy, and the report gains
an accepted-answer column once lists exist.
