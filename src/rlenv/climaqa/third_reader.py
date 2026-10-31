"""Jev as a third reader of the ClimaQA miss sort (decision 0008).

uv run python -m rlenv.climaqa.third_reader   # needs TYPESAFE_API_KEY; stops before $0.10
"""

import argparse
import csv
import itertools
import json
import statistics
import urllib.request
from collections import Counter
from pathlib import Path

from rlenv.climaqa import expert_sheet, jev

RUNS = 5  # identical calls per item, for stability
LOG = Path("logs/2026-10-31-jev/responses.jsonl")  # raw responses, not in git
REVIEW = Path("reviews/phase-2-climaqa-port.md")
REPORT = Path("reports/climaqa/runs/2026-10-31-jev-third-reader.md")
FIRST_ESTIMATE = 2000  # input tokens assumed for the first call, before any usage is known
LABELS = {  # the miss notes' bucket names, as the item-level options Jev chooses from
    "mcq": {
        "model error": "key_right",
        "ambiguous": "ambiguous",
        "flawed": "flawed_item",
        "source only": "source_only",
    },
    "cloze": {
        "strictness": "same_answer",
        "other": "other_correct_word",
        "model error": "wrong_reply",
    },
}


def state(row: dict) -> dict:
    """The item and the model's answer as Jev sees them: no notes, flags or labels."""
    if row["task"] == "mcq":
        options = dict(line.split(") ", 1) for line in row["options"].splitlines())
        key, answer = row["key"][0], row["model_answer"][0]
        return {"question": row["question"], "options": options, "key": key, "model_answer": answer}
    return {"sentence": row["question"], "key": row["key"], "reply": row["model_answer"]}


def run(
    rows: list[dict],
    key: str,
    out: Path = LOG,
    opener=urllib.request.urlopen,
    budget: jev.Budget | None = None,
    runs: int = RUNS,
    first_estimate: int = FIRST_ESTIMATE,
) -> list[dict]:
    """RUNS identical requests per item, each raw response appended to `out` as it arrives;
    stops when the next call might cross the budget. Refuses an existing log, so a second
    launch cannot spend twice."""
    budget = budget or jev.Budget()
    if out.exists():
        raise FileExistsError(f"{out} exists; move it away before a new run")
    out.parent.mkdir(parents=True, exist_ok=True)
    records, seen = [], []
    with out.open("w", encoding="utf-8") as log:
        for row in rows:
            body = jev.request(row["task"], state(row))
            for k in range(1, runs + 1):
                if not budget.allows(max(seen) if seen else first_estimate):
                    return records
                payload, seconds = jev.call(body, key, opener=opener)
                seen.append(payload["usage"]["input_tokens"])
                budget.charge(seen[-1])
                record = {"id": row["id"], "task": row["task"], "run": k, "seconds": seconds}
                records.append(record | {"response": payload})
                log.write(json.dumps(records[-1]) + "\n")
                log.flush()
    return records


def _primary(bucket: str) -> str:
    return bucket.split(":")[0].split(",")[0].strip()


def mine() -> dict[str, str]:
    """The build session's bucket for each miss, from the two miss notes."""
    out = {}
    for task, path in expert_sheet.NOTES.items():
        for item, _, bucket, _ in expert_sheet.note_rows(path.read_text("utf-8"), task):
            out[item] = LABELS[task][_primary(bucket)]
    return out


def fable(review: Path = REVIEW) -> dict[str, str]:
    """Fable's blind sort of the 33 cloze misses, from the baseline review, section 3."""
    section = review.read_text("utf-8").split("### 3. Blind sort against the author's sort")[1]
    out = {}
    for line in section.split("\n### ")[0].splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split(" | ")]
        if len(cells) == 6 and cells[0].isdigit():
            out[f"gold/cloze/{cells[0]}"] = LABELS["cloze"][_primary(cells[4])]
    return out


