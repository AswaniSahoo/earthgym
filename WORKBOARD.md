# Workboard

Updated 2026-10-30. Publish after completion. Small commits, one-line messages.

## Now: Phase 2, clean ClimaQA port and multi-model baseline

- [x] Radar check for Phase 2 (scout): 20 entries in docs/radar.md
- [x] Clean set v1: 350 kept (222 MCQ, 128 cloze), 102 excluded with reasons, one fixed
      option order, sha256 in reports/climaqa/clean_v1_manifest.json
- [x] Scoring: one contract (climaqa_v1/contract.py) for both harnesses; 12 cloze keys cleaned
- [x] Inspect tasks for MCQ (222) and cloze (128) with the contract scorer, tested on mockllm
- [ ] Baseline: Gemini 3.8 Flash on Vertex over clean set v1 (running); report in reports/climaqa/runs/
- [x] verifiers v1 taskset climaqa-v1 (350 tasks, shared answer contract)
- [x] Phase 2 review (Fable): every issue fixed test-first; author response in the review

## Waiting on Aswani

- [ ] reports/climaqa/leak_review.csv: 56 Gold and Silver pairs, same item or not
- [ ] reports/climaqa/review_sample.csv: 30 validated Gold MCQ items

## Done

- [x] 2026-10-30 Phase 1 ClimaQA audit; Fable review fixes landed test-first; CI green
- [x] 2026-10-30 CI runner pinned to ubuntu-24.04

## Later

- Phase 3 ERA5 forecast-score environment
- Phase 4 IBTrACS cyclone analytics environment
- Phase 5 heat-insurance basis-risk environment
- Before publishing: LICENSE, write-up, blog posts from reports/
