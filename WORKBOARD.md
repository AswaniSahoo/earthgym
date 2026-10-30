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
- [x] Cloze misses sorted (33): 8 scorer strictness, 25 other correct words (8 debatable),
      0 clear model errors; blind second sort matched 31 of 33; contract unchanged;
      reports/climaqa/runs/2026-10-30-gemini-3.8-flash-cloze-misses.md
- [x] MCQ misses sorted (28): 7 model errors (3 debatable), 12 ambiguous, 6 flawed, 3 source
      only; reports/climaqa/runs/2026-10-30-gemini-3.8-flash-mcq-misses.md
- [x] Fable baseline review: no High, M1 to M4, L1 to L6; reviews/phase-2-climaqa-port.md
- [ ] Report fixes from that review, test-first: M3 (dirty tree and provider defaults), L1 to L5
- [x] verifiers v1 taskset climaqa-v1 (350 tasks, shared answer contract)
- [x] Phase 2 review (Fable): every issue fixed test-first; author response in the review

## Waiting on Aswani

- [ ] reports/climaqa/leak_review.csv: 56 Gold and Silver pairs, same item or not
- [ ] reports/climaqa/review_sample.csv: 30 validated Gold MCQ items
- [ ] Decision 0005 (proposed): expert review of the flagged items in both splits,
      accepted-answer lists for cloze, rewards from reviewed items only, no judge model.
      Not implemented until yes

## Done

- [x] 2026-10-30 Phase 1 ClimaQA audit; Fable review fixes landed test-first; CI green
- [x] 2026-10-30 CI runner pinned to ubuntu-24.04

## Later

- Phase 3 ERA5 forecast-score environment
- Two-model inspect_evals Register run: parked 2026-10-30; Gemini 3.8 Flash is the only
  baseline for now, and the second model needs Aswani's yes
- Phase 4 IBTrACS cyclone analytics environment
- Phase 5 heat-insurance basis-risk environment
- Before publishing: LICENSE, write-up, blog posts from reports/
