"""Spend on the Anthropic key: every model run is Claude Sonnet 5.5, capped at $20 in total
(decision 0010). The ledger is reports/spend.md.

Prices, USD per million tokens for Claude Sonnet 5.5, from Anthropic's pricing page
(https://platform.claude.com/docs/en/about-claude/pricing), fetched 2026-11-01: base input
$2, 5-minute cache writes $2.50, cache hits $0.10, output $10. Thinking tokens are billed as
output: the extended thinking page says `usage.output_tokens_details.thinking_tokens`
"reports how many of the billed output tokens were internal reasoning". The Batch API gives
"a 50 percent discount on both input and output tokens", and the cache multipliers "stack
with other pricing modifiers, including the Batch API discount", so a batch halves each price.

uv run python -m rlenv.spend "<run>" <log dir>   # appends the run's row to the ledger
"""

import argparse
import statistics
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

CAP = 20.0
LEDGER = Path("reports/spend.md")
PRICE = {"input": 2.0, "cache_write": 2.5, "cache_read": 0.10, "output": 10.0}
KINDS = ("input", "cache_write", "cache_read", "output", "reasoning")
TABLE = (
    "| run | date | log | mode | tokens in | cache write | cache read | tokens out | reasoning "
    "| cost USD | total USD |\n|---|---|---|---|---|---|---|---|---|---|---|\n"
)


def tokens(logs) -> dict:
    """Token totals over the logs' model usage."""
    return count(log.stats.model_usage for log in logs)


def count(usages) -> dict:
    """Token totals over model usage maps, a log's or a sample's; Inspect's input count
    excludes cached tokens."""
    usage = [u for d in usages for u in d.values()]
    return {
        "input": sum(u.input_tokens for u in usage),
        "cache_write": sum(u.input_tokens_cache_write or 0 for u in usage),
        "cache_read": sum(u.input_tokens_cache_read or 0 for u in usage),
        "output": sum(u.output_tokens for u in usage),
        "reasoning": sum(u.reasoning_tokens or 0 for u in usage),
    }


def cost(t: dict, batch: bool = False) -> float:
    """USD at the page's prices; reasoning tokens are already inside output."""
    usd = sum(t[k] * PRICE[k] for k in PRICE) / 1e6
    return usd / 2 if batch else usd


def project(costs: list[float], n: int) -> tuple[float, float]:
    """A run of n items priced from a probe's per-item costs: the mean, and the mean plus two
    standard errors as the margin a start decision uses."""
    mean = statistics.fmean(costs)
    return n * mean, n * (mean + 2 * statistics.stdev(costs) / len(costs) ** 0.5)


def check(text: str) -> float:
    """The running total, after checking each row's cost and total against its tokens."""
    total = 0.0
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| run "):
            continue
        cells = [c.strip() for c in line.strip("| ").split(" | ")]
        usd = cost(dict(zip(KINDS, map(int, cells[4:9]), strict=True)), cells[3] == "batch")
        total += usd
        if abs(float(cells[9]) - usd) > 1e-4 or abs(float(cells[10]) - total) > 1e-4:
            raise ValueError(f"ledger row {cells[0]!r} does not add up")
    return total


def add(run: str, log: str, logs, ledger: Path = LEDGER, batch: bool = False) -> float:
    """Append the run's row to the ledger and return the new total."""
    text = ledger.read_text("utf-8")
    t = tokens(logs)
    usd = cost(t, batch)
    total = check(text) + usd
    date = max(x.stats.completed_at for x in logs)[:10]
    mode = "batch" if batch else "standard"
    cells = [run, date, log, mode, *(str(t[k]) for k in KINDS), f"{usd:.4f}", f"{total:.4f}"]
    ledger.write_text(text.rstrip("\n") + "\n| " + " | ".join(cells) + " |\n", "utf-8")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a run's tokens and cost to the ledger.")
    parser.add_argument("run")
    parser.add_argument("log_dir")
    args = parser.parse_args()
    logs = [read_eval_log(info, header_only=True) for info in list_eval_logs(args.log_dir)]
    # --batch lands in the eval-level config, which overrides the model's own
    configs = [x.eval.model_generate_config.merge(x.plan.config) for x in logs]
    total = add(args.run, args.log_dir, logs, batch=all(c.batch for c in configs))
    print(f"total ${total:.4f} of ${CAP:.2f}; ${CAP - total:.4f} left")


if __name__ == "__main__":
    main()
