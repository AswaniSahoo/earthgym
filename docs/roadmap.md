# Roadmap

What I plan next, in order. What is done is in the log (`docs/log.md`), and why I chose it is in
the decisions (`docs/decisions/`).

## Before the repository goes public

- I read and confirm every decision record, 0001 onward, from the plain-language digest in
  `docs/human-checks/decisions.md`. `docs/how-built.md` states the review as in progress, and its
  wording changes to match what I agree with, change or question.
- The last 21 samples of Qwen3.5-2B's ERA5 run, cut by a session's deadline (decision 0025): one
  short resumed session on Kaggle, after the weekly allowance renews on 2026-11-07.
- My own hand checks: the 30-item ClimaQA sample and the 56 Gold and Silver leak pairs, from
  sheets under `docs/human-checks/`.
- A README that leads with the claim, the results and the three findings.
- Independent oracles for the keys (the Codex review's finding 8): today the heat and storm
  item tests rebuild the items with the same code that made them, which proves consistency, not
  correctness. Recompute every bundled heat and storm key from the prompt data with separate
  code, and add archived references for ERA5 temperature and the 24 and 48 h leads.

## After that

- The drafts for distribution under `docs/release/`, written on 2026-11-02, stay there until I
  decide to go public: the issue for the ClimaQA maintainers, the eval logs as a release asset,
  notes for an inspect_evals Register entry for ClimaQA, notes for the Prime Intellect Hub, and
  a Hugging Face dataset card.

## Open questions

- Who reviews the cloze items as a domain expert (decision 0005). The sheet is ready:
  `reports/climaqa/expert_review_v2.csv`.
- The Jev third-reader study (decision 0008) is built and tested with its HTTP call mocked, but
  it runs only with a TypeSafe key, which I do not have.
- The GHCN-Daily station files stay unpublished unless NCEI states that they may be
  redistributed (decision 0018). The bundled heat items carry those stations' values too, so
  making the repository public publishes derived GHCN-Daily data: I decide that before the flip
  (`docs/release/dataset-card.md`).
