"""ibtracs-storm-v1 as a verifiers v1 taskset: 300 per-storm questions with exact answers."""

import json
from importlib.resources import files

import verifiers.v1 as vf

from ibtracs_storm_v1 import contract

DATA_FILE = "ibtracs_storm_v1.jsonl"


def records() -> list[dict]:
    """The bundled items, one dict each; shared with the Inspect task."""
    lines = files("ibtracs_storm_v1").joinpath(DATA_FILE).read_text("utf-8").splitlines()
    return [json.loads(line) for line in lines]


class StormData(vf.TaskData):
    question: str
    key: float


class StormTask(vf.Task[StormData]):
    @vf.reward(weight=1.0)
    async def exact(self, trace: vf.Trace) -> float:
        d = self.data
        return contract.reward(d.question, contract.answer(trace.last_reply), d.key)


class StormConfig(vf.TasksetConfig):
    questions: list[str] = list(contract.QUESTIONS)
    rules: bool = True  # False: the rules-hidden ablation


class StormTaskset(vf.Taskset[StormTask, StormConfig]):
    def load(self) -> list[StormTask]:
        return [
            StormTask(to_data(row, self.config.rules), self.config.task)
            for row in records()
            if row["question"] in self.config.questions
        ]


def to_data(row: dict, rules: bool = True) -> StormData:
    return StormData(
        id=row["id"],
        prompt=contract.prompt(row, rules),
        question=row["question"],
        key=row["key"],
    )
