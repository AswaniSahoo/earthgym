# A filtered ClimaQA, and what two models score on it

Phase 2 of rlenv, written up on 2026-11-01. Every number below comes from a file in this repo;
the source is named next to it.

## The clean set

Clean set v1 keeps 350 Gold items, 222 multiple choice and 128 cloze, at the pinned revision
3f084a02, sha256 5f345d8e (`reports/climaqa/clean_v1_manifest.json`). An item leaves when the
experts rejected it (47), it leaks from Silver (26, plus 2 across tasks), its cloze answer
appears outside the blank (24), or its options are broken (2 "all or none of the above", 5
with the answer in the question, 1 with duplicate options); an item can have more than one
reason. The filter removes exact overlaps only: 21 kept items are near matches of Silver that
no human has ruled on, and a strict variant of 329 items leaves them out. One answer contract
scores both harnesses, the Inspect tasks and the verifiers
taskset: a multiple-choice reply must end with a line `ANSWER: X`; a cloze reply must be the
missing word or phrase, matched after case, punctuation and articles are folded
(`environments/climaqa_v1/climaqa_v1/contract.py`).

## Two models, item by item

Gemini 3.8 Flash ran on 2026-10-30 and Claude Sonnet 5.5 on 2026-11-01, each with its
provider's defaults (`reports/climaqa/runs/2026-10-30-gemini-3.8-flash.md`,
`reports/climaqa/runs/2026-11-01-claude-sonnet-5-5.md`). Paired by item
(`reports/climaqa/2026-11-01-sonnet-vs-gemini.md`):

| task | n | Gemini 3.8 Flash | Claude Sonnet 5.5 | only Gemini right | only Sonnet right | McNemar p |
|---|---|---|---|---|---|---|
| multiple choice | 222 | 0.874 | 0.874 | 6 | 6 | 1.000 |
| cloze | 128 | 0.742 | 0.508 | 33 | 3 | below 0.001 |

On multiple choice the two models tie item for item. On cloze, Sonnet's lower score is partly
a format result: the prompt says "Reply with only the missing word or phrase", and Sonnet
wrote more than one line on 34 of its 128 replies, often explaining first and ending with the
word in bold; Gemini never did. On 18 of Sonnet's 63 misses the last line alone is the key.
Crediting those 18 would still leave Sonnet at 0.648, below Gemini's 0.742, so not all of the
gap is format.

On the strict variant the picture holds: multiple choice 0.871 for both models over 210
items, cloze 0.739 against 0.513 over 119 (same report, strict table).

## Where both models agree and are both wrong

Both models gave the same wrong answer on 18 multiple-choice and 11 cloze items (same
comparison report). Two different models landing on the same wrong option is a hint that the
key, not the models, may be wrong; these items go to the expert review of decision 0005.

## Limits

- One run per model, on different days, each with its provider's default settings.
- The Gemini run cannot be repeated: no Vertex AI or Gemini calls are made from 2026-11-01
  (decision 0010).
- In the multiple-choice set, the key is the strictly longest option in 82 of the 222 items
  (`reports/climaqa/runs/2026-10-30-gemini-3.8-flash.md`, Limits); how much that cue helps
  either model is not measured.
- The Sonnet run cost $0.4123 for the 350 items through the Batch API (`reports/spend.md`).

## Reproduce

    uv run inspect eval src/rlenv/climaqa/tasks.py@climaqa_mcq \
        src/rlenv/climaqa/tasks.py@climaqa_cloze --model anthropic/claude-sonnet-5-5 --batch
    uv run python -m rlenv.climaqa.report <log dir> --out <report>.md
    uv run python -m rlenv.climaqa.compare <log dir a> <log dir b> --out <report>.md
