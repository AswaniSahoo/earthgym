# climaqa: small open models, 8 samples per item

Dated 2026-11-02. Each item answered 8 times by each model; a sample passes at reward 1. An
item whose reward varies across its samples is one a GRPO-style update can learn from
(decision 0022).

Drawn with llama.cpp on Kaggle's T4 GPUs (decisions 0022 and 0025).

| model | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | 350 | 8 | 0.503 | 0.417 | 0.503 | 0.711 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | 350 | 8 | 0.378 | 0.151 | 0.378 | 0.463 |

## Strict variant: the near matches of Silver left out

| model | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | 329 | 8 | 0.506 | 0.426 | 0.506 | 0.720 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | 329 | 8 | 0.388 | 0.146 | 0.388 | 0.468 |

## Per question

| model | question | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | cloze | 128 | 8 | 0.145 | 0.305 | 0.145 | 0.336 |
| openai-api/llamacpp/qwen3.5-2b-q8_0 | mcq | 222 | 8 | 0.710 | 0.482 | 0.710 | 0.928 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | cloze | 128 | 8 | 0.020 | 0.031 | 0.020 | 0.039 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | mcq | 222 | 8 | 0.584 | 0.221 | 0.584 | 0.707 |

## Settings and cost

- openai-api/llamacpp/qwen3.5-2b-q8_0: max_connections 32, max_tokens 4096, top_p 0.8, temperature 0.7, extra_body {'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}}; 2800 samples, 1113386 output tokens, from 2026-11-02T03:53:47+00:00 to 2026-11-02T04:44:42+00:00 (UTC). 52 of 2800 replies stopped at the 4096-token cap; 51 had no parseable answer and score 0.
- openai-api/llamacpp/granite-4.0-h-1b-q8_0: max_connections 32, max_tokens 4096, top_p 0.8, temperature 0.7, extra_body {'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}}; 2800 samples, 30377 output tokens, from 2026-11-02T03:53:47+00:00 to 2026-11-02T04:14:24+00:00 (UTC). 0 of 2800 replies stopped at the 4096-token cap; 30 had no parseable answer and score 0.
