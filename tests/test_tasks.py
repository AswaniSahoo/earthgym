import json

from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from rlenv.climaqa import tasks

RECORDS = [
    {
        "id": "gold/mcq/0",
        "task": "mcq",
        "question": "Why does convection start?",
        "options": ["Warm air rises.", "Cold air rises.", "Still air.", "Sinking air."],
        "answer": "A",
        "complexity": "BASE",
    },
    {
        "id": "gold/cloze/0",
        "task": "cloze",
        "question": "<MASK> cools the surface.",
        "answer": "Evaporation",
        "complexity": "",
    },
]


def write_set(tmp_path):
    path = tmp_path / "set.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in RECORDS), encoding="utf-8")
    return str(path)


def accuracy(task, reply, tmp_path):
    model = get_model(
        "mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", reply)]
    )
    log = eval(task, model=model, log_dir=str(tmp_path / "logs"), display="none")[0]
    assert log.status == "success" and len(log.samples) == 1
    return log.results.scores[0].metrics["accuracy"].value


def test_mcq_task_scores_the_keyed_letter_and_ignores_cloze_rows(tmp_path):
    task = tasks.climaqa_mcq(path=write_set(tmp_path), shuffle=False)
    assert accuracy(task, "ANSWER: A", tmp_path) == 1.0
    assert accuracy(task, "ANSWER: B", tmp_path) == 0.0


def test_cloze_task_needs_the_missing_word_only(tmp_path):
    task = tasks.climaqa_cloze(path=write_set(tmp_path))
    assert accuracy(task, "evaporation", tmp_path) == 1.0
    assert accuracy(task, "condensation", tmp_path) == 0.0
