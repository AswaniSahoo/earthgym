"""heat-basis-v1 as a verifiers v1 taskset: 300 heat policy questions with exact answers."""

import json
from importlib.resources import files

import verifiers.v1 as vf

from heat_basis_v1 import contract

DATA_FILE = "heat_basis_v1.jsonl"


def records() -> list[dict]:
    """The bundled items, one dict each; shared with the Inspect task."""
    lines = files("heat_basis_v1").joinpath(DATA_FILE).read_text("utf-8").splitlines()
    return [json.loads(line) for line in lines]


class HeatData(vf.TaskData):
    question: str
    key: int


class HeatTask(vf.Task[HeatData]):
    @vf.reward(weight=1.0)
    async def exact(self, trace: vf.Trace) -> float:
        return contract.reward(contract.answer(trace.last_reply), self.data.key)


class HeatConfig(vf.TasksetConfig):
    questions: list[str] = list(contract.QUESTIONS)


class HeatTaskset(vf.Taskset[HeatTask, HeatConfig]):
    def load(self) -> list[HeatTask]:
        return [
            HeatTask(to_data(row), self.config.task)
            for row in records()
            if row["question"] in self.config.questions
        ]


def to_data(row: dict) -> HeatData:
    return HeatData(
        id=row["id"], prompt=contract.prompt(row), question=row["question"], key=row["key"]
    )
