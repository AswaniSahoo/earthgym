# Spend on the Anthropic key

Every rlenv model run uses Claude Sonnet 5.5 on the Anthropic key, within a managed budget of $20
in total (Aswani, 2026-11-01; decision 0010). Before each run a small probe projects its cost,
and no run was started that would have taken the total past $20. Nothing enforces this when a
run starts: `tests/test_spend.py` checks after each run that every row's cost matches its
tokens, that the running total adds up, and that the total stays within $20, and the ledger
refuses logs from models it has no price for.

Prices, USD per million tokens for Claude Sonnet 5.5, from Anthropic's pricing page
(https://platform.claude.com/docs/en/about-claude/pricing), fetched 2026-11-01: base input
$2, 5-minute cache writes $2.50, cache hits $0.10, output $10. Thinking tokens are billed as
output tokens, and a Batch API run (mode batch) pays half of every price. The tokens are the
ones Inspect recorded in each log; the bill in the Anthropic Console is the authority and is
not read here.

The Gemini 3.8 Flash runs on Vertex AI are separate and stay as recorded in their reports.

Rows are added with `uv run python -m rlenv.spend "<run>" <log dir>`.

Final for the Definition of done (2026-11-01): 12 runs, $9.1298 of the $20 budget.

| run | date (UTC) | log | mode | tokens in | cache write | cache read | tokens out | reasoning | cost USD | total USD |
|---|---|---|---|---|---|---|---|---|---|---|
| ERA5 probe, 12 items | 2026-10-31 | logs/2026-11-01-era5-claude-sonnet-5-5-probe | batch | 5382 | 0 | 0 | 4102 | 0 | 0.0259 | 0.0259 |
| ERA5 full run, 720 items | 2026-10-31 | logs/2026-11-01-era5-claude-sonnet-5-5 | batch | 322920 | 0 | 0 | 257940 | 0 | 1.6126 | 1.6385 |
| ClimaQA probe, 16 items | 2026-11-01 | logs/2026-11-01-climaqa-claude-sonnet-5-5-probe | batch | 2237 | 0 | 0 | 2990 | 342 | 0.0172 | 1.6557 |
| ClimaQA clean v1, 350 items | 2026-11-01 | logs/2026-11-01-climaqa-claude-sonnet-5-5 | batch | 52251 | 644 | 0 | 71858 | 8013 | 0.4123 | 2.0680 |
| Phase 4 probe, 6 items | 2026-11-01 | logs/2026-11-01-ibtracs-claude-sonnet-5-5-probe | batch | 24 | 10477 | 0 | 2293 | 732 | 0.0246 | 2.0926 |
| Phase 4 ibtracs-storm-v1, 300 items | 2026-11-01 | logs/2026-11-01-ibtracs-claude-sonnet-5-5 | batch | 1685 | 539944 | 2137 | 137181 | 48487 | 1.3626 | 3.4553 |
| Phase 5 probe, 6 items | 2026-11-01 | logs/2026-11-01-heat-claude-sonnet-5-5-probe | batch | 24 | 12447 | 0 | 4764 | 2725 | 0.0394 | 3.4947 |
| Phase 4 rules-hidden probe, 6 items | 2026-11-01 | logs/2026-11-01-ibtracs-hidden-claude-sonnet-5-5-probe | batch | 24 | 9935 | 0 | 4722 | 2826 | 0.0361 | 3.5307 |
| Phase 4 rules-hidden, 300 items | 2026-11-01 | logs/2026-11-01-ibtracs-hidden-claude-sonnet-5-5 | batch | 2090 | 512499 | 2077 | 227435 | 124643 | 1.7800 | 5.3107 |
| Phase 5 heat-basis-v1, 300 items | 2026-11-01 | logs/2026-11-01-heat-claude-sonnet-5-5 | batch | 625516 | 0 | 0 | 250923 | 153313 | 1.8801 | 7.1908 |
| Phase 5 terms-only probe, 6 items | 2026-11-01 | logs/2026-11-01-heat-terms-claude-sonnet-5-5-probe | batch | 12325 | 0 | 0 | 4600 | 2817 | 0.0353 | 7.2262 |
| Phase 5 terms-only, 300 items | 2026-11-01 | logs/2026-11-01-heat-terms-claude-sonnet-5-5 | batch | 618216 | 0 | 0 | 257075 | 160216 | 1.9036 | 9.1298 |
