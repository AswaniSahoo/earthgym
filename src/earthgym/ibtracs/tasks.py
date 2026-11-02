"""Inspect task for ibtracs-storm-v1, rewarded by the same contract as the verifiers taskset.

uv run inspect eval src/earthgym/ibtracs/tasks.py@ibtracs_storm --model <provider/model>
uv run python -m earthgym.ibtracs.tasks   # probe ids for --sample-id, 2 per question
"""

import json
from collections import Counter
from contextlib import closing
from pathlib import Path

from ibtracs_storm_v1 import contract
from ibtracs_storm_v1.taskset import records
from inspect_ai import Task, task
from inspect_ai.agent import AgentSubmit, react
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import Score, Target, mean, scorer, stderr
from inspect_ai.solver import Generate, Solver, TaskState, generate, solver
from inspect_ai.tool import Tool, tool
from inspect_ai.util import store

HIDDEN = ("question", "key", "sid", "season", "name")
MESSAGE_LIMIT = 30  # tools mode: the prompts, 13 queries and the submit, each call 2 messages


def samples(path: str | None, rules: bool = True, tools: bool = False) -> MemoryDataset:
    """The bundled items unless a JSONL path is given (tests). In tools mode the rows leave the
    prompt for the metadata, from where the setup puts them in the store."""
    rows = (
        records() if path is None else [json.loads(x) for x in Path(path).read_text().splitlines()]
    )
    out = [
        Sample(
            input=contract.tools_prompt(row) if tools else contract.prompt(row, rules),
            target=str(row["key"]),
            id=row["id"],
            metadata={k: row[k] for k in HIDDEN + (("rows",) if tools else ())},
        )
        for row in rows
    ]
    return MemoryDataset(out, name="ibtracs_storm")


@solver
def rows_to_store() -> Solver:
    """Tools mode: put the storm's rows in the sample's store, where the query tool reads them."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.store.set("rows", state.metadata["rows"])
        return state

    return solve


@tool
def query() -> Tool:
    async def execute(sql: str) -> str:
        """Run one SQLite SELECT statement on the table track and return its result as text.

        Args:
            sql: One SQLite SELECT statement.
        """
        with closing(contract.database(store().get("rows"))) as db:
            return contract.query(db, sql)

    return execute


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
def storm_scorer(tools: bool = False):
    """The contract's reward; in tools mode a final answer may also be the number alone."""
    parse = contract.final_answer if tools else contract.answer

    async def score(state: TaskState, target: Target) -> Score:
        m = state.metadata
        value = parse(state.output.completion)
        return Score(
            value=contract.reward(m["question"], value, m["key"]),
            answer="" if value is None else str(value),
        )

    return score


@task
def ibtracs_storm(path: str | None = None, rules: bool = True, tools: bool = False) -> Task:
    """rules=False (`-T rules=false`) leaves the rule out of every prompt: the ablation.
    tools=True (`-T tools=true`) leaves the rows and the rule out, whatever `rules` says: the
    model reads the rows with the query tool and submits its answer (decision 0023)."""
    if not tools:
        return Task(dataset=samples(path, rules), solver=generate(), scorer=storm_scorer())
    return Task(
        dataset=samples(path, tools=True),
        setup=rows_to_store(),
        solver=react(tools=[query()], submit=AgentSubmit(answer_only=True), attempts=1),
        scorer=storm_scorer(tools=True),
        message_limit=MESSAGE_LIMIT,
    )


if __name__ == "__main__":
    print(",".join(probe_ids()))
