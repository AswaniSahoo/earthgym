# Expert review for clean set v2

Decision 0005 (accepted 2026-10-30): before clean set v2, a domain expert confirms or rejects
every flagged item, and only the expert writes accepted answers. The sheet is
`expert_review_v2.csv`, 83 rows, written once by `uv run python -m earthgym.climaqa.expert_sheet`;
the code never overwrites it.

## Rows

- 28 MCQ and 33 cloze items that Gemini 3.8 Flash missed on 2026-10-30, with the build
  session's sort (`flag`) and reason (`our_note`). The full reasoning is in
  `runs/2026-10-30-gemini-3.8-flash-mcq-misses.md` and
  `runs/2026-10-30-gemini-3.8-flash-cloze-misses.md`.
- 2 kept MCQ items the baseline review flagged as testing the source document (56, 215).
  Among the misses, the review also flagged mcq 132, cloze 59 and 144 (the source document),
  cloze 8 and 22 (the key abbreviates the words before the mask), and mcq 167 and 207 (the
  same question twice).
- 20 items the model got right (seed 20261030), because only misses were read: please check
  that the key is right.

## Columns

`id`, `task`, `question`; `options` (MCQ, in the order the model saw); `key`; `model_answer`;
`flag` and `our_note` (one non-expert reader's sort, not a verdict). The expert fills:

- `verdict`. MCQ: `key_ok`, `key_wrong` (put the right letter in `expert_note`), `ambiguous`
  (more than one option is right: say fix or drop), `not_science`, `drop`. Cloze: `key_only`,
  `accept_more`, `ambiguous`, `drop`.
- `accepted_answers` (cloze with `accept_more` only): every answer that should earn the
  reward, separated by `;`.
- `expert_note`: anything else.
