import json

from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from rlenv.climaqa import tasks

RECORDS = [
    {
        "id": "gold/mcq/0",
        "task": "mcq",
        "question": "Why does convection start?",
        "options": ["Cold air rises.", "Warm air rises.", "Still air.", "Sinking air."],
        "answer": "B",
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
    output = ModelOutput.from_content("mockllm/model", reply)
    model = get_model("mockllm/model", custom_outputs=[output])
    log = eval(task, model=model, log_dir=str(tmp_path / "logs"), display="none")[0]
    assert log.status == "success" and len(log.samples) == 1
    return log.results.scores[0].metrics["accuracy"].value


def test_default_tasks_read_the_bundled_clean_set_from_any_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # Inspect changes directory to the task file before loading
    assert (len(tasks.climaqa_mcq().dataset), len(tasks.climaqa_cloze().dataset)) == (222, 128)


def test_mcq_task_scores_with_the_shared_contract(tmp_path):
    task = tasks.climaqa_mcq(path=write_set(tmp_path))
    assert accuracy(task, "Warm air is lighter.\nANSWER: B", tmp_path) == 1.0
    assert accuracy(task, "B", tmp_path) == 0.0


def test_cloze_task_scores_with_the_shared_contract(tmp_path):
    task = tasks.climaqa_cloze(path=write_set(tmp_path))
    assert accuracy(task, "the evaporation", tmp_path) == 1.0
    assert accuracy(task, "condensation", tmp_path) == 0.0
