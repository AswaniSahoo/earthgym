"""ClimaQA clean set v1 as a verifiers v1 taskset: MCQ and cloze with exact rewards."""

import json
from importlib.resources import files

import verifiers.v1 as vf

from climaqa_v1 import contract

DATA_FILE = "climaqa_clean_v1.jsonl"


def records() -> list[dict]:
    """The bundled clean set, one dict per item; shared with the Inspect tasks."""
    lines = files("climaqa_v1").joinpath(DATA_FILE).read_text("utf-8").splitlines()
    return [json.loads(line) for line in lines]


class ClimaqaData(vf.TaskData):
    kind: str
    question: str
    answer: str
    key_text: str


class ClimaqaTask(vf.Task[ClimaqaData]):
    @vf.reward(weight=1.0)
    async def correct(self, trace: vf.Trace) -> float:
        reply, key = trace.last_reply, self.data.answer
        ok = (
            contract.mcq_correct(reply, key)
            if self.data.kind == "mcq"
            else contract.cloze_correct(reply, key)
        )
        return float(ok)


class ClimaqaConfig(vf.TasksetConfig):
    kinds: list[str] = ["mcq", "cloze"]


class ClimaqaTaskset(vf.Taskset[ClimaqaTask, ClimaqaConfig]):
    def load(self) -> list[ClimaqaTask]:
        return [
            ClimaqaTask(to_data(row), self.config.task)
            for row in records()
            if row["task"] in self.config.kinds
        ]


def to_data(row: dict) -> ClimaqaData:
    if row["task"] == "cloze":
        return ClimaqaData(
            id=row["id"],
            prompt=contract.cloze_prompt(row["question"]),
            kind="cloze",
            question=row["question"],
            answer=row["answer"],
            key_text=row["answer"],
        )
    options = row["options"]  # shuffled once, per item id, by rlenv.climaqa.clean
    return ClimaqaData(
        id=row["id"],
        prompt=contract.mcq_prompt(row["question"], options),
        kind="mcq",
        question=row["question"],
        answer=row["answer"],
        key_text=options[contract.LETTERS.index(row["answer"])],
    )
