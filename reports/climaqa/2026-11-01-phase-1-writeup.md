# Checking a climate science benchmark before trusting it

Phase 1 of rlenv, written up on 2026-11-01. Every number below comes from a file in this repo;
the source is named next to it.

## The question

ClimaQA (Rose-STL-Lab/ClimaQA) is a question-answering benchmark for climate science. A
benchmark is an exam paper: before anyone is graded on it, someone should check the answer
key, the wording, and that no exam question leaked into the study material. We ran that check
on the released files at a pinned revision, 3f084a02 (`reports/climaqa/SUMMARY.md`).

## What we checked

The paper's statistics table first: its counts per split and complexity level match the
released files on all six rows we could compare (`reports/climaqa/SUMMARY.md`, Paper check).
Then pure integrity checks over every item: option labels, keys that are not options, empty or
duplicate options, cloze items without a mask, and exact-match overlap between the Gold test
set and Silver, the set the paper fine-tunes on (arXiv 2410.16701v2, A.3.2).

## What we found

- 43 validated Gold test questions appear verbatim in Silver: 17 multiple choice, 9 cloze and
  17 freeform, plus 6 more across tasks (4 freeform and 2 multiple choice). Since the paper
  fine-tunes on Silver, these are train/test leaks for its fine-tuned results
  (`reports/climaqa/SUMMARY.md`, Findings: leak.gold_in_silver and
  leak.gold_in_other_silver_task).
- 34 more Gold items are near copies of Silver items (12 cloze, 8 freeform, 14 multiple
  choice); a human has to judge those (same table, leak.near_match).
- The Gold multiple-choice file still holds the 47 items the experts rejected
  (Validation=False), and the freeform file 20 (same report, Inventory). The authors' own
  notebooks keep only the validated items, which matches the paper's counts; any other loader
  has to filter the same way. The later ClimaQA scores we checked,
  OpenCompass's and SciEvalKit's, use the unfiltered file
  (`docs/radar.md`, the ClimaQA scores row).
- 24 Gold cloze items repeat their answer outside the blank (same table,
  cloze.answer_in_question).

## A lesson in checking the source

A gap between 292 multiple-choice rows and the paper's 245 first looked like a defect. The
Validation column and the authors' notebooks showed it is the 47 expert-rejected items. A
claim about someone else's data is checked at the source before it is made (docs/log.md,
2026-10-30).

## Limits

- Leak counts are exact matches after case and whitespace folding, so they are a lower bound;
  the near copies wait for a human verdict (`reports/climaqa/leak_review.csv`).
- The hand-check of 30 validated items is still open (`reports/climaqa/review_sample.csv`).

## Reproduce

    uv run python -m rlenv.climaqa.audit   # downloads the pinned CSVs, writes reports/climaqa/
    uv run pytest
