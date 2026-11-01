"""Inspect tasks for the clean ClimaQA set, scored by the same contract as the verifiers taskset.

uv run inspect eval src/earthgym/climaqa/tasks.py@climaqa_mcq --model <provider/model>
"""

import json
from pathlib import Path

from climaqa_v1 import contract
from climaqa_v1.taskset import near_matches, records
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState, generate


def samples(kind: str, path: str | None, strict: bool = False) -> MemoryDataset:
    """Items of one kind; the bundled clean set unless a JSONL path is given (tests). strict
    leaves out the near matches of Silver."""
    rows = (
        records() if path is None else [json.loads(x) for x in Path(path).read_text().splitlines()]
    )
    near = near_matches() if strict else set()
    out = []
    for row in rows:
        if row["task"] != kind or row["id"] in near:
            continue
        prompt = (
            contract.mcq_prompt(row["question"], row["options"])
            if kind == "mcq"
            else contract.cloze_prompt(row["question"])
        )
        meta = {"task": kind, "complexity": row["complexity"]}
        out.append(Sample(input=prompt, target=row["answer"], id=row["id"], metadata=meta))
    return MemoryDataset(out, name=f"climaqa_{kind}")


@scorer(metrics=[accuracy(), stderr()])
def contract_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        reply = state.output.completion
        if state.metadata["task"] == "mcq":
            ok, answer = contract.mcq_correct(reply, target.text), contract.mcq_choice(reply)
        else:
            ok, answer = contract.cloze_correct(reply, target.text), contract.normalize(reply)
        return Score(value=CORRECT if ok else INCORRECT, answer=answer or "")

    return score


@task
def climaqa_mcq(path: str | None = None, strict: bool = False) -> Task:
    return Task(dataset=samples("mcq", path, strict), solver=generate(), scorer=contract_scorer())


@task
def climaqa_cloze(path: str | None = None, strict: bool = False) -> Task:
    return Task(dataset=samples("cloze", path, strict), solver=generate(), scorer=contract_scorer())
