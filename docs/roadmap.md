# Roadmap

What I plan next, in order. What is done is in the log (`docs/log.md`), and why I chose it is in
the decisions (`docs/decisions/`).

## Still open, with the repository public

The repository went public on 2026-11-13 (decision 0027). What the list before that left open:

- I read and confirm every decision record, 0001 onward, from the plain-language digest in
  `docs/human-checks/decisions.md`. `docs/how-built.md` states the review as in progress, and its
  wording changes to match what I agree with, change or question.
- My own hand checks: the 30-item ClimaQA sample and the 56 Gold and Silver leak pairs, from
  sheets under `docs/human-checks/`.
- Tools mode for `ibtracs-storm-v1` (decision 0023): its Sonnet run stopped at 225 of 300 items on
  2026-11-02, when the API account's credit ran out, with the ledger at $12.2793 of the $20 budget
  (`reports/spend.md`). It stays unfinished until I add API credit to that account myself.

## After that

- The drafts for distribution under `docs/release/`, written on 2026-11-02, stay there until I
  decide on each: the issue for the ClimaQA maintainers, the eval logs as a release asset, notes
  for an inspect_evals Register entry for ClimaQA, notes for the Prime Intellect Hub, and a Hugging
  Face dataset card, which carries the heat items with the two facts of decision 0027.

## Open questions

- Who reviews the cloze items as a domain expert (decision 0005). The sheet is ready:
  `reports/climaqa/expert_review_v2.csv`.
- The Jev third-reader study (decision 0008) is built and tested with its HTTP call mocked, but
  it runs only with a TypeSafe key, which I do not have.
- The GHCN-Daily station files stay unpublished unless NCEI states that they may be
  redistributed (decisions 0018 and 0027). NOAA's NODD listing of GHCN-Daily on the AWS open data
  registry gives CC0-1.0 for data disseminated through NODD; whether that covers NCEI's own files,
  and so gives the heat items a stated basis, is UNKNOWN (decision 0027).
