"""Inspect task for era5-forecast-v1, rewarded by the same contract as the verifiers taskset.

uv run inspect eval src/rlenv/era5/tasks.py@era5_forecast --model <provider/model>
uv run python -m rlenv.era5.tasks   # probe ids for --sample-id, 2 per variable and lead
"""

import json
from collections import Counter
from pathlib import Path

from era5_forecast_v1 import contract
from era5_forecast_v1.taskset import records
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import Score, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState, generate

HIDDEN = ("variable", "truth", "climatology", "floor", "hres", "area_weight", "lead_hours")


def samples(path: str | None) -> MemoryDataset:
    """The bundled items unless a JSONL path is given (tests)."""
    rows = (
        records() if path is None else [json.loads(x) for x in Path(path).read_text().splitlines()]
    )
    out = []
    for row in rows:
        meta = {key: row[key] for key in HIDDEN} | {"persistence": row["history"][-1]}
        prompt, truth = contract.prompt(row), str(row["truth"])
        out.append(Sample(input=prompt, target=truth, id=row["id"], metadata=meta))
    return MemoryDataset(out, name="era5_forecast")


def probe_ids(rows: list[dict] | None = None, n: int = 2) -> list[str]:
    """The first n item ids of each variable and lead, in item order: a balanced probe."""
    taken: Counter = Counter()
    out = []
    for row in records() if rows is None else rows:
        group = (row["variable"], row["lead_hours"])
        if taken[group] < n:
            taken[group] += 1
            out.append(row["id"])
    return out


@scorer(metrics=[mean(), stderr()])
def forecast_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        m = state.metadata
        forecast = contract.answer(state.output.completion)
        value = contract.reward(
            forecast, m["truth"], m["persistence"], m["climatology"], m["floor"]
        )
        return Score(value=value, answer="" if forecast is None else str(forecast))

    return score


@task
def era5_forecast(path: str | None = None) -> Task:
    return Task(dataset=samples(path), solver=generate(), scorer=forecast_scorer())


if __name__ == "__main__":
    print(",".join(probe_ids()))