def kappa(a: list[str], b: list[str]) -> float:
    """Cohen's kappa between two raters' labels for the same items."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    count_a, count_b = Counter(a), Counter(b)
    chance = sum(count_a[label] * count_b[label] for label in set(a) | set(b)) / n**2
    return 1.0 if chance == 1 else (observed - chance) / (1 - chance)


def brier(probabilities: dict[str, float], label: str) -> float:
    """Multi-class Brier score of one probability spread against the reference label."""
    return float(sum((p - (option == label)) ** 2 for option, p in probabilities.items()))


def stability(choices: list[str]) -> dict:
    """The modal choice over repeated calls, whether all agree, and pairwise agreement."""
    pairs = list(itertools.combinations(choices, 2))
    return {
        "modal": Counter(choices).most_common(1)[0][0],
        "all_same": len(set(choices)) == 1,
        "agreement": sum(x == y for x, y in pairs) / len(pairs),
    }


def _modal(choices: list[str], spreads: list[dict]) -> str:
    """The most frequent choice; a tie goes to the higher mean probability."""
    counts = Counter(choices)
    return max(counts, key=lambda o: (counts[o], sum(s.get(o, 0.0) for s in spreads)))


def analyse(
    records: list[dict],
    mine_labels: dict,
    fable_labels: dict,
    usd_per_input_token: float = jev.USD_PER_INPUT_TOKEN,
) -> dict:
    """Agreement, calibration, stability, cost and latency from the raw records."""
    by_item: dict[str, list[dict]] = {}
    for r in records:
        by_item.setdefault(r["id"], []).append(r["response"]["answers"]["bucket"])
    modal = {
        i: _modal([a["choice"] for a in answers], [a["probabilities"] for a in answers])
        for i, answers in by_item.items()
    }

    def against(reference: dict, labels: dict) -> tuple[float, int]:
        shared = [i for i in reference if i in labels]
        return kappa([labels[i] for i in shared], [reference[i] for i in shared]), len(shared)

    both = [i for i in fable_labels if mine_labels.get(i) == fable_labels[i] and i in by_item]
    briers = [
        sum(brier(a["probabilities"], fable_labels[i]) for a in by_item[i]) / len(by_item[i])
        for i in both
    ]
    stable = [stability([a["choice"] for a in answers]) for answers in by_item.values()]
    seconds = [r["seconds"] for r in records]
    tokens = sum(r["response"]["usage"]["input_tokens"] for r in records)
    out = {"modal": modal, "items": len(by_item), "runs": max(map(len, by_item.values()))}
    out |= dict(zip(("kappa_mine", "n_mine"), against(mine_labels, modal), strict=True))
    out |= dict(zip(("kappa_fable", "n_fable"), against(fable_labels, modal), strict=True))
    out |= dict(
        zip(("kappa_mine_fable", "n_mine_fable"), against(fable_labels, mine_labels), strict=True)
    )
    out |= {"brier": sum(briers) / len(briers) if briers else None, "brier_items": len(briers)}
    out |= {"all_same": sum(s["all_same"] for s in stable)}
    out |= {"agreement": sum(s["agreement"] for s in stable) / len(stable)}
    out |= {"calls": len(records), "input_tokens": tokens, "usd": tokens * usd_per_input_token}
    out |= {"median_seconds": statistics.median(seconds)}
    out |= {"p90_seconds": statistics.quantiles(seconds, n=10, method="inclusive")[-1]}
    out |= {"models": sorted({r["response"]["model"] for r in records})}
    out |= {"others": dict(Counter(modal[i] for i in modal if i not in mine_labels))}
    return out


def render(a: dict) -> str:
    brier_line = (
        f"Brier score where both sorts agree: {a['brier']:.3f} over {a['brier_items']} items "
        "(0 is perfect; 2 is a sure wrong answer)."
        if a["brier"] is not None
        else "Brier score: no item where both sorts agree."
    )
    lines = [
        "# Jev as a third reader of the ClimaQA misses",
        "",
        f"Model {', '.join(a['models'])} (requested as the pinned jev-1.14.0), one item per",
        f"request, {a['runs']} identical calls per item, {a['items']} items (decision 0008).",
        "",
        "| comparison | items | kappa |",
        "|---|---|---|",
        f"| Jev against the build session | {a['n_mine']} | {a['kappa_mine']:.3f} |",
        f"| Jev against Fable's blind sort | {a['n_fable']} | {a['kappa_fable']:.3f} |",
        f"| build session against Fable's blind sort | {a['n_mine_fable']} | "
        f"{a['kappa_mine_fable']:.3f} |",
        "",
        brier_line,
        "",
        f"Stability: all {a['runs']} calls chose the same bucket on {a['all_same']} of "
        f"{a['items']} items; mean pairwise agreement {a['agreement']:.3f}.",
        "",
        f"Cost: {a['calls']} calls, {a['input_tokens']} input tokens, ${a['usd']:.4f} "
        "(output tokens are free).",
        "",
        f"Latency per call: median {a['median_seconds']:.3f} s, p90 {a['p90_seconds']:.3f} s.",
        "",
        "Items outside the miss sort, by Jev's bucket: "
        + (", ".join(f"{k} {v}" for k, v in sorted(a["others"].items())) or "none")
        + ".",
    ]
    return "\n".join([*lines, ""])


def main() -> None:
    parser = argparse.ArgumentParser(description="Jev third reader: run the calls, then report.")
    parser.add_argument("step", choices=["run", "report"])
    if parser.parse_args().step == "run":
        rows = list(csv.DictReader(expert_sheet.SHEET.open(encoding="utf-8")))
        print(f"{len(run(rows, jev.load_key()))} calls logged to {LOG}")
        return
    records = [json.loads(line) for line in LOG.read_text("utf-8").splitlines()]
    REPORT.write_text(render(analyse(records, mine(), fable())), "utf-8")
    print(f"report written to {REPORT}")


if __name__ == "__main__":
    main()
