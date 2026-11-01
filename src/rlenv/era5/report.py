"""Dated report of a model run on era5-forecast-v1, from its Inspect log (decision 0010).

uv run python -m rlenv.era5.report <log dir> --out reports/era5/<date>-<model>.md
"""

import argparse
import json
import statistics
from pathlib import Path

from era5_forecast_v1.taskset import records
from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log

from rlenv import spend
from rlenv.era5 import baselines


def _midpoint(item: dict) -> float:
    return baselines.reward(item, baselines.BASELINES["midpoint"](item))


def _paired(paid: dict, by_id: dict) -> dict:
    """The model's reward minus the midpoint's, item by item: mean, standard error, counts."""
    d = [paid[i] - _midpoint(by_id[i]) for i in paid]
    se = statistics.stdev(d) / len(d) ** 0.5 if len(d) > 1 else None
    return {"diff": statistics.fmean(d), "se": se} | {
        "higher": sum(x > 0 for x in d),
        "lower": sum(x < 0 for x in d),
        "tied": sum(x == 0 for x in d),
    }


def summarize(log: EvalLog, items: list[dict]) -> dict:
    """Scores, parse failures, tokens and cost of one run; the model is graded like the
    baselines, on the items it answered. A run of one item has no standard error."""
    if not log.samples:
        raise ValueError("the log has no samples")
    by_id = {r["id"]: r for r in items}
    config = log.eval.model_generate_config.merge(log.plan.config)
    batch = bool(config.batch)
    forecasts, rewards, item_costs, paid = {}, [], [], {}
    parse_failures = errors = 0
    for s in log.samples or []:
        if s.metadata["truth"] != by_id[s.id]["truth"]:
            raise ValueError(f"{s.id}: the log's truth differs from the item's")
        item_costs.append(spend.cost(spend.count([s.model_usage]), batch))
        if s.error or not s.scores:
            errors += 1
            rewards.append(0.0)
            paid[s.id] = 0.0
            continue
        score = next(iter(s.scores.values()))
        rewards.append(float(score.value))
        paid[s.id] = float(score.value)
        if score.answer:
            forecasts[s.id] = float(score.answer)
        else:
            parse_failures += 1
    label = log.eval.model.split("/")[-1]
    answered = [by_id[i] for i in forecasts]
    model = {label: lambda item: forecasts[item["id"]]}
    t = spend.tokens([log])
    rev = log.eval.revision
    settings = config.model_dump(exclude_none=True)
    return {
        "model": log.eval.model,
        "label": label,
        "n": len(rewards),
        "parsed": len(forecasts),
        "parse_failures": parse_failures,
        "errors": errors,
        "reward": statistics.fmean(rewards),
        "stderr": statistics.stdev(rewards) / len(rewards) ** 0.5 if len(rewards) > 1 else None,
        "table": baselines.rows(answered, baselines.forecasters(items) | model),
        "paired": _paired(paid, by_id),
        "tokens": t,
        "batch": batch,
        "cost": spend.cost(t, batch),
        "item_costs": item_costs,
        "commit": f"{rev.commit}{' (dirty)' if rev.dirty else ''}" if rev else "unknown",
        "generate_config": ", ".join(f"{k} {v}" for k, v in settings.items()) or "none",
        "inspect_ai": log.eval.packages.get("inspect_ai", ""),
        "started": log.stats.started_at,
        "completed": log.stats.completed_at,
        "log": Path(log.location).name,
    }


def _paired_line(p: dict) -> str:
    if p["se"] is None:
        se, verdict = "n/a", "too few items to test"
    else:
        se = f"{p['se']:.4f}"
        verdict = "significant" if abs(p["diff"]) > 2 * p["se"] else "not significant"
        verdict += " at two standard errors"
    return (
        f"Against the midpoint (persistence + climatology) / 2, item by item: {p['diff']:+.4f} "
        f"(SE {se}); the model is higher on {p['higher']} items, lower on {p['lower']} "
        f"and tied on {p['tied']}: {verdict}."
    )


def render(s: dict) -> str:
    t, n = s["tokens"], s["n"]
    se = "n/a, one item" if s["stderr"] is None else f"{s['stderr']:.3f}"
    lines = [
        f"# era5-forecast-v1 on {s['label']}",
        "",
        f"Model `{s['model']}` on {n} items, scored by era5_forecast_v1/contract.py at commit "
        f"{s['commit']}.",
        "",
        "## Result",
        "",
        f"Mean reward {s['reward']:.3f} (stderr {se}) over all {n} items, parse "
        "failures and errors scored 0. The reward is the skill over the better of persistence "
        "and climatology for each item, clipped to [0, 1] (decision 0007).",
        "",
        f"Replies without a parseable answer line: {s['parse_failures']} of {n}. Samples that "
        f"errored: {s['errors']}.",
        "",
        _paired_line(s["paired"]),
        "",
        f"Area-weighted RMSE and ACC by the WB2 rules, and the mean reward, on the {s['parsed']} "
        "items with a parsed answer, each baseline on the same items:",
        "",
        "| variable | lead h | forecast | n | RMSE | ACC | mean reward |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in s["table"]:
        acc = "n/a" if r["acc"] is None else f"{r['acc']:.3f}"
        lines.append(
            f"| {r['variable']} | {r['lead']} | {r['baseline']} | {r['n']} | "
            f"{r['rmse']:.3f} | {acc} | {r['reward']:.3f} |"
        )
    api = "the Batch API, at half price" if s["batch"] else "the standard API"
    lines += [
        "",
        "## Tokens and cost",
        "",
        f"{t['input']} input and {t['output']} output tokens, {t['reasoning']} of the output "
        f"reasoning; cache writes {t['cache_write']}, cache reads {t['cache_read']}. Sent "
        f"through {api}. At the prices in reports/spend.md (Anthropic's pricing page, fetched "
        f"2026-11-01): ${s['cost']:.4f}, or ${s['cost'] / n:.5f} an item.",
        "",
        "## Run config",
        "",
        f"- Generate settings: {s['generate_config']}; the rest are the provider's defaults "
        "(decision 0010).",
        f"- inspect_ai {s['inspect_ai']}; run from {s['started']} to {s['completed']}.",
        f"- Log `{s['log']}` (not in git).",
        "- Prompt, answer parser and reward: environments/era5_forecast_v1/era5_forecast_v1/"
        "contract.py at the commit above.",
        "",
        "## Limits",
        "",
        "- One reply per item, with no seed or temperature set, so a rerun gives other replies;",
        "  the run-to-run spread is not measured.",
    ]
    if s["parsed"] < n:
        lines.append(
            f"- The RMSE and ACC table covers the {s['parsed']} items with a parsed answer, "
            f"not all {n}."
        )
    lines += [
        "- The reward's baseline is the better of persistence and climatology for each item,",
        "  picked with the truth known, so items where one is nearly exact leave little to earn",
        "  (reports/era5/items_v1_baselines.md).",
        "- The items are 2020 ERA5 values, which are public; whether the model saw them in",
        "  training is UNKNOWN.",
        "- The cost uses the token counts in the log; the Anthropic Console's bill is not read.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Report a model run on era5-forecast-v1.")
    parser.add_argument("log_dir")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    logs = [read_eval_log(info) for info in list_eval_logs(args.log_dir)]
    if [x.status for x in logs] != ["success"]:
        raise SystemExit(f"want one successful log in {args.log_dir}")
    s = summarize(logs[0], records())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(s), "utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(s, indent=1, default=str), "utf-8")
    print(f"{s['n']} items, mean reward {s['reward']:.3f}, written to {args.out}")


if __name__ == "__main__":
    main()
