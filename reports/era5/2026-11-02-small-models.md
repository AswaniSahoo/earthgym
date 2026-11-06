# era5: small open models, 8 samples per item

Dated 2026-11-02. Each item answered 8 times by each model; a sample passes at a reward above 0. An
item whose reward varies across its samples is one a GRPO-style update can learn from
(decision 0022).

Drawn with llama.cpp on Kaggle's T4 GPUs (decisions 0022 and 0025).

| model | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | 627 | 8 | 0.029 | 0.357 | 0.063 | 0.357 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | 648 | 8 | 0.042 | 0.304 | 0.102 | 0.304 |

## Per question

| model | question | items | samples | mean reward | items whose reward varies | pass@1 | pass@8 |
|---|---|---|---|---|---|---|---|
| openai-api/llamacpp/qwen3.5-2b-q8_0 | 2m_temperature | 303 | 8 | 0.027 | 0.314 | 0.054 | 0.314 |
| openai-api/llamacpp/qwen3.5-2b-q8_0 | mean_sea_level_pressure | 324 | 8 | 0.032 | 0.398 | 0.071 | 0.398 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | 2m_temperature | 324 | 8 | 0.027 | 0.228 | 0.063 | 0.228 |
| openai-api/llamacpp/granite-4.0-h-1b-q8_0 | mean_sea_level_pressure | 324 | 8 | 0.058 | 0.380 | 0.140 | 0.380 |

## Settings and cost

- openai-api/llamacpp/qwen3.5-2b-q8_0: max_connections 32, max_tokens 4096, top_p 0.8, temperature 0.7, extra_body {'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}}; 5016 samples, 12304456 output tokens, from 2026-11-02T17:05:28+00:00 to 2026-11-03T04:02:53+00:00 (UTC). 1913 of 5016 replies stopped at the 4096-token cap; 1917 had no parseable answer and score 0. 21 items left out: a session's deadline stopped a sample of each before it finished.
- openai-api/llamacpp/granite-4.0-h-1b-q8_0: max_connections 32, max_tokens 4096, top_p 0.8, temperature 0.7, extra_body {'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}}; 5184 samples, 58696 output tokens, from 2026-11-02T06:48:26+00:00 to 2026-11-02T07:31:43+00:00 (UTC). 0 of 5184 replies stopped at the 4096-token cap; 491 had no parseable answer and score 0.
