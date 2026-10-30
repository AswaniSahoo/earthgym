"""Inspect tasks for the clean ClimaQA set: multiple choice and cloze.

uv run inspect eval src/rlenv/climaqa/tasks.py@climaqa_mcq --model <provider/model>
"""

from inspect_ai import Task, task
from inspect_ai.dataset import FieldSpec, json_dataset
from inspect_ai.scorer import accuracy, choice, exact, stderr
from inspect_ai.solver import generate, multiple_choice, system_message

CLEAN_SET = "data/clean/climaqa_v0.jsonl"
SEED = 20261030
CLOZE_PROMPT = (
    "Fill in the <MASK> in the climate science statement. "
    "Reply with only the missing word or phrase."
)


def load(path: str, task_name: str, shuffle: bool):
    fields = FieldSpec(
        input="question",
        target="answer",
        choices="options",
        id="id",
        metadata=["task", "complexity"],
    )
    dataset = json_dataset(path, fields, shuffle_choices=SEED if shuffle else None)
    return dataset.filter(lambda sample: sample.metadata["task"] == task_name)


@task
def climaqa_mcq(path: str = CLEAN_SET, shuffle: bool = True) -> Task:
    return Task(dataset=load(path, "mcq", shuffle), solver=multiple_choice(), scorer=choice())


@task
def climaqa_cloze(path: str = CLEAN_SET) -> Task:
    return Task(
        dataset=load(path, "cloze", shuffle=False),
        solver=[system_message(CLOZE_PROMPT), generate()],
        scorer=exact(),
        metrics=[accuracy(), stderr()],  # same metric names as the MCQ task
    )
