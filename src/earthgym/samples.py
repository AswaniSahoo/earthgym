"""What several samples per item say about an environment's training signal (decision 0022):
the mean reward, the share of items whose reward varies across the samples (an item where every
sample earns the same reward gives a GRPO-style update nothing to compare), and pass@1 against
pass@k."""

import statistics
from math import comb


def pass_at_k(n: int, c: int, k: int) -> float:
    """The unbiased pass@k for one item: n samples, c of them passing (Chen et al. 2021)."""
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def by_item(rows: list[dict]) -> dict[str, list[float]]:
    """Each item's rewards, an errored sample counted as 0."""
    out: dict[str, list[float]] = {}
    for r in rows:
        out.setdefault(r["id"], []).append(0.0 if r.get("error") else r["reward"])
    return out


def summary(rows: list[dict], passed=lambda reward: reward == 1.0, k: int | None = None) -> dict:
    """Mean reward, share of items whose reward varies, pass@1 and pass@k (k: the samples per
    item); `passed` says when a sample counts as a pass."""
    items = by_item(rows)
    counts = {len(v) for v in items.values()}
    if len(counts) != 1:
        raise ValueError(f"every item needs the same number of samples, not {sorted(counts)}")
    n = counts.pop()
    k = n if k is None else k
    hits = [sum(map(passed, v)) for v in items.values()]
    return {
        "items": len(items),
        "samples": n,
        "mean_reward": statistics.fmean(r for v in items.values() for r in v),
        "varies": statistics.fmean(min(v) != max(v) for v in items.values()),
        "pass@1": statistics.fmean(pass_at_k(n, c, 1) for c in hits),
        f"pass@{k}": statistics.fmean(pass_at_k(n, c, k) for c in hits),
    }
