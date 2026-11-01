"""Report of a model run on ibtracs-storm-v1, next to the baselines of decision 0011.

uv run python -m rlenv.ibtracs.report <log dir> --out reports/ibtracs/<date>-<model>.md
"""

import argparse
import json
import statistics
from pathlib import Path

from ibtracs_storm_v1 import contract
from ibtracs_storm_v1.taskset import records
from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log

from rlenv import spend
from rlenv.ibtracs import stats

TESTS = {  # what a question still tests when its careless reading is right anyway
    "ace": "summing the squares",
    "peak_category": "reading the Saffir-Simpson scale",
    "hurricane_hours": "counting the rows",
}


def _category(knots: int) -> int:
    return next((c for k, c in stats.CATEGORIES if knots >= k), 0)


def careless(item: dict) -> dict:
    """The answer each careless reading of the item's rule gives (decision 0011)."""
    rows = item["rows"]
    synoptic = [r for r in rows if r[0][11:] in stats.SYNOPTIC]
    if item["question"] == "ace":
        every = sum(w * w for _, s, w, _ in rows if s in stats.NAMED and w >= 34)
        any_status = sum(w * w for _, _, w, _ in synoptic if w >= 34)
        return {
            "ACE over every row": round(every / 1e4, 1),
            "ACE ignoring status": round(any_status / 1e4, 1),
        }
    if item["question"] == "peak_category":
        return {
            "category ignoring status": _category(max(w for _, _, w, _ in rows)),
            "category from synoptic rows only": _category(
                max((w for _, s, w, _ in synoptic if s == "HU"), default=0)
            ),
        }
    return {"hours over every HU row": 6 * sum(s == "HU" for _, s, _, _ in rows)}


def best_constant(items: list[dict]) -> tuple[float, float]:
    """The single answer right on the most items of one question, and its accuracy."""
    question, keys = items[0]["question"], [i["key"] for i in items]
    candidates = sorted({round(k, 1) if question == "ace" else k for k in keys})

    def right(value: float) -> float:
        return sum(contract.reward(question, value, k) for k in keys)

    best = max(candidates, key=lambda v: (right(v), -v))
    return best, right(best) / len(keys)


def summarize(log: EvalLog, items: list[dict]) -> dict:
    """Accuracy per question with the baselines, the traps the misses fell into, tokens and
    cost of one run."""
    by_id = {i["id"]: i for i in items}
    config = log.eval.model_generate_config.merge(log.plan.config)
    batch = bool(config.batch)
    answers, paid, item_costs = {}, {}, []
    parse_failures = errors = 0
    for s in log.samples or []:
        if s.metadata["key"] != by_id[s.id]["key"]:
            raise ValueError(f"{s.id}: the log's key differs from the item's")
        item_costs.append(spend.cost(spend.count([s.model_usage]), batch))
        if s.error or not s.scores:
            errors += 1
            answers[s.id], paid[s.id] = None, 0.0
            continue
        score = next(iter(s.scores.values()))
        answers[s.id] = float(score.answer) if score.answer else None
        paid[s.id] = float(score.value)
        parse_failures += answers[s.id] is None
    questions = []
    for q in contract.QUESTIONS:
        group = [by_id[i] for i in paid if by_id[i]["question"] == q]
        if not group:
            continue
        names = list(careless(group[0]))
        misses = [i for i in group if paid[i["id"]] == 0 and answers[i["id"]] is not None]
        questions.append(
            {"question": q, "n": len(group)}
            | {"accuracy": statistics.fmean(paid[i["id"]] for i in group)}
            | {"best_constant": best_constant(group)}
            | {
                "baselines": {
                    name: statistics.fmean(
                        contract.reward(q, careless(i)[name], i["key"]) for i in group
                    )
                    for name in names
                },
                "traps": {
                    name: sum(
                        contract.reward(q, answers[i["id"]], careless(i)[name]) == 1.0
                        for i in misses
                    )
                    for name in names
                },
            }
        )
    rewards = list(paid.values())
    t = spend.tokens([log])
    rev = log.eval.revision
    settings = config.model_dump(exclude_none=True)
    return {
        "model": log.eval.model,
        "label": log.eval.model.split("/")[-1],
        "n": len(rewards),
        "parse_failures": parse_failures,
        "errors": errors,
        "reward": statistics.fmean(rewards),
        "stderr": statistics.stdev(rewards) / len(rewards) ** 0.5,
        "questions": questions,
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


def render(s: dict) -> str:
    t, n = s["tokens"], s["n"]
    lines = [
        f"# ibtracs-storm-v1 on {s['label']}",
        "",
        f"Model `{s['model']}` on {n} items, scored by ibtracs_storm_v1/contract.py at commit "
        f"{s['commit']}.",
        "",
        "## Result",
        "",
        f"Accuracy {s['reward']:.3f} (stderr {s['stderr']:.3f}) over all {n} items, parse "
        "failures and errors scored 0. Each answer is right or wrong against the exact key "
        "(decision 0011).",
        "",
        f"Replies without a parseable answer line: {s['parse_failures']} of {n}. Samples that "
        f"errored: {s['errors']}.",
        "",
        "Accuracy per question, with the best constant answer and each careless reading of the "
        "rule as baselines:",
        "",
        "| question | answer by | n | accuracy |",
        "|---|---|---|---|",
    ]
    for r in s["questions"]:
        q, k = r["question"], r["n"]
        value, constant = r["best_constant"]
        lines.append(f"| {q} | model | {k} | {r['accuracy']:.3f} |")
        lines.append(f"| {q} | best constant ({value:g}) | {k} | {constant:.3f} |")
        lines += [f"| {q} | {name} | {k} | {acc:.3f} |" for name, acc in r["baselines"].items()]
    lines += [
        "",
        "Wrong answers by the model that equal a careless reading of the rule:",
        "",
        "| question | careless reading | model misses that match |",
        "|---|---|---|",
    ]
    for r in s["questions"]:
        lines += [f"| {r['question']} | {name} | {c} |" for name, c in r["traps"].items()]
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
        "- Prompt, rules, answer parser and reward: environments/ibtracs_storm_v1/"
        "ibtracs_storm_v1/contract.py at the commit above.",
        "",
        "## Limits",
        "",
        "- One reply per item, with no seed or temperature set, so a rerun gives other replies;",
        "  the run-to-run spread is not measured.",
        "- The prompt leaves out the name and year, but a model can still recognize a famous",
        "  track; whether any answer was recalled rather than counted is UNKNOWN.",
        "- North Atlantic storms from 1980 to 2025 only, with the rules in the prompt; the",
        "  rules-hidden ablation is not run here.",
        "- The cost uses the token counts in the log; the Anthropic Console's bill is not read.",
    ]
    for r in s[
        "questions"
    ]:  # a careless reading that is mostly right shows a trap that rarely bites
        for name, acc in r["baselines"].items():
            if acc >= 0.9:
                lines.append(
                    f"- {r['question']}: '{name}' is right on {round(acc * r['n'])} of {r['n']} "
                    f"items, so on these storms the question mostly tests {TESTS[r['question']]}, "
                    "not the rule's choice of rows (decision 0011)."
                )
    return "\n".join([*lines, ""])


def main() -> None:
    parser = argparse.ArgumentParser(description="Report a model run on ibtracs-storm-v1.")
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
    print(f"{s['n']} items, accuracy {s['reward']:.3f}, written to {args.out}")


if __name__ == "__main__":
    main()
