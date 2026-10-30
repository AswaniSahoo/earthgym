# Log

Newest first. One entry per working session: what changed, what we learned, what is next.

## 2026-10-30

- Phase 1 ClimaQA audit built stdlib-only on a pinned dataset revision (3f084a0, sha256 per
  file). The paper's statistics table matches the released files on all 6 rows.
- Finding: 43 validated Gold test questions appear verbatim in Silver (17 MCQ, 9 cloze,
  17 freeform), plus 6 across tasks. The paper fine-tunes Llama-3.1-8B and Mistral-7B on
  Silver (arXiv 2410.16701v2, A.3.2), so these are train/test leaks for its ft-silver results.
  34 reworded near copies wait for a human verdict.
- Lesson: the "292 vs 245" gap first looked like a defect; the Validation column and the
  authors' notebooks showed it is the expert-rejected items. Check the source before claiming.
- Lesson: stripping punctuation made `(scl - senv)` equal `(senv - scl)`; a test now guards it.
- Fable review (correctness 7, tests 5, publish-readiness 4); every fix landed test-first,
  20 tests, CI green. Runner pinned to ubuntu-24.04.
- Next: Phase 2 radar check, clean set v0, scorers, Inspect tasks, baselines.
