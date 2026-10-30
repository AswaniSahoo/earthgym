# Workboard

Updated 2026-10-30. Publish after completion. Small commits, one-line messages.

## Now: Phase 2, clean ClimaQA port and multi-model baseline

- [x] Radar check for Phase 2 (scout): 20 entries in docs/radar.md
- [x] Clean set v1: 350 kept (222 MCQ, 128 cloze), 102 excluded with reasons, one fixed
      option order, sha256 in reports/climaqa/clean_v1_manifest.json
- [x] Scoring: one contract (climaqa_v1/contract.py) for both harnesses; 12 cloze keys cleaned
- [x] Inspect tasks for MCQ (222) and cloze (128) with the contract scorer, tested on mockllm
- [x] Baseline: Gemini 3.8 Flash on Vertex over clean set v1: MCQ 0.874 (194 of 222, stderr
      0.022), cloze 0.742 (95 of 128, stderr 0.039), 0 format failures, provider default
      settings; reports/climaqa/runs/2026-10-30-gemini-3.8-flash.md
- [x] Cloze misses sorted (33): 8 scorer strictness, 24 other correct words (7 debatable),
      1 model error; contract unchanged;
      reports/climaqa/runs/2026-10-30-gemini-3.8-flash-cloze-misses.md
- [ ] Fable review of the baseline and a blind second sort of the 33 cloze misses (running)
- [x] verifiers v1 taskset climaqa-v1 (350 tasks, shared answer contract)
- [x] Phase 2 review (Fable): every issue fixed test-first; author response in the review

## Waiting on Aswani

- [ ] reports/climaqa/leak_review.csv: 56 Gold and Silver pairs, same item or not
- [ ] reports/climaqa/review_sample.csv: 30 validated Gold MCQ items
- [ ] Second model for the inspect_evals Register (needs an account or key)
- [ ] Cloze aliases: keep exact match, or approve aliases for the 8 same-meaning keys, cut clean
      set v2 and rescore the same logs (0.742 becomes 0.805; no new paid run)

## Done

- [x] 2026-10-30 Phase 1 ClimaQA audit; Fable review fixes landed test-first; CI green
- [x] 2026-10-30 CI runner pinned to ubuntu-24.04

## Later

- Phase 3 ERA5 forecast-score environment
- Phase 4 IBTrACS cyclone analytics environment
- Phase 5 heat-insurance basis-risk environment
- Before publishing: LICENSE, write-up, blog posts from reports/
