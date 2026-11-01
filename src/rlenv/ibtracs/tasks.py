"""Inspect task for ibtracs-storm-v1, rewarded by the same contract as the verifiers taskset.

uv run inspect eval src/rlenv/ibtracs/tasks.py@ibtracs_storm --model <provider/model>
uv run python -m rlenv.ibtracs.tasks   # probe ids for --sample-id, 2 per question
"""

import json
from collections import Counter
from pathlib import Path

from ibtracs_storm_v1 import contract
from ibtracs_storm_v1.taskset import records
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import Score, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState, generate

HIDDEN = ("question", "key", "sid", "season", "name")


def samples(path: str | None) -> MemoryDataset:
    """The bundled items unless a JSONL path is given (tests)."""
    rows = (
        records() if path is None else [json.loads(x) for x in Path(path).read_text().splitlines()]
    )
    out = [
        Sample(
            input=contract.prompt(row),
            target=str(row["key"]),
            id=row["id"],
            metadata={k: row[k] for k in HIDDEN},
        )
        for row in rows
    ]
    return MemoryDataset(out, name="ibtracs_storm")


def probe_ids(rows: list[dict] | None = None, n: int = 2) -> list[str]:
    """The first n item ids of each question, in item order: a balanced probe."""
    taken: Counter = Counter()
    out = []
    for row in records() if rows is None else rows:
        if taken[row["question"]] < n:
            taken[row["question"]] += 1
            out.append(row["id"])
    return out


@scorer(metrics=[mean(), stderr()])
def storm_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        m = state.metadata
        value = contract.answer(state.output.completion)
        return Score(
            value=contract.reward(m["question"], value, m["key"]),
            answer="" if value is None else str(value),
        )

    return score


@task
def ibtracs_storm(path: str | None = None) -> Task:
    return Task(dataset=samples(path), solver=generate(), scorer=storm_scorer())


if __name__ == "__main__":
    print(",".join(probe_ids()))
