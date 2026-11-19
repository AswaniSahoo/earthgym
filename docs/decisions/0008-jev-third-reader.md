# 0008: Jev as a third reader of the ClimaQA miss sort

Date: 2026-10-31. Status: accepted, 2026-10-31: I chose this study. Amended 2026-11-19 (the
provider, below); run 2026-11-18 (UTC), reported in
`reports/climaqa/runs/2026-10-31-jev-third-reader.md`.

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
only after the key is added. (It ran on 2026-11-18, UTC: see the amendment.)

## Amendment, 2026-11-19

- Decision, revised the same day. Unless `JEV_BASE_URL` names a provider, TypeSafe direct, with the
  pinned `jev-1.14.0`, is used whenever a TypeSafe key is set, and otherwise the Experiential Labs
  gateway. These are the two providers climate-risk-agent vets (at `d5d7c84`: `rag/jev_client.py`,
  lines 95 to 117; `DEPLOY.md`, lines 162 to 168), though that project chooses by `JEV_BASE_URL`
  alone and uses TypeSafe direct when it is unset (`DEPLOY.md`, lines 203 to 206). I first ruled the
  gateway out after reading its new privacy policy (see "Where the data goes" below), then chose it
  as the fallback knowing what that policy says. No TypeSafe key was set, so this run went through
  the gateway: 626 calls from 2026-11-18T20:38:49Z to 21:56:57Z, 0 retries, 332,326 input tokens,
  $0.0140 at TypeSafe's list price, every reply naming model `jev-latest` and provider `typesafe`
  (`reports/climaqa/results/2026-10-31-jev-third-reader.jsonl`, header fields `started` and
  `completed`; report `reports/climaqa/runs/2026-10-31-jev-third-reader.md`).
- Provider and key. `JEV_BASE_URL` picks one of the two vetted providers: `https://api.typesafe.ai`
  (TypeSafe direct, `jev-1.14.0`) or `https://api.experientiallabs.ai` (the gateway, which relays
  the same `POST /v1/systemone` to TypeSafe, with `jev-latest`). Any other value is refused before a
  key is looked up or a call is made. Unset, the choice is TypeSafe direct when `TYPESAFE_API_KEY`
  is set, else the gateway. Each key belongs to one provider: TypeSafe direct reads only
  `TYPESAFE_API_KEY` and the gateway only `JEV_API_KEY`. `TYPESAFE_API_KEY`, `JEV_BASE_URL` and
  `JEV_MIN_INTERVAL_S` come from the environment, else from `.env`. The gateway's `JEV_API_KEY`
  comes only from where `JEV_BASE_URL` came from: the environment when `JEV_BASE_URL` is exported,
  and `.env` when it is in `.env` or unset; an exported `JEV_API_KEY` is refused unless
  `JEV_BASE_URL` is exported too. The reason is that climate-risk-agent uses `JEV_API_KEY` for
  whichever provider it chooses, TypeSafe direct by default (at `d5d7c84`, `DEPLOY.md`, lines 183 to
  185 and 203 to 204), so a shell set up for it holds a TypeSafe key in that variable. Before the
  first call the runner prints the provider, its model, and which variable and source the key came
  from, never the key. Values are stripped, and a blank value counts as unset. A key that still
  holds whitespace or an unprintable character is refused, and no error shows a key. Redirects are
  refused for both providers, so a key goes only to the vetted host it was chosen for.
- The model cannot be pinned through the gateway. Its model list grants only the `jev-latest` alias,
  and `jev-1.14.0` is refused with HTTP 403 `model_not_granted` (climate-risk-agent at `d5d7c84`,
  `rag/jev_client.py`, lines 105 to 109, read 2026-11-11). Its public model list, read 2026-11-19,
  has one Jev entry (https://platform.experientiallabs.ai/models). TypeSafe's alias table gives
  `jev-latest` as pointing to `jev-1.14.0` and says "Each response's `model` field gives the
  versioned ID that answered" (https://docs.typesafe.ai/models, read 2026-11-19), but all 626
  replies of this run name `jev-latest`, as the 2026-11-11 run's did (climate-risk-agent at
  `d5d7c84`, `evals/results/jev-triage-test-2026-11-11.md`, line 8). Which Jev version answered is
  UNKNOWN.
