# ClimaQA baseline

Clean set v1 (exact-overlap-filtered; 21 near matches of Silver unresolved), sha256 `5f345d8e234b65a310b8de47f1d99059b47c6e2429c5f22b80b154ef6b698464`, scored by climaqa_v1/contract.py.

| task | model | n | accuracy | stderr | format failures |
|---|---|---|---|---|---|
| climaqa_cloze | anthropic/claude-sonnet-5-5 | 128 | 0.508 | 0.044 | n/a |
| climaqa_mcq | anthropic/claude-sonnet-5-5 | 222 | 0.874 | 0.022 | 2 |

## Accuracy by complexity

| task | complexity | n | accuracy |
|---|---|---|---|
| climaqa_cloze | none | 128 | 0.508 |
| climaqa_mcq | BASE | 107 | 0.897 |
| climaqa_mcq | HYPOTHETICAL | 46 | 0.848 |
| climaqa_mcq | REASONING | 69 | 0.855 |

## Run config

Prompts and scoring rules: climaqa_v1/contract.py at the commit shown. Tokens out include reasoning tokens.

| task | commit | generate config | tokens in | tokens out | reasoning | log |
|---|---|---|---|---|---|---|
| climaqa_cloze | f4db6e8 | batch 100 | 13339 | 9604 | 5144 | 2026-11-01T00-43-51-00-00_climaqa-cloze_PSt74BjC4tMRMTXDk4RD5x.eval |
| climaqa_mcq | f4db6e8 | batch 100 | 38912 | 62254 | 2869 | 2026-11-01T00-43-51-00-00_climaqa-mcq_TjRQNh8StVCd8PTSaACzfX.eval |

## Limits

- Clean set v1 keeps 21 Gold items that are near matches of Silver (leak.near_match in reports/climaqa/findings.json).
- Cloze counts exact matches only, ignoring case, punctuation and articles.
- climaqa_mcq keys: A 60, B 51, C 51, D 60; the key is the strictly longest option in 82 of 222 items.

Runs: climaqa_cloze from 2026-11-01T00:50:39+00:00 to 2026-11-01T00:56:39+00:00, climaqa_mcq from 2026-11-01T00:43:51+00:00 to 2026-11-01T00:50:39+00:00. inspect_ai 0.3.286.
Logs: `logs/2026-11-01-climaqa-claude-sonnet-5-5` (not in git).
