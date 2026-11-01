"""Paired comparison of two models on clean ClimaQA v1, item by item, from their Inspect logs.

uv run python -m rlenv.climaqa.compare <log dir a> <log dir b> --out reports/climaqa/<name>.md
"""

import argparse
import json
from math import comb
from pathlib import Path

from climaqa_v1 import contract
from inspect_ai.log import list_eval_logs, read_eval_log
from inspect_ai.scorer import CORRECT


def mcnemar(b: int, c: int) -> float:
    """Exact two-sided McNemar test: the binomial test of the discordant pairs at one half."""
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2**n)


def outcomes(log) -> dict:
    """Per sample id: right or not, the answer given (lower case) and the complexity level."""
    out = {}
    for s in log.samples or []:
        score = next(iter(s.scores.values()))
        answer = (score.answer or "").strip().lower()
        out[s.id] = (score.value == CORRECT, answer, s.metadata.get("complexity") or "none")
    return out


def multiline(log) -> int:
    """Replies over more than one line."""
    return sum(len(s.output.completion.strip().splitlines()) > 1 for s in log.samples or [])


def format_misses(log) -> list:
    """Wrong cloze replies over more than one line whose last line alone would be right: the
    cloze prompt asks for only the missing word or phrase."""
    out = []
    for s in log.samples or []:
        lines = s.output.completion.strip().splitlines()
        wrong = next(iter(s.scores.values())).value != CORRECT
        if wrong and len(lines) > 1 and contract.cloze_correct(lines[-1], s.target):
            out.append(s.id)
    return sorted(out, key=str)


def compare(a, b) -> dict:
    """Paired counts, both accuracies, the exact McNemar p-value, and the items both models
    answered with the same wrong answer."""
    oa, ob = outcomes(a), outcomes(b)
    if set(oa) != set(ob):
        raise ValueError("the logs are not over the same items")
    ids = sorted(oa, key=str)
    right_a, right_b = [oa[i][0] for i in ids], [ob[i][0] for i in ids]
    pairs = list(zip(right_a, right_b, strict=True))
    only_a = sum(x and not y for x, y in pairs)
    only_b = sum(y and not x for x, y in pairs)
    same = [i for i in ids if not oa[i][0] and not ob[i][0] and oa[i][1] and oa[i][1] == ob[i][1]]
    return {
        "task": a.eval.task.split("/")[-1],
        "model_a": a.eval.model,
        "model_b": b.eval.model,
        "n": len(ids),
        "accuracy_a": sum(right_a) / len(ids),
        "accuracy_b": sum(right_b) / len(ids),
        "both_right": sum(x and y for x, y in pairs),
        "both_wrong": sum(not x and not y for x, y in pairs),
        "only_a": only_a,
        "only_b": only_b,
        "p": mcnemar(only_a, only_b),
        "same_wrong": same,
    } | (
        {
            "multiline_a": multiline(a),
            "multiline_b": multiline(b),
            "format_a": len(format_misses(a)),
            "format_b": len(format_misses(b)),
        }
        if a.eval.task.endswith("cloze")
        else {}
    )


def by_level(a, b) -> dict:
    """Per complexity level: n and each model's accuracy."""
    oa, ob = outcomes(a), outcomes(b)
    levels: dict[str, list[tuple[bool, bool]]] = {}
    for i, (right, _, level) in oa.items():
        levels.setdefault(level, []).append((right, ob[i][0]))
    return {
        level: (len(v), sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v))
        for level, v in sorted(levels.items())
    }


def render(rows: list[dict], levels: dict, dirs: tuple[str, str] = ("", "")) -> str:
    a, b = (rows[0]["model_a"], rows[0]["model_b"]) if rows else ("a", "b")
    lines = [
        f"# Clean ClimaQA v1: {b} against {a}",
        "",
        "Each item paired across the two runs. McNemar's exact test on the items only one model",
        "got right, two-sided.",
        "",
        f"| task | n | accuracy {a} | accuracy {b} | both right | both wrong | only {a} | "
        f"only {b} | McNemar p |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['task']} | {r['n']} | {r['accuracy_a']:.3f} | {r['accuracy_b']:.3f} | "
            f"{r['both_right']} | {r['both_wrong']} | {r['only_a']} | {r['only_b']} | "
            f"{r['p']:.3f} |"
        )
    lines += ["", "## Accuracy by complexity", "", f"| task | level | n | {a} | {b} |"]
    lines.append("|---|---|---|---|---|")
    for task, by in levels.items():
        lines += [f"| {task} | {lv} | {n} | {x:.3f} | {y:.3f} |" for lv, (n, x, y) in by.items()]
    lines += [
        "",
        "## Items both models got wrong with the same answer",
        "",
        "Candidates for a wrong key or a shared misconception; none is reviewed yet (decision",
        "0005's expert review).",
        "",
    ]
    for r in rows:
        k = len(r["same_wrong"])
        ids = ", ".join(str(i) for i in r["same_wrong"])
        lines.append(f"- {r['task']}: {k} item{'s' if k != 1 else ''} ({ids})")
    cloze = [r for r in rows if "format_a" in r]
    if cloze:
        lines += [
            "",
            "## Cloze replies that explain first",
            "",
            'The cloze prompt says "Reply with only the missing word or phrase." Replies over',
            "more than one line, and wrong replies whose last line alone is the key:",
            "",
            "| task | model | replies over one line | wrong, last line alone right |",
            "|---|---|---|---|",
        ]
        for r in cloze:
            lines.append(f"| {r['task']} | {a} | {r['multiline_a']} | {r['format_a']} |")
            lines.append(f"| {r['task']} | {b} | {r['multiline_b']} | {r['format_b']} |")
    lines += [
        "",
        "## Limits",
        "",
        "- One run per model, each with its provider's default settings, on different days.",
        "- The Gemini run cannot be repeated: no Vertex AI or Gemini calls from 2026-11-01",
        "  (decision 0010).",
        "- Cloze answers count as the same only when their normalized text matches exactly.",
    ]
    if any(dirs):
        lines.append(f"- Logs: `{dirs[0]}` and `{dirs[1]}` (not in git).")
    return "\n".join([*lines, ""])


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two models on clean ClimaQA v1.")
    parser.add_argument("a")
    parser.add_argument("b")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    def logs(path: str) -> dict:
        found = (read_eval_log(info) for info in list_eval_logs(path))
        return {x.eval.task.split("/")[-1]: x for x in found if x.status == "success"}

    la, lb = logs(args.a), logs(args.b)
    tasks = [t for t in sorted(la) if t in lb]
    rows = [compare(la[t], lb[t]) for t in tasks]
    levels = {t: by_level(la[t], lb[t]) for t in tasks}
    args.out.write_text(render(rows, levels, (args.a, args.b)), "utf-8")
    record = {"rows": rows, "levels": levels}
    args.out.with_suffix(".json").write_text(json.dumps(record, indent=1, default=str), "utf-8")
    print(f"{len(rows)} tasks compared, written to {args.out}")


if __name__ == "__main__":
    main()