- Pacing, retries and failures. Calls through the gateway start at least 7.5 s apart, timed on a
  monotonic clock; `JEV_MIN_INTERVAL_S`, a finite number of 0 or more, overrides it, and TypeSafe
  direct is not paced unless it is set. The gateway's pricing page gives its free limits as "10 RPM,
  250K TPM and 1M tokens/day, shared across GPT-6 Luna, DeepSeek V4.1 Flash and Clef, plus Jev for
  existing accounts" and says "Requests above a cap get a 429 response"
  (https://www.experientiallabs.ai/pricing, read 2026-11-19). The gateway's Jev page says "Use a
  bounded timeout, surface HTTP and transport errors, and do not add automatic retries or
  Idempotency-Key: an unknown outcome may already be charged"
  (https://platform.experientiallabs.ai/models/jev-latest, read 2026-11-19). So through the gateway
  no call is retried automatically: every HTTP or transport error surfaces at once, and a relaunch
  sends that call again. TypeSafe direct retries 429 and 5xx, at most 4 tries after waits of 10, 20
  and 40 s. Any other refusal stops the run, and every try is charged. A reply that names no model,
  whose choice or probabilities do not match the options sent, or whose token counts are not whole
  numbers of 0 or more, counts as a failed call; a missing output count is read as 0, as in
  climate-risk-agent. A call that fails is logged with its error, HTTP status, retries, request id
  and an estimate of one token per 1.4 characters of the request (and, for an unusable reply, the
  raw body cut to 2,000 characters), charged at that estimate, then raised; a relaunch sends it
  again. An answered call is never sent twice. A call starts only if its provider's maximum tries (1
  through the gateway, 4 direct) at its own estimate fit under what is left of the cap. Over all 626
  calls of this run the request held 1.634 to 2.418 characters per reported input token (median
  1.873), so the estimate was above every reported count, and a test checks that for each call; a
  request much denser than these could still be underestimated, and so carry spend past the cap by
  part of one call. A run stopped with Ctrl-C during a call writes no record, so that try is not
  charged. The lock file `logs/2026-10-31-jev/responses.jsonl.lock` stops two runs at once. A
  relaunch picks up where a run stopped and refuses a log made through the other provider.
- The cap is unchanged: $0.10, charged at TypeSafe's list price of $0.042 per million input tokens,
  whatever the provider reports. One item per request is unchanged.
- Outputs. This repository still never trains a model on Jev's outputs. Through the gateway, though,
  this run's replies entered a program that uses content "to develop, train, fine-tune, and evaluate
  AI models" (the privacy policy below, section 13). Whether that still fits TypeSafe's MCA 2.3(b),
  the reason for that rule: UNKNOWN.
- Where the data goes through the gateway. Its privacy policy changed after the 2026-11-11 read: the
  version read on 2026-11-19 says "Effective November 17, 2026", and the sentence quoted on
  2026-11-11, "The standard hosted service records prompts, responses and related activity."
  (climate-risk-agent at `d5d7c84`, `evals/results/jev-triage-test-2026-11-11.md`, line 7), is no
  longer in it (https://www.experientiallabs.ai/privacy). It says: "If you are on a free
  Subscription Plan, storage of request and response content is enabled by default." Its Data
  Licensing Program "includes: (a) all Customer Content submitted through free Subscription Plan
  accounts", where "participation is a condition of the free plan and cannot be disabled at the
  account level", and for paid plans "only content submitted after the customer affirmatively opts
  in". De-identified Program Content ("prompts, outputs, files, tool data, and traces") is used "to
  develop, train, fine-tune, and evaluate AI models" and sold or licensed "to third-party
  businesses, including AI developers and approved data resellers". "Usage metadata is recorded
  regardless of content-storage settings." On my account, "Prompt and response storage" is on and
  cannot be switched off, and "No-training routing" is off and cannot be switched on (my own
  account's settings, https://platform.experientiallabs.ai/settings/data-controls, read 2026-11-19).
  So this run's items, Gemini 3.8 Flash's answers and Jev's replies enter that program. The items
  are public: ClimaQA is Apache-2.0, and this repository's first finding is that 43 of its Gold test
  questions already appear word for word in the set the paper fine-tunes on (`README.md`, line 20;
  `reports/climaqa/SUMMARY.md`). The program "applies only to Program Content submitted on or after
  the effective date of this version of these Terms", which is November 17, 2026
  (https://www.experientiallabs.ai/terms, section 7.4, read 2026-11-19), so under these terms
  climate-risk-agent's 2026-11-11 gateway runs are outside it; whether a grant under an earlier
  version of the terms covers them: UNKNOWN. Whether Google's terms allow sending Gemini's answers
  to TypeSafe, or to the gateway and its program: UNKNOWN, as when 0008 was accepted.
- TypeSafe direct, the first choice: its privacy policy says it "will not train or fine tune any
  artificial intelligence or machine learning models on Input"
  (https://typesafe.ai/legal/privacy-policy, last updated 2025-11-19, read 2026-11-19), and its
  models page lists `jev-1.14.0` at $0.042 per million input tokens, with output free
  (https://docs.typesafe.ai/models, read 2026-11-19).
