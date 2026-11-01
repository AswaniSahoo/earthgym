"""Report of a model run on heat-basis-v1, next to the baselines of decision 0013.

uv run python -m rlenv.heat.report <log dir> --out reports/heat/<date>-<model>.md
"""

import argparse
import json
import re
import statistics
from pathlib import Path

from heat_basis_v1 import contract
from heat_basis_v1.taskset import records
from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log

from rlenv import ablation, spend

MISSING = ("missing days skipped", "missing index days left out")  # the missing-value rules
YEAR = re.compile(r"\b20(1[5-9]|2[0-4])\b")  # a season the prompt leaves out
TESTS = {  # what a question still tests when its careless reading is right anyway
    "trigger_days": "counting the hot days",
    "events": "finding the runs",
    "missed_days": "comparing the two columns",
}


def _runs(hot: list[bool]) -> list[int]:
    """Lengths of the runs of True."""
    out, run = [], 0
    for h in [*hot, False]:
        if h:
            run += 1
        elif run:
            out.append(run)
            run = 0
    return out


def careless(item: dict) -> dict:
    """The answer each careless reading of the item's rule gives (decision 0013). An
    independent re-implementation in whole degrees, from the prompt's columns, as a check on
    the keys' code."""
    f, k = item["threshold"], item["k"]
    index, site = item["index_f"], item["site_f"]

    def hot(v):
        return v is not None and v >= f

    if item["question"] == "trigger_days":
        return {
            "above, not at, the threshold": sum(v is not None and v > f for v in index),
            "the site's column": sum(hot(v) for v in site),
        }
    if item["question"] == "events":
        runs = _runs([hot(v) for v in index])
        return {
            "trigger days, not events": sum(hot(v) for v in index),
            "every run, whatever its length": len(runs),
            "missing days skipped": sum(
                r >= k for r in _runs([hot(v) for v in index if v is not None])
            ),
            "blocks of k days": sum(r // k for r in runs),
            "runs longer than k": sum(r > k for r in runs),
            "runs of exactly k": sum(r == k for r in runs),
        }
    pairs = list(zip(index, site, strict=True))
    missed = sum(hot(s) and not hot(i) for i, s in pairs)
    return {
        "both ways": missed + sum(hot(i) and s is not None and not hot(s) for i, s in pairs),
        "every hot site day": sum(hot(s) for _, s in pairs),
        "missing index days left out": sum(
            hot(s) and i is not None and not hot(i) for i, s in pairs
        ),
        "site strictly above the threshold": sum(
            s is not None and s > f and not hot(i) for i, s in pairs
        ),
        "the other way round": sum(hot(i) and s is not None and not hot(s) for i, s in pairs),
    }


def _gap_days(item: dict) -> int:
    """Hot site days with no index value: what a missed-days answer turns on when the
    missing-index rule is read the other way."""
    f = item["threshold"]
    pairs = zip(item["index_f"], item["site_f"], strict=True)
    return sum(i is None and s is not None and s >= f for i, s in pairs)


def _where(group: list[dict], names: list[str]) -> dict:
    """For the missing-value readings: the stations and seasons where they change a key."""
    out = {}
    for name in (n for n in names if n in MISSING):
        places: dict[str, int] = {}
        for i in group:
            if careless(i)[name] != i["key"]:
                place = f"{i['index_name']} {i['year']}"
                places[place] = places.get(place, 0) + 1
        if places:
            out[name] = places
    return out


def _places(places: dict) -> str:
    return ", ".join(f"{p} ({c})" for p, c in sorted(places.items(), key=lambda x: -x[1]))


def best_constant(items: list[dict]) -> tuple[float, float]:
    """The single answer right on the most items of one question, and its accuracy."""
    keys = [i["key"] for i in items]
    best = max(sorted(set(keys)), key=lambda v: (keys.count(v), -v))
    return best, keys.count(best) / len(keys)


def summarize(log: EvalLog, items: list[dict]) -> dict:
    """Accuracy per question with the baselines, the traps the misses fell into, tokens and
    cost of one run."""
    by_id = {i["id"]: i for i in items}
    config = log.eval.model_generate_config.merge(log.plan.config)
    batch = bool(config.batch)
    answers, paid, item_costs = {}, {}, []
    parse_failures = errors = recognized = 0
    for s in log.samples or []:
        if s.metadata["key"] != by_id[s.id]["key"]:
            raise ValueError(f"{s.id}: the log's key differs from the item's")
        recognized += bool(YEAR.search(s.output.completion))
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
                        contract.reward(careless(i)[name], i["key"]) for i in group
                    )
                    for name in names
                },
                "traps": {
                    name: sum(answers[i["id"]] == careless(i)[name] for i in misses)
                    for name in names
                },
                "explained": sum(
                    any(answers[i["id"]] == careless(i)[name] for name in names) for i in misses
                ),
                "matched": {
                    name: ids
                    for name in names
                    if (ids := [i["id"] for i in misses if answers[i["id"]] == careless(i)[name]])
                },
                "off_by_one": sum(abs(answers[i["id"]] - i["key"]) == 1 for i in misses),
                "gap_days": sum(
                    0 < _gap_days(i) == abs(answers[i["id"]] - i["key"]) for i in misses
                ),
                "where": _where(group, names),
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
        "ids": [s.id for s in log.samples or []],
        "parse_failures": parse_failures,
        "rules": log.eval.task_args.get("rules", True),
        "recognized": recognized,
        "recognized_what": "name a season from 2015 to 2024",
        "errors": errors,
        "reward": statistics.fmean(rewards),
        "stderr": statistics.stdev(rewards) / len(rewards) ** 0.5 if len(rewards) > 1 else 0.0,
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
        f"# heat-basis-v1 on {s['label']}{'' if s['rules'] else ' (terms only)'}",
        "",
        f"Model `{s['model']}` on {n} items, scored by heat_basis_v1/contract.py at commit "
        f"{s['commit']}" + ("." if s["rules"] else ", with the policy terms alone in the prompt."),
        "",
        "## Result",
        "",
        f"Accuracy {s['reward']:.3f} (stderr {s['stderr']:.3f}) over all {n} items, parse "
        "failures and errors scored 0. Each answer is right or wrong against the exact key "
        "(decision 0013).",
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
    wrong = sum(round((1 - r["accuracy"]) * r["n"]) for r in s["questions"]) - s["parse_failures"]
    lines += [
        "",
        f"Matches are by value. Misses off by exactly one: "
        f"{sum(r['off_by_one'] for r in s['questions'])} of {wrong}; missed-days misses off by "
        "the number of hot site days with no index value: "
        f"{sum(r['gap_days'] for r in s['questions'] if r['question'] == 'missed_days')}.",
    ]
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
        "- Prompt, rules, answer parser and reward: environments/heat_basis_v1/"
        "heat_basis_v1/contract.py at the commit above.",
        "",
        "## Limits",
        "",
        "- One reply per item, with no seed or temperature set, so a rerun gives other replies;",
        "  the run-to-run spread is not measured.",
        f"- The prompt leaves out the year, and {s['recognized']} of {n} replies name a season "
        "from 2015 to 2024.",
        "- The missed-days question asks the policyholder's side of basis risk only: days the",
        "  index paid while the site was not hot are not asked.",
        "- Four Phoenix-area stations, seasons 2015 to 2024. "
        + (
            "The rules are in the prompt: this run is the control for the terms-only ablation."
            if s["rules"]
            else "The prompt gives the policy terms alone; the rules-shown run is the control."
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
                    f"items, so on these seasons the question mostly tests {TESTS[r['question']]}, "
                    "not the rule's choice of days (decision 0013)."
                )
    for r in s["questions"]:
        lines += [
            f"- '{name}' gives another answer than the key on {sum(places.values())} of "
            f"{r['n']} {r['question']} items: {_places(places)}."
            for name, places in r["where"].items()
        ]
    return "\n".join([*lines, ""])


def render_pair(shown: dict, hidden: dict) -> str:
    """The rules-shown and terms-only runs side by side (the ablation in decision 0013)."""
    flag = "the policy terms alone (`-T rules=false`)"
    clause = (
        "and, as an untested guess, one a policy would take from the reward in a few steps "
        "rather than learn as a skill"
    )
    text = ablation.render_pair(
        shown, hidden, "heat-basis-v1", "terms only", flag, "with terms only", clause
    )
    where = [
        f"Where '{name}' gives another answer than the key ({r['question']}): {_places(places)}."
        for r in hidden["questions"]
        for name, places in r.get("where", {}).items()
    ]
    return text + "".join(f"\n{line}\n" for line in where)


def main() -> None:
    parser = argparse.ArgumentParser(description="Report a model run on heat-basis-v1.")
    parser.add_argument("log_dir")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--hidden", help="log dir of the terms-only run: write the pair")
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
