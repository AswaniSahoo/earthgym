# Spend on the Anthropic key

Every rlenv model run uses Claude Sonnet 5.5 on the Anthropic key, with a hard cap of $20 in
total (Aswani, 2026-11-01; decision 0010). Before each run a small probe projects its cost,
and no run starts that would take the total past the cap. `tests/test_spend.py` checks every
row's cost against its tokens, the running total, and the cap.

Prices, USD per million tokens for Claude Sonnet 5.5, from Anthropic's pricing page
(https://platform.claude.com/docs/en/about-claude/pricing), fetched 2026-11-01: base input
$2, 5-minute cache writes $2.50, cache hits $0.10, output $10. Thinking tokens are billed as
output tokens, and a Batch API run (mode batch) pays half of every price. The tokens are the
ones Inspect recorded in each log; the bill in the Anthropic Console is the authority and is
not read here.

The Gemini 3.8 Flash runs on Vertex AI are separate and stay as recorded in their reports.

Rows are added with `uv run python -m rlenv.spend "<run>" <log dir>`.

| run | date (UTC) | log | mode | tokens in | cache write | cache read | tokens out | reasoning | cost USD | total USD |
|---|---|---|---|---|---|---|---|---|---|---|
| ERA5 probe, 12 items | 2026-10-31 | logs/2026-11-01-era5-claude-sonnet-5-5-probe | batch | 5382 | 0 | 0 | 4102 | 0 | 0.0259 | 0.0259 |
