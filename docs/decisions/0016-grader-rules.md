# 0016: one answer-line rule, ACE by its rounding, cloze signs kept, and guards

Date: 2026-11-02. Status: accepted, 2026-11-02. From the Codex review's findings 7, 10, 12, 13
and 15, which I took up in fix batch 1.

Context: each contract grew its own answer parser. They differed in where the answer may sit
(an ERA5 test accepted `ANSWER: 285.5` followed by another line), in which Markdown they strip,
and in whether `1e999`, which parses as infinity, counts as a number. ACE paid any answer within
0.05 of the exact value, so 12.37 paid for an exact 12.34 although the prompt asks for one
decimal. The cloze normalizer turned all punctuation into spaces, so `-2` matched `2` and `x^2`
matched `x 2`. Three code paths failed late or not at all: an unknown heat question fell through
to the missed-days count, the ERA5 report crashed on an empty or one-item run, and a pair report
put two runs of different models or items side by side.

Decision:

- One answer-line rule for every `ANSWER:` line: ClimaQA's MCQ and the numeric answers of ERA5,
  IBTrACS and heat (`last_line` in each `contract.py`). The reply's last non-empty line, with
  Markdown emphasis (`*` and backticks) removed and U+2212 read as `-`, must be the answer line,
  with horizontal space only: the label and the answer share one line and nothing follows them.
  A number must be finite. `tests/test_answer_lines.py` runs the same cases through every
  contract: text after the answer, Markdown, an answer split over two lines, and `1e999`.
  Cloze answers have no answer line; the whole reply is the answer. A known limit: since every
  `*` is removed, `ANSWER: 2*3` reads as 23. No reply in any run's log under `logs/` has an
  asterisk inside the number of its answer line (checked 2026-11-02, the Phase 6 review); tools
  mode's bare number keeps its inner asterisks (decision 0023).
- ACE pays only a one-decimal answer equal to the exact value (kept to four decimals) rounded to
  one decimal, or either neighbour when the exact value is a tie: 5 at the second decimal and 0
  after it (`_roundings` in `ibtracs_storm_v1/contract.py`, integer arithmetic on the key times
  10^4, so no float rounding decides a tie).
- The cloze normalizer keeps what carries meaning in a science answer: the operators
  `+ / ^ = < >`, a decimal point between digits, and a minus sign before a number that is not
  inside a word. `*` is not kept, since models use it for bold. Articles drop only as whole
  words, so `a+b` stays. Hyphenated words still split.
- Guards: `earthgym.heat.items.key` raises on an unknown question; `earthgym.era5.report` refuses a run
  with no samples and gives a one-item run no standard error and no significance test;
  `earthgym.ablation.render_pair` refuses two runs of different models, a run that repeats an item
  id, and runs over different items.

Consequences:

- The reported runs were scored by the earlier rules. Re-grading their 2,620 logged replies with
  these rules (ClimaQA MCQ and cloze for Gemini 3.8 Flash and Sonnet 5.5, ERA5, IBTrACS with the
  rule shown and hidden, heat with the rules shown and the terms only) changes no score. 10 of
  Sonnet's cloze replies get another normalized answer string (their decimals kept) with the
  same verdict, and the items both models got wrong with the same answer stay the same 11 cloze
  and 18 MCQ items. Every reported number stands, and every Markdown report re-renders byte for
  byte from the logs.
- A reply that gives its answer line and then adds a line now scores 0, as does an ACE answer
  at two decimals. Every prompt already asks for `ANSWER:` on the last line, and the ACE question
  for one decimal.
- ACE to two decimals stays a later option (decision 0011).
