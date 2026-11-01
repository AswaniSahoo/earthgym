# Clean ClimaQA v1: anthropic/claude-sonnet-5-5 against google/vertex/gemini-3.8-flash

Each item paired across the two runs. McNemar's exact test on the items only one model
got right, two-sided. Clean set v1 is exact-overlap-filtered: 21 near matches of Silver
stay in, unresolved, and the strict variant below leaves them out.

| task | n | accuracy google/vertex/gemini-3.8-flash | accuracy anthropic/claude-sonnet-5-5 | both right | both wrong | only google/vertex/gemini-3.8-flash | only anthropic/claude-sonnet-5-5 | McNemar p |
|---|---|---|---|---|---|---|---|---|
| climaqa_cloze | 128 | 0.742 | 0.508 | 62 | 30 | 33 | 3 | 0.000 |
| climaqa_mcq | 222 | 0.874 | 0.874 | 188 | 22 | 6 | 6 | 1.000 |

## Strict variant: the near matches of Silver left out

| task | n | accuracy google/vertex/gemini-3.8-flash | accuracy anthropic/claude-sonnet-5-5 | both right | both wrong | only google/vertex/gemini-3.8-flash | only anthropic/claude-sonnet-5-5 | McNemar p |
|---|---|---|---|---|---|---|---|---|
| climaqa_cloze | 119 | 0.739 | 0.513 | 58 | 28 | 30 | 3 | 0.000 |
| climaqa_mcq | 210 | 0.871 | 0.871 | 177 | 21 | 6 | 6 | 1.000 |

## Accuracy by complexity

| task | level | n | google/vertex/gemini-3.8-flash | anthropic/claude-sonnet-5-5 |
|---|---|---|---|---|
| climaqa_cloze | none | 128 | 0.742 | 0.508 |
| climaqa_mcq | BASE | 107 | 0.907 | 0.897 |
| climaqa_mcq | HYPOTHETICAL | 46 | 0.848 | 0.848 |
| climaqa_mcq | REASONING | 69 | 0.841 | 0.855 |

## Items both models got wrong with the same answer

Candidates for a wrong key or a shared misconception; none is reviewed yet (decision
0005's expert review).

- climaqa_cloze: 11 items (gold/cloze/102, gold/cloze/111, gold/cloze/139, gold/cloze/26, gold/cloze/34, gold/cloze/37, gold/cloze/4, gold/cloze/47, gold/cloze/56, gold/cloze/66, gold/cloze/85)
- climaqa_mcq: 18 items (gold/mcq/102, gold/mcq/113, gold/mcq/125, gold/mcq/130, gold/mcq/141, gold/mcq/167, gold/mcq/187, gold/mcq/207, gold/mcq/210, gold/mcq/232, gold/mcq/249, gold/mcq/255, gold/mcq/277, gold/mcq/279, gold/mcq/36, gold/mcq/50, gold/mcq/74, gold/mcq/97)

## Cloze replies that explain first

The cloze prompt says "Reply with only the missing word or phrase." Replies over
more than one line, and wrong replies whose last line alone is the key:

| task | model | replies over one line | wrong, last line alone right |
|---|---|---|---|
| climaqa_cloze | google/vertex/gemini-3.8-flash | 0 | 0 |
| climaqa_cloze | anthropic/claude-sonnet-5-5 | 34 | 18 |

## Limits

- One run per model, each with its provider's default settings, on different days.
- The Gemini run cannot be repeated: no Vertex AI or Gemini calls from 2026-11-01
  (decision 0010).
- Cloze answers count as the same only when their normalized text matches exactly.
- Logs: `logs/2026-10-30-gemini-3.8-flash` and `logs/2026-11-01-climaqa-claude-sonnet-5-5` (not in git).
