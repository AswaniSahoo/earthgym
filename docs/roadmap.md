# Roadmap

What I plan next, in order. What is done is in the log (`docs/log.md`), and why I chose it is in
the decisions (`docs/decisions/`).

## Before the repository goes public

- A gold check for every environment: each item's reference answer must score 1.0, and items
  that fail it leave the set (the market review found 3 ERA5 items that no forecast can win).
- Say plainly that IBTrACS and heat, with their rules shown, are saturated for a frontier model
  (0.997 and 0.987). I keep them as the controls for the rules-hidden and terms-only ablations
  and for small-model curricula.
- Evidence from small open models, at no API cost: two instruct models from different
  families, 8 samples per item, on all four environments. For each: the mean reward, the share
  of items whose reward varies across the 8 samples, and pass@1 against pass@8.
- My own hand checks: the 30-item ClimaQA sample and the 56 Gold and Silver leak pairs, from
  sheets under `docs/human-checks/`.
- A README that leads with the claim, the results and the three findings.
- Independent oracles for the keys (the Codex review's finding 8): today the heat and storm
  item tests rebuild the items with the same code that made them, which proves consistency, not
  correctness. Recompute every bundled heat and storm key from the prompt data with separate
  code, and add archived references for ERA5 temperature and the 24 and 48 h leads.

## After that

- A tool-using environment, starting from IBTrACS with the rules hidden: the model queries the
  track table and computes statistics in a sandbox instead of reading the whole table in the
  prompt.
- A small GRPO run with a small open model on one environment, with the reward on the train
  split and on the held-out split, reported whether or not it moves.
- Drafts for distribution, kept under `docs/release/` until I decide to go public: the issue
  for the ClimaQA maintainers, the eval logs as a release asset, notes for an inspect_evals
  Register entry for ClimaQA (MCQ and cloze, with the logs of two models), notes for the Prime
  Intellect Hub, and a Hugging Face dataset card.

## Open questions

- Who reviews the cloze items as a domain expert (decision 0005). The sheet is ready:
  `reports/climaqa/expert_review_v2.csv`.
- The Jev third-reader study (decision 0008) is built and tested with its HTTP call mocked, but
  it runs only with a TypeSafe key, which I do not have.
- The GHCN-Daily station files stay unpublished unless NCEI states that they may be
  redistributed (decision 0018).
