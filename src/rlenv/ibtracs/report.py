"""Report of a model run on ibtracs-storm-v1, next to the baselines of decision 0011.

uv run python -m rlenv.ibtracs.report <log dir> --out reports/ibtracs/<date>-<model>.md
"""

import argparse
import datetime as dt
import json
import re
import statistics
from pathlib import Path

from ibtracs_storm_v1 import contract
from ibtracs_storm_v1.taskset import records
from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log

from rlenv import ablation, results, spend
from rlenv.ibtracs import stats

TESTS = {  # what a question still tests when its careless reading is right anyway
    "ace": "summing the squares",
    "peak_category": "reading the Saffir-Simpson scale",
    "hurricane_hours": "counting the rows",
}


def _hours(rows: list) -> dict:
    """Two duration readings of the hours question: every HU row's status held until the next
    row, and the elapsed time of each spell of consecutive HU rows."""
    times = [dt.datetime.fromisoformat(r[0]) for r in rows]
    hu = [r[1] == "HU" for r in rows]
    gaps = zip(times, times[1:], hu, strict=False)
    holds = sum((later - t).total_seconds() / 3600 for t, later, h in gaps if h)
    spells, start = 0.0, None
    for i, h in enumerate([*hu, False]):
        if h and start is None:
            start = i
        elif not h and start is not None:
            spells += (times[i - 1] - times[start]).total_seconds() / 3600
            start = None
    return {
        "each row's status holds until the next row": round(holds),
        "elapsed time of each hurricane spell": round(spells),
    }


def careless(item: dict) -> dict:
    """The answer each careless reading of the item's rule gives (decision 0011)."""
    rows = item["rows"]
    synoptic = [r for r in rows if r[0][11:] in stats.SYNOPTIC]
    if item["question"] == "ace":
        every = sum(w * w for _, s, w, _ in rows if s in stats.NAMED and w >= 34)
        any_status = sum(w * w for _, _, w, _ in synoptic if w >= 34)
        no_ss = sum(w * w for _, s, w, _ in synoptic if s in ("TS", "HU") and w >= 34)
        return {
            "ACE over every row": round(every / 1e4, 1),
            "ACE ignoring status": round(any_status / 1e4, 1),
            "ACE from TS and HU only": round(no_ss / 1e4, 1),
        }
    if item["question"] == "peak_category":
        peak = max((w for _, s, w, _ in rows if s == "HU"), default=0)
        return {
            "category ignoring status": stats.scale(max(w for _, _, w, _ in rows)),
            "category from synoptic rows only": stats.scale(
                max((w for _, s, w, _ in synoptic if s == "HU"), default=0)
            ),
            "category by the mph thresholds": stats.scale(peak, stats.MPH),
        }
    return {"hours over every HU row": 6 * sum(r[1] == "HU" for r in rows)} | _hours(rows)


def names_storm(reply: str, meta: dict) -> bool:
    """Whether a reply names the storm or its season, words the prompt leaves out."""
    name, season = meta.get("name", ""), str(meta.get("season", ""))
    named = name not in ("", "UNNAMED", "NOT_NAMED") and re.search(
        rf"\b{re.escape(name)}\b", reply, re.I
    )
    return bool(named or (season and re.search(rf"\b{season}\b", reply)))


def best_constant(items: list[dict]) -> tuple[float, float]:
    """The single answer right on the most items of one question, and its accuracy."""
    question, keys = items[0]["question"], [i["key"] for i in items]
    candidates = sorted({round(k, 1) if question == "ace" else k for k in keys})

    def right(value: float) -> float:
        return sum(contract.reward(question, value, k) for k in keys)

    best = max(candidates, key=lambda v: (right(v), -v))
    return best, right(best) / len(keys)


def rows(log: EvalLog, items: list[dict] | None = None) -> list[dict]:
    """The run's per-item results (rlenv.results), with whether each reply names the storm or
    its season; items defaults to the bundled set."""
    by_id = {i["id"]: i for i in (records() if items is None else items)}
    out = []
    for s in log.samples or []:
        if s.metadata["key"] != by_id[s.id]["key"]:
            raise ValueError(f"{s.id}: the log's key differs from the item's")
        out.append(results.row(s) | {"recognized": names_storm(s.output.completion, s.metadata)})
    return out


