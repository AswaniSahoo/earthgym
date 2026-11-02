"""ibtracs-storm-v1 as a verifiers v1 taskset: 300 per-storm questions with exact answers, and a
tools mode in which the model reads the storm's rows through one SQL tool (decision 0023)."""

import json
from importlib.resources import files
from types import SimpleNamespace
from typing import Literal

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
    rows: list[tuple[str, str, int, int | None]] | None = None  # tools mode: what query reads


class TrackToolset(vf.Toolset[vf.ToolsetConfig]):
    """The query tool over one storm's rows. In tools mode verifiers starts one server per
    rollout, as `python -m ibtracs_storm_v1.taskset`, and hands it that rollout's task data."""

    TOOL_PREFIX = None  # the model sees the tool as `query`, as in the Inspect task

    async def setup_task(self, task: StormData) -> None:
        self.db = contract.database(task.rows)

    @vf.tool
    def query(self, sql: str) -> str:
        """Run one SQLite SELECT statement on the table track and return its result as text."""
        return contract.query(self.db, sql)


class StormTaskConfig(vf.TaskConfig):
    tools: bool = False  # copied from StormConfig.tools: Task.toolsets sees only this config


class StormTask(vf.Task[StormData, vf.State, StormTaskConfig]):
    @classmethod
    def toolsets(cls, config: StormTaskConfig) -> list[vf.Toolset]:
        return [TrackToolset(vf.ToolsetConfig())] if config.tools else []

    @vf.reward(weight=1.0)
    async def exact(self, trace: vf.Trace) -> float:
        d = self.data
        return contract.reward(d.question, contract.answer(trace.last_reply), d.key)

    async def validate(self, runtime) -> bool:
        """The gold check: the reference reply, through this task's own reward, scores 1.0
        (decision 0021)."""
        return (
            await self.exact(
                SimpleNamespace(last_reply=contract.gold(self.data.question, self.data.key))
            )
            == 1.0
        )


class StormConfig(vf.TasksetConfig):
    task: StormTaskConfig = StormTaskConfig()
    questions: list[str] = list(contract.QUESTIONS)
    rules: bool = True  # False: the rules-hidden ablation
    tools: bool = False  # True: no row and no rule in the prompt; the query tool reads the rows
    split: Literal["train", "test"] | None = None  # held out by group (decision 0017)

    def model_post_init(self, context, /) -> None:
        super().model_post_init(context)
        self.task = self.task.model_copy(update={"tools": self.tools})


class StormTaskset(vf.Taskset[StormTask, StormConfig]):
    def load(self) -> list[StormTask]:
        c = self.config
        return [
            StormTask(to_data(row, c.rules, c.tools), c.task)
            for row in records()
            if row["question"] in c.questions and c.split in (None, contract.split(row))
        ]


def to_data(row: dict, rules: bool = True, tools: bool = False) -> StormData:
    return StormData(
        id=row["id"],
        prompt=contract.tools_prompt(row) if tools else contract.prompt(row, rules),
        question=row["question"],
        key=row["key"],
        rows=row["rows"] if tools else None,
    )


if __name__ == "__main__":  # how verifiers starts the tool server (verifiers/v1/mcp/launch.py)
    TrackToolset.run()
