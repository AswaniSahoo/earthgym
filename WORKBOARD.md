# Workboard

Updated 2026-10-30. Publish after completion. Small commits, one-line messages.

## Now: Phase 2, clean ClimaQA port and multi-model baseline

- [ ] Radar check for Phase 2 (scout): Inspect, verifiers, MCQ and cloze scoring practice,
      cheapest model access, recent climate benchmarks
- [x] Clean set v0: 377 kept (226 MCQ, 151 cloze), 75 excluded with reasons in
      reports/climaqa/clean_v0_manifest.json
- [ ] Deterministic scorers: MCQ letter extraction, cloze exact match
- [ ] Inspect tasks for MCQ and cloze
- [ ] Baseline runs on several models, dated report in reports/
- [ ] verifiers environment for MCQ and cloze
- [ ] Phase 2 review (Fable), fixes test-first

## Waiting on Aswani

- [ ] reports/climaqa/leak_review.csv: 56 Gold and Silver pairs, same item or not
- [ ] reports/climaqa/review_sample.csv: 30 validated Gold MCQ items
- [ ] Model access for baselines: local small models on the RTX 3050 (4 GB), Gemini on
      Vertex AI from the GCP credit, or a free-tier API key

## Done

- [x] 2026-10-30 Phase 1 ClimaQA audit; Fable review fixes landed test-first; CI green
- [x] 2026-10-30 CI runner pinned to ubuntu-24.04

## Later

- Phase 3 ERA5 forecast-score environment
- Phase 4 IBTrACS cyclone analytics environment
- Phase 5 heat-insurance basis-risk environment
- Before publishing: LICENSE, write-up, blog posts from reports/
