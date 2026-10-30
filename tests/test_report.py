import json

from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from rlenv.climaqa import report, tasks

MCQ = [
    {
        "id": "gold/mcq/1",
        "task": "mcq",
        "question": "Q1?",
        "options": list("wxyz"),
        "answer": "B",
        "complexity": "BASE",
    },
    {
        "id": "gold/mcq/2",
        "task": "mcq",
        "question": "Q2?",
        "options": list("wxyz"),
        "answer": "C",
        "complexity": "REASONING",
    },
]


def run(tmp_path, reply):
    path = tmp_path / "set.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in MCQ), encoding="utf-8")
    outputs = [ModelOutput.from_content("mockllm/model", reply)] * len(MCQ)
    model = get_model("mockllm/model", custom_outputs=outputs)
    task = tasks.climaqa_mcq(path=str(path))
    return eval(task, model=model, log_dir=str(tmp_path / "logs"), display="none")[0]


def test_summary_counts_accuracy_complexity_and_format_failures(tmp_path):
    summary = report.summarize(run(tmp_path, "ANSWER: B"))
    assert (summary["n"], summary["accuracy"], summary["format_failures"]) == (2, 0.5, 0)
    assert summary["by_complexity"] == {"BASE": 1.0, "REASONING": 0.0}
    assert report.summarize(run(tmp_path, "B"))["format_failures"] == 2


def test_render_lists_each_task_with_its_model_and_the_set_checksum(tmp_path):
    text = report.render([report.summarize(run(tmp_path, "ANSWER: B"))], set_sha256="abc123")
    assert "| climaqa_mcq | mockllm/model | 2 | 0.500 |" in text and "abc123" in text
