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
- Phase 2 started. Radar refreshed to 20 entries: verifiers 0.4.0 replaced its API with
  `verifiers.v1` tasksets; Inspect 0.3.286 never shuffles MCQ choices by itself; Gemini 2.5
  Flash on Vertex retired 2026-10-20; torchtpu is real but needs TPU v5e or newer.
- Finding: every published ClimaQA score we checked uses the unfiltered file, which still holds
  the 47 expert-rejected MCQ items; 12 Gold cloze keys end in "," or "." and break exact match.
- Clean set v0: 377 items (226 MCQ, 151 cloze), 75 excluded with reasons; MCQ keys uppercase,
  cloze keys cleaned. Inspect tasks use built-in choice() and exact(); 26 tests, CI green.
- Next: baselines (model access decision), verifiers taskset, Phase 2 review.