def summarize(log: EvalLog, items: list[dict]) -> dict:
    """Accuracy per question with the baselines, the traps the misses fell into, tokens and
    cost of one run."""
    return from_results(results.header(log), rows(log, items), items)


def from_results(head: dict, rows: list[dict], items: list[dict]) -> dict:
    """The summary of a run from its per-item results, read from a log or from the committed
    file (rlenv.results)."""
    by_id = {i["id"]: i for i in items}
    batch = bool(head["settings"].get("batch"))
    answers, paid, item_costs = {}, {}, []
    parse_failures = errors = recognized = 0
    for r in rows:
        recognized += r["recognized"]
        item_costs.append(spend.cost(dict(zip(spend.KINDS, r["tokens"], strict=True)), batch))
        if r.get("error"):
            errors += 1
            answers[r["id"]], paid[r["id"]] = None, 0.0
            continue
        answers[r["id"]] = float(r["answer"]) if r["answer"] else None
        paid[r["id"]] = r["reward"]
        parse_failures += answers[r["id"]] is None
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
                "explained": sum(
                    any(
                        contract.reward(q, answers[i["id"]], careless(i)[name]) == 1.0
                        for name in names
                    )
                    for i in misses
                ),
            }
        )
    rewards = list(paid.values())
    t, settings = head["tokens"], head["settings"]
    return {
        "model": head["model"],
        "label": head["model"].split("/")[-1],
        "n": len(rewards),
        "ids": [r["id"] for r in rows],
        "parse_failures": parse_failures,
        "errors": errors,
        "rules": head["task_args"].get("rules", True),
        "recognized": recognized,
        "recognized_what": "name the storm or its season",
        "reward": statistics.fmean(rewards),
        "stderr": statistics.stdev(rewards) / len(rewards) ** 0.5 if len(rewards) > 1 else 0.0,
        "questions": questions,
        "tokens": t,
        "batch": batch,
        "cost": spend.cost(t, batch),
        "item_costs": item_costs,
        "commit": head["commit"],
        "generate_config": ", ".join(f"{k} {v}" for k, v in settings.items()) or "none",
        "inspect_ai": head["inspect_ai"],
        "started": head["started"],
        "completed": head["completed"],
        "log": head["log"],
    }


def render(s: dict) -> str:
    t, n = s["tokens"], s["n"]
    lines = [
        f"# ibtracs-storm-v1 on {s['label']}{'' if s['rules'] else ' (rules hidden)'}",
        "",
        f"Model `{s['model']}` on {n} items, scored by ibtracs_storm_v1/contract.py at commit "
        f"{s['commit']}"
        + ("." if s["rules"] else ", with each question's rule left out of the prompt."),
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
        f"- The prompt leaves out the name and year, yet {s['recognized']} of {n} replies name the "
        "storm or its season: a model can recognize a famous track.",
        "- North Atlantic storms from 1980 to 2025 only. "
        + (
            "The rules are in the prompt: this run is the control for the rules-hidden ablation."
            if s["rules"]
            else "Each rule is left out of the prompt; the rules-shown run is the control."
        ),
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


def render_pair(shown: dict, hidden: dict) -> str:
    """The rules-shown and rules-hidden runs side by side (the ablation in decision 0011)."""
    return ablation.render_pair(
        shown,
        hidden,
        "ibtracs-storm-v1",
        "rules hidden",
        "the rule left out (`-T rules=false`)",
        "hidden",
        "and, as an untested guess, one a policy would close as a constant offset rather than "
        "learn as a skill",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Report a model run on ibtracs-storm-v1.")
    parser.add_argument("log_dir")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--hidden", help="log dir of the rules-hidden run: write the pair")
    args = parser.parse_args()

    def one(path: str) -> dict:
        logs = [read_eval_log(info) for info in list_eval_logs(path)]
        if [x.status for x in logs] != ["success"]:
            raise SystemExit(f"want one successful log in {path}")
        return summarize(logs[0], records())

    s = one(args.log_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.hidden:
        args.out.write_text(render_pair(s, one(args.hidden)), "utf-8")
        print(f"pair report written to {args.out}")
        return
    args.out.write_text(render(s), "utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(s, indent=1, default=str), "utf-8")
    print(f"{s['n']} items, accuracy {s['reward']:.3f}, written to {args.out}")


if __name__ == "__main__":
    main()
