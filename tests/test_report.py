import json

from inspect_ai import eval
from inspect_ai.log import EvalRevision
from inspect_ai.model import GenerateConfig, ModelOutput, ModelUsage, get_model

from rlenv.climaqa import report, tasks

MCQ = [
    {
        "id": "gold/mcq/1",
        "task": "mcq",
        "question": "Q1?",
        "options": ["w", "xx", "y", "z"],
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


CLOZE = [
    {
        "id": "gold/cloze/1",
        "task": "cloze",
        "question": "The <MASK> rises.",
        "answer": "sun",
        "complexity": "",
    },
    {
        "id": "gold/cloze/2",
        "task": "cloze",
        "question": "The <MASK> falls.",
        "answer": "rain",
        "complexity": "",
    },
]


def run(tmp_path, reply, model_config=None, kind="mcq", **config):
    rows = MCQ if kind == "mcq" else CLOZE
    path = tmp_path / "set.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    output = ModelOutput.from_content("mockllm/model", reply)
    output.usage = ModelUsage(input_tokens=10, output_tokens=5, total_tokens=15, reasoning_tokens=3)
    model = get_model("mockllm/model", config=model_config, custom_outputs=[output] * len(rows))
    task = (tasks.climaqa_mcq if kind == "mcq" else tasks.climaqa_cloze)(path=str(path))
    return eval(task, model=model, log_dir=str(tmp_path / "logs"), display="none", **config)[0]


def test_summary_counts_accuracy_complexity_and_format_failures(tmp_path):
    summary = report.summarize(run(tmp_path, "ANSWER: B"))
    assert (summary["n"], summary["accuracy"], summary["format_failures"]) == (2, 0.5, 0)
    assert summary["by_complexity"] == {
        "BASE": {"n": 1, "accuracy": 1.0},
        "REASONING": {"n": 1, "accuracy": 0.0},
    }
    assert report.summarize(run(tmp_path, "B"))["format_failures"] == 2


def test_render_lists_each_task_with_its_model_and_the_set_checksum(tmp_path):
    text = report.render([report.summarize(run(tmp_path, "ANSWER: B"))], set_sha256="abc123")
    assert "| climaqa_mcq | mockllm/model | 2 | 0.500 |" in text and "abc123" in text


def test_render_gives_n_and_accuracy_per_complexity_level(tmp_path):
    text = report.render([report.summarize(run(tmp_path, "ANSWER: B"))], set_sha256="abc123")
    assert "| climaqa_mcq | BASE | 1 | 1.000 |" in text
    assert "| climaqa_mcq | REASONING | 1 | 0.000 |" in text


def test_cloze_runs_report_no_format_check(tmp_path):
    summary = report.summarize(run(tmp_path, "sun", kind="cloze"))
    assert summary["format_failures"] is None
    text = report.render([summary], set_sha256="abc123")
    assert "| climaqa_cloze | mockllm/model | 2 | 0.500 | 0.500 | n/a |" in text


def test_render_warns_about_a_dirty_tree_and_provider_defaults(tmp_path):
    log = run(tmp_path, "ANSWER: B")
    log.eval.revision = EvalRevision(type="git", origin="o", commit="abc1234", dirty=True)
    text = report.render([report.summarize(log)], set_sha256="abc123")
    assert "uncommitted changes at run time" in text
    assert "provider's defaults" in text


def test_render_leaves_out_warnings_that_do_not_apply(tmp_path):
    log = run(tmp_path, "ANSWER: B", temperature=0.0)
    log.eval.revision = EvalRevision(type="git", origin="o", commit="abc1234", dirty=False)
    text = report.render([report.summarize(log)], set_sha256="abc123")
    assert "uncommitted changes" not in text and "provider's defaults" not in text


def test_render_gives_key_letters_and_the_longest_option_share(tmp_path):
    text = report.render([report.summarize(run(tmp_path, "ANSWER: B"))], set_sha256="abc123")
    assert (
        "climaqa_mcq keys: A 0, B 1, C 1, D 0; the key is the strictly longest option in 1 of 2"
        in text
    )


def test_render_links_the_miss_notes_beside_the_report(tmp_path):
    summary = report.summarize(run(tmp_path, "ANSWER: B"))
    text = report.render([summary], set_sha256="abc123", notes=["r-cloze-misses.md"])
    assert "[r-cloze-misses.md](r-cloze-misses.md)" in text


def test_render_gives_when_each_task_ran(tmp_path):
    log = run(tmp_path, "ANSWER: B")
    log.stats.started_at = "2026-01-01T00:00:00+00:00"
    log.stats.completed_at = "2026-01-01T00:10:00+00:00"
    text = report.render([report.summarize(log)], set_sha256="abc123")
    assert "climaqa_mcq from 2026-01-01T00:00:00+00:00 to 2026-01-01T00:10:00+00:00" in text


def test_summary_records_the_run_config(tmp_path):
    log = run(tmp_path, "ANSWER: B", GenerateConfig(max_tokens=50), temperature=0.0)
    log.eval.revision = EvalRevision(type="git", origin="o", commit="abc1234", dirty=True)
    summary = report.summarize(log)
    assert summary["commit"] == "abc1234 (dirty)"
    assert summary["generate_config"] == "max_tokens 50, temperature 0.0"
    assert summary["tokens"] == {"input": 20, "output": 10, "reasoning": 6}
    assert summary["log"] == next((tmp_path / "logs").glob("*.eval")).name


def test_summary_labels_settings_the_log_does_not_record(tmp_path):
    log = run(tmp_path, "ANSWER: B")
    log.eval.revision = None
    summary = report.summarize(log)
    assert (summary["commit"], summary["generate_config"]) == ("unknown", "provider defaults")


def test_render_prints_the_run_config_of_each_task(tmp_path):
    log = run(tmp_path, "ANSWER: B", temperature=0.0)
    log.eval.revision = EvalRevision(type="git", origin="o", commit="abc1234", dirty=False)
    text = report.render([report.summarize(log)], set_sha256="abc123")
    name = next((tmp_path / "logs").glob("*.eval")).name
    assert f"| climaqa_mcq | abc1234 | temperature 0.0 | 20 | 10 | 6 | {name} |" in text
