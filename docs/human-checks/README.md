# Hand checks

Three things only I can check. In the two CSV sheets, fill in `verdict` with yes, no or unsure, and
add a `note` when it helps. Nothing else in them needs changing.

## climaqa-sample.csv: is the key right? (30 items)

Thirty multiple-choice questions from ClimaQA's expert-validated Gold set, ten per difficulty level,
picked at random (seed 20261030). Read the question and its options, then `gold_answer`, the option
the benchmark marks as right.

- yes: the gold answer is correct, and it is the only correct option.
- no: the gold answer is wrong, another option is just as right, or the question cannot be answered
  from what it says. Say which in `note`.
- unsure: you cannot tell without a source. Say what you would need.

## leak-pairs.csv: is it the same item? (56 pairs)

Each row puts a Gold test question next to a question from ClimaQA's Silver set, the set the paper
fine-tunes its models on. A pair is listed because the two read alike (34 near matches), because the
Gold question appears word for word in another Silver task (7), or because it appears word for word
with a different answer (15).

- yes: they are the same item. A model trained on the Silver one has, in effect, seen the Gold one's
  answer: a leak, even if a few words differ.
- no: they ask different things, or their answers differ in substance, so training on one does not
  give away the other.
- unsure: say why.

## decisions.md: do I agree with each decision?

One row per decision record, in plain words: what it decides, why, and the main alternative. Write
agree, change (and what) or question (and what) in the last column. The records and
`docs/how-built.md` then change to match.
