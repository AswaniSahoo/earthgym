# 0010: every model run on Claude Sonnet 5.5, $20 in total, no Vertex

Date: 2026-11-01. Status: accepted, 2026-11-01.

Context: the ERA5 baseline was approved on Gemini 3.8 Flash on Vertex AI with a guard of 1.5
million tokens. The 10-item probe (`logs/2026-11-01-era5-probe/`, all MSLP at 24 h) projected
1,731,960 tokens for the 720 items, so the full run stopped (docs/log.md, 2026-11-01).

Decision, in my words of 2026-11-01:

- "use sonnet 5-5 and use as much credit you need": the ERA5 baseline moves to Claude Sonnet
  5.5. The Gemini full run is dropped and its probe log kept as a record.
- "use for everything keep cap at 20 $": Claude Sonnet 5.5 on the Anthropic key for every
  earthgym model run, with a hard cap of $20 in total on that key. This replaces the open budget
  of the first message. Order within the cap: the ERA5 run, then clean ClimaQA v1 (the second
  model for the inspect_evals Register, compared with Gemini), then the Phase 4 baseline, then
  Phase 5.
- "never use my gemini further ... from now no more vertex ai call": no Vertex AI or Gemini
  calls of any kind, probes and smoke tests included. Gemini logs, reports and numbers stay
  as they are, and comparisons may read those logs.

How I run it (Inspect 0.3.286 source paths are under `inspect_ai/`):

- Model `anthropic/claude-sonnet-5-5`. The id is the Claude API ID on Anthropic's models
  overview (platform.claude.com/docs/en/about-claude/models/overview, fetched 2026-11-01).
  Inspect sends Claude to Vertex only for a service prefix such as `anthropic/vertex/...`
  (`model/_providers/anthropic.py:451-456`), so this name goes to the Anthropic API.
- Package `anthropic==2.3.0` in the eval group, the newest on PyPI (2026-10-23). Inspect
  needs 2.0.0 or newer: `MIN_VERSION = "2.0.0"`, "2.0.0 split MessageParam into role-specific
  types" (`model/_providers/providers.py:398-399`).
- `google-genai` leaves the eval group and takes `google-auth` with it, so neither a
  `google/...` model nor `anthropic/vertex/...` can run here; `tests/test_spend.py` fails if
  either client comes back. Reading the old Gemini logs needs neither. CI runs only ruff,
  pytest, `vf-validate --only-noop` and an Inspect eval on `mockllm/model`.
- Key: `ANTHROPIC_API_KEY` in `.env` at the repo root (ignored by git, mode 600), added by me.
  The Inspect CLI loads it: `init_dotenv()` (`_cli/main.py:61`) calls
  `find_dotenv(usecwd=True)` (`_util/dotenv.py:23`) and overrides variables already set only
  inside VS Code (line 20). This shell sets no ANTHROPIC variable. The key is never printed
  or logged.
- Generate settings: none but `--batch`, so the provider defaults apply. Inspect sends
  `max_tokens` 32000 (`ANTHROPIC_MAX_TOKENS`, `model/_providers/_anthropic_max_tokens.py:8`)
  and `thinking: {"type": "adaptive"}` with a `block_binding` setting
  (`apply_thinking_block_binding`, `model/_providers/anthropic.py:1716-1718`); it sends an
  effort in `output_config` only when `reasoning_effort` is set (lines 1456-1460). The ERA5
  probe's logged request shows exactly these fields. So Sonnet 5.5 thinks adaptively at its
  default effort, `high`: Anthropic's "Steering thinking" page lists "`high` (default on most
  models)" and `medium` as the default only on Claude Opus 5.5 and Claude Haiku 5.5. No
  temperature or seed is sent, so each reply is one draw.
- Prompt caching: Inspect enables `cache_prompt` by default and sends a top-level
  `cache_control` (`model/_generate_config.py:153-154`, `model/_providers/anthropic.py:886-887`),
  so every prompt over the 512-token minimum was billed as a cache write at 1.25 times the
  input price, with no reuse since every prompt differs: about $0.133 of the $1.3626 of the
  Phase 4 run (Phase 4 review, L1). From the Phase 5 full runs on, single-turn runs pass
  `--cache-prompt false`. The ledger prices the cache writes either way.
- Batch API for full runs. A batch costs half: "a 50 percent discount on both input and
  output tokens", and the cache multipliers "stack with other pricing modifiers, including the
  Batch API discount" (pricing page, fetched 2026-11-01). The requests are the same, so the
  replies are draws from the same model and settings. At standard prices the four runs would
  not fit in $20 on rough sizes (ERA5 alone about $15 at 2,000 output tokens an item); at
  batch prices they can. With `--batch`, Inspect runs up to 10,000 samples at once
  (`DEFAULT_MAX_CONNECTIONS_BATCH`, `_util/constants.py:10`) in batches of 100 for Anthropic.
- Prices (pricing page, fetched 2026-11-01), USD per million tokens for Sonnet 5.5: base input
  $2, 5-minute cache writes $2.50, cache hits $0.10, output $10; batch input $1, batch output
  $5. Thinking tokens are billed as output: `usage.output_tokens_details.thinking_tokens`
  "reports how many of the billed output tokens were internal reasoning" (extended thinking
  page).
- Ledger: `reports/spend.md`, one row per run, probes included, from the tokens Inspect
  recorded, with a running total. `tests/test_spend.py` checks every row against its tokens
  and the total against the cap.
- Before each run, a probe balanced over the run's strata projects its cost. The run starts
  only if the total so far plus the projection, with a margin for the probe's spread, stays
  under $20; otherwise the run waits for my decision. Each run's share is set so the later
  runs in the order still fit. The ERA5 probe is 12 items, the first 2 of each variable and
  lead (`uv run python -m earthgym.era5.tasks`), sent through the Batch API so it tests the
  full run's path.

How the budget is kept (2026-11-02, from the Codex review's finding 11): the $20 is a managed
budget, not an enforced cap. Probes projected each run's cost before it started, and the
ledger is checked after each run; nothing stops a run that would pass $20 when it starts.
`earthgym.spend` refuses logs from models it has no price for.

Consequences:

- Thinking is adaptive, so tokens per item vary from item to item and from run to run; the
  ledger records what was spent, and the projection is only a guide.
- A batch is slower than live calls: Anthropic says "most batches completing within 1 hour",
  and a batch that does not finish within 24 hours expires (batch processing page, fetched
  2026-11-01).
- The ledger counts the tokens in the logs. The Anthropic Console's bill is the authority and
  is not read here, since reading it needs the account.
