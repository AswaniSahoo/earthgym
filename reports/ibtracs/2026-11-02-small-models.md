# ibtracs: small open models, 8 samples per item

Dated 2026-11-02. Each item answered 8 times by each model; a sample passes at reward 1. An
item whose reward varies across its samples is one a GRPO-style update can learn from
(decision 0022).

Drawn with llama.cpp on Kaggle's T4 GPUs (decisions 0022 and 0025).

| model | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | 300 | 8 | 0.370 | 0.317 | 0.370 | 0.537 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | 300 | 8 | 0.032 | 0.120 | 0.032 | 0.120 |

## Per question

| model | question | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | ace | 100 | 8 | 0.160 | 0.420 | 0.160 | 0.430 |
| openai-api/llamacpp/qwen3.5-2b-q8_0 | hurricane_hours | 100 | 8 | 0.025 | 0.180 | 0.025 | 0.180 |
| openai-api/llamacpp/qwen3.5-2b-q8_0 | peak_category | 100 | 8 | 0.925 | 0.350 | 0.925 | 1.000 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | ace | 100 | 8 | 0.022 | 0.140 | 0.022 | 0.140 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | hurricane_hours | 100 | 8 | 0.007 | 0.030 | 0.007 | 0.030 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | peak_category | 100 | 8 | 0.066 | 0.190 | 0.066 | 0.190 |

## Settings and cost

- openai-api/llamacpp/qwen3.5-2b-q8_0: max_connections 32, max_tokens 4096, top_p 0.8, temperature 0.7, extra_body {'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}}; 2400 samples, 4035120 output tokens, from 2026-11-02T04:44:50+00:00 to 2026-11-02T13:07:04+00:00 (UTC). 296 of 2400 replies stopped at the 4096-token cap; 296 had no parseable answer and score 0.
- openai-api/llamacpp/granite-4.0-h-1b-q8_0: max_connections 32, max_tokens 4096, top_p 0.8, temperature 0.7, extra_body {'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}}; 2400 samples, 188813 output tokens, from 2026-11-02T04:14:36+00:00 to 2026-11-02T05:18:29+00:00 (UTC). 3 of 2400 replies stopped at the 4096-token cap; 930 had no parseable answer and score 0.
