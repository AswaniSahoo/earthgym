# heat: small open models, 8 samples per item

Dated 2026-11-02. Each item answered 8 times by each model; a sample passes at reward 1. An
item whose reward varies across its samples is one a GRPO-style update can learn from
(decision 0022).

Drawn with llama.cpp on Kaggle's T4 GPUs (decisions 0022 and 0025).

| model | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | 300 | 8 | 0.217 | 0.487 | 0.217 | 0.523 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | 300 | 8 | 0.028 | 0.163 | 0.028 | 0.163 |

## Per question

| model | question | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | events | 100 | 8 | 0.345 | 0.730 | 0.345 | 0.790 |
| openai-api/llamacpp/qwen3.5-2b-q8_0 | missed_days | 100 | 8 | 0.029 | 0.180 | 0.029 | 0.180 |
| openai-api/llamacpp/qwen3.5-2b-q8_0 | trigger_days | 100 | 8 | 0.279 | 0.550 | 0.279 | 0.600 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | events | 100 | 8 | 0.037 | 0.230 | 0.037 | 0.230 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | missed_days | 100 | 8 | 0.039 | 0.210 | 0.039 | 0.210 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | trigger_days | 100 | 8 | 0.006 | 0.050 | 0.006 | 0.050 |

## Settings and cost

- openai-api/llamacpp/qwen3.5-2b-q8_0: max_connections 32, max_tokens 4096, top_p 0.8, temperature 0.7, extra_body {'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}}; 2400 samples, 7718175 output tokens, from 2026-11-02T17:05:28+00:00 to 2026-11-03T01:00:41+00:00 (UTC). 930 of 2400 replies stopped at the 4096-token cap; 930 had no parseable answer and score 0.
- openai-api/llamacpp/granite-4.0-h-1b-q8_0: max_connections 32, max_tokens 4096, top_p 0.8, temperature 0.7, extra_body {'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}}; 2400 samples, 496324 output tokens, from 2026-11-02T05:18:46+00:00 to 2026-11-02T06:48:10+00:00 (UTC). 0 of 2400 replies stopped at the 4096-token cap; 904 had no parseable answer and score 0.
