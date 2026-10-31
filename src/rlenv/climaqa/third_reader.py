"""Jev as a third reader of the ClimaQA miss sort (decision 0008).

uv run python -m rlenv.climaqa.third_reader   # needs TYPESAFE_API_KEY; stops before $0.10
"""

import itertools
import json
import urllib.request
from collections import Counter
from pathlib import Path

from rlenv.climaqa import expert_sheet, jev

RUNS = 5  # identical calls per item, for stability
LOG = Path("logs/2026-10-31-jev/responses.jsonl")  # raw responses, not in git
REVIEW = Path("reviews/phase-2-climaqa-port.md")
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
