"""heat-basis-v1 as a verifiers v1 taskset: 300 heat policy questions with exact answers."""

import json
from importlib.resources import files
from types import SimpleNamespace
from typing import Literal

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

    async def validate(self, runtime) -> bool:
        """The gold check: the reference reply, through this task's own reward, scores 1.0
        (decision 0021)."""
        return await self.exact(SimpleNamespace(last_reply=contract.gold(self.data.key))) == 1.0


class HeatConfig(vf.TasksetConfig):
    questions: list[str] = list(contract.QUESTIONS)
    rules: bool = True  # False: the terms-only ablation
    split: Literal["train", "test"] | None = None  # held out by group (decision 0017)


class HeatTaskset(vf.Taskset[HeatTask, HeatConfig]):
    def load(self) -> list[HeatTask]:
        return [
            HeatTask(to_data(row, self.config.rules), self.config.task)
            for row in records()
            if row["question"] in self.config.questions
            and self.config.split in (None, contract.split(row))
        ]


def to_data(row: dict, rules: bool = True) -> HeatData:
    return HeatData(
        id=row["id"],
        prompt=contract.prompt(row, rules),
        question=row["question"],
        key=row["key"],
    )
