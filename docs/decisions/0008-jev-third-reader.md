# 0008: Jev as a third reader of the ClimaQA miss sort

Date: 2026-10-31. Status: accepted, 2026-10-31: I chose this study.

Context: two sorts of the 2026-10-30 Gemini 3.8 Flash misses exist: the first, made with Claude Code
(the two miss notes), and the Phase 2 reviewer's blind sort of the 33 cloze misses
(`docs/reviews/phase-2-climaqa-port.md`, Baseline review, section 3). The expert review sheet
`reports/climaqa/expert_review_v2.csv` holds 83 rows: 61 misses, 2 flagged items and 20 sampled
correct answers. TypeSafe's Jev answers typed questions about a `state` with probabilities (`POST
https://api.typesafe.ai/v1/systemone`; OpenAPI spec `info.version` 0.2.0, sha256
`3ca93b6e6b9aa8d7820531b78c66ed7a9798b11e6e163ad96b140fb3d75fbcf4`, read 2026-10-31).

Decision:

- Jev sorts each of the 83 rows, as a third reader, with one `choice` question whose options
  restate the miss notes' buckets as properties of the item, so they also fit correct answers.
  I measure Cohen's kappa against both sorts, the Brier score of its probabilities where the
  two sorts agree, stability over 5 identical calls per item, cost and latency.
- The same run measures first-position bias, which TypeSafe lists among Jev's weaknesses:
  one extra call per other cyclic rotation of the option order, so each option is listed
  first once per item (626 calls in all). The report gives how often the first-listed option
  wins against the rate if order did not matter, the probability an option gains from being
  listed first, and kappa from rotation-averaged probabilities next to the fixed-order kappa.
- Jev never enters a reward: under 0005 rewards come only from expert-reviewed items. Its
  outputs never train a model: TypeSafe's MCA 2.3(b) bars using Output to "train a model to
  imitate the output of the Services".
- One item per request, because unrelated items in the state shift its scores (TypeSafe's own
  list of weaknesses names "large irrelevant state"). The model is pinned to `jev-1.14.0`, not
  an alias. The client is plain `urllib`, so no new dependency. Raw responses stay under
  `logs/`, which is not in git.
- The key comes from `TYPESAFE_API_KEY` or `.env` at the repo root (gitignored since 6473926); it
  is never printed, logged or committed.
- Spend: real calls up to $0.10 in total, my cap, at $0.042 per million input tokens with
  output free (docs.typesafe.ai/models, read 2026-10-31). The runner stops before the cap.
  Anything above needs my approval.
- What leaves the machine: the items (ClimaQA, Apache-2.0) and Gemini 3.8 Flash's answers to
  them, with no notes or labels. TypeSafe's MCA 4.1 and 4.3 let it keep "Telemetry", including
  "classifications", and process it "without restriction". Whether Google's terms allow
  passing Gemini's answers to another service was not checked: UNKNOWN.
- Reports name Jev as the reader of its sort (TypeSafe AUP 1.4 bars misleading anyone about
  whether output came from AI).

Consequences: CI stays offline, since every HTTP call in the tests is mocked. The study runs
only after the key is added.
