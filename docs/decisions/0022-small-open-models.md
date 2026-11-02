# 0022: two small open models, 8 samples per item, on the laptop's GPU

Date: 2026-11-02. Status: accepted, 2026-11-02.

Context: one paid model and one draw per item cannot show whether an environment gives a
training signal. GRPO-style training compares several samples of the same item, so it learns
only from items whose reward varies across samples. On 2026-11-02 I allowed local open models
at no API cost, and Kaggle's free GPUs. Claude Sonnet 5.5 stays the only paid model, and Vertex
AI and Gemini stay off (decision 0010).

Decision:

- Models: two small instruct models from different families, both Apache-2.0 and ungated.
  Q8_0 is the quantization closest to the full weights that fits the card, and the radar rows
  give the reasons for these two over the other candidates.
  - Qwen3.5-2B: `unsloth/Qwen3.5-2B-GGUF` at `f6d5376be1edb4d416d56da11e5397a961aca8ae`,
    `Qwen3.5-2B-Q8_0.gguf`, 2,012,012,800 bytes, sha256
    `1b04acba824817554f4ce23639bc8495ff70453b8fcb047900c731521021f2c1`.
  - IBM Granite 4.0 H-1B, a hybrid with Mamba2 layers: `ibm-granite/granite-4.0-h-1b-GGUF` at
    `c2cb1972f511add21f3bae244990b8ff3a3ffb23`, `granite-4.0-h-1b-Q8_0.gguf`, 1,558,926,560
    bytes, sha256 `f29248184ca766350e56e6d161c2a637ad302a6d595e15d4a62cd58327a0ac0e`.
- Runner: llama.cpp's `llama-server`, build b11960 (the binaries of release v0.8.0), the CUDA
  12.8 build (`llama-b11960-bin-ubuntu-cuda-12.8-x64.tar.gz`, sha256
  `64d57beb9abb637c177c6afb313760a0c0782224cac71e74869eed5b8f9a1ea4`, with its runtime, sha256
  `7c4d5974bd39649df649649e5d71950688a70e37aaae00bf11afbb656ea2cc56`), on the RTX 3050
  Laptop GPU with 4 GB: `-ngl all -c 65536 -np 16 -kvu`, 16 parallel slots sharing a
  65,536-token cache. On 16 concurrent heat requests of 512 tokens it gave 275 tokens a second
  in all; the Vulkan build gave 186, and with 8 slots about 160.
- Harness: Inspect 0.3.286, model `openai-api/llamacpp/<name>`. Its OpenAI-compatible provider
  needs openai 3.4.0 or newer, while verifiers 0.4.0 requires openai below 3.0.0, so the runs add
  `openai==3.42.1` for the run only (`uv run --with 'openai==3.42.1'`), outside `uv.lock`.
- Settings: 8 samples per item (`--epochs 8`), temperature 0.7, top_p 0.8 and top_k 20 (the
  Qwen card's settings for its non-thinking mode, without its presence penalty of 1.5), thinking
  off (`enable_thinking: false`), up to 4,096 output tokens, 16 connections, and no seed. Granite's
  card gives no sampling settings, so it gets the same ones. With no seed each sample is a fresh
  draw: a rerun gives other samples, and only the statistics can be compared.
- Why thinking off and 4,096 tokens: in a probe of 20 heat items at 8 samples with Qwen's
  thinking on, all 160 samples spent their 1,024 tokens thinking and wrote no answer. With
  thinking off, heat replies go through the season day by day, a median of 3,068 tokens on 16
  items, with 4 of the 16 still at 4,096; IBTrACS replies had a median of 1,486.
- Items: every bundled item as it stands: ClimaQA 350 (the strict 329 are a subset), ERA5 648,
  IBTrACS 300 and heat 300, both with the rules shown.
- Measures, per environment (`earthgym.samples`): the mean reward over all samples; the share of
  items whose reward varies across their 8 samples; and pass@1 against pass@8, by the unbiased
  estimator of Chen et al. (2021). A sample passes at reward 1, or in ERA5, whose reward is
  continuous, when it beats the better of persistence and climatology (a reward above 0).
- Per-item results: one row per sample (id, epoch, parsed answer, reward, tokens) under
  `reports/<env>/results/`, as for the Sonnet runs (decision 0019).

The main alternative was a Kaggle GPU, which is faster but was the larger setup: its GPU type,
driver version and Python had to be checked, and the code uploaded. vLLM needs torch, too large
a download for this card's 4 GB.

Consequences:

- The runs cost nothing but take long on this GPU; the report gives the real times.
- They are not seed-reproducible, by choice: a fixed seed would make Inspect send the same seed
  for all 8 samples.
- `openai==3.42.1` is a run-time dependency outside the lock, pinned in the command.
- Decision 0010's rule of one model now covers paid runs only.
