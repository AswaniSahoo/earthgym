import json

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelOutput, ModelUsage, get_model

from rlenv.heat import report, tasks


def item(question, index_f, site_f, key, threshold=110, k=None):
    n = len(index_f)
    return {"id": f"{question}/A/B/2020/{threshold}", "question": question, "index": "A"} | {
        "site": "B",
        "index_name": "Index",
        "site_name": "Site",
        "year": 2020,
        "threshold": threshold,
        "k": k,
        "dates": [f"05-{d:02d}" for d in range(1, n + 1)],
        "index_f": index_f,
        "site_f": site_f,
        "key": key,
    }


ITEMS = [
    # trigger days at 110: 110, 111 count (2); strictly above counts 1; the site column counts 3
    item("trigger_days", [110, 111, 109, None], [112, 110, 110, 108], 2),
    # events at 110, k 2: one run of 2 (05-01, 05-02); a gap on 05-03 then 05-04 and 05-05
    item("events", [110, 112, None, 110, 111], [100] * 5, 2, k=2),
    # missed at 110: 05-02 (index missing) and 05-03 (index 109); index-only 05-01 (site 108)
    item("missed_days", [110, None, 109, 112], [108, 111, 110, 111], 2),
]


def test_careless_readings_fall_into_each_trap():
    assert report.careless(ITEMS[0]) == {
        "above, not at, the threshold": 1,
        "the site's column": 3,
    }
    assert report.careless(ITEMS[1]) == {
        "trigger days, not events": 4,
        "every run, whatever its length": 2,
        "missing days skipped": 1,
    }
    assert report.careless(ITEMS[2]) == {
        "both ways": 3,
        "every hot site day": 3,
        "missing index days left out": 1,
    }


def test_best_constant_is_the_single_answer_right_most_often():
    rows = [item("events", [100], [100], k_, k=2) for k_ in (0, 0, 3)]
    assert report.best_constant(rows) == (0, pytest.approx(2 / 3))


@pytest.fixture(scope="module")
def log(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("heat")
    path = tmp / "items.jsonl"
    path.write_text("".join(json.dumps(i) + "\n" for i in ITEMS), encoding="utf-8")
    outputs = []
    for text in ("ANSWER: 3", "ANSWER: 2", "Two days."):
        out = ModelOutput.from_content("mockllm/model", text)
        out.usage = ModelUsage(input_tokens=1000, output_tokens=100)
        outputs.append(out)
    model = get_model("mockllm/model", custom_outputs=outputs)
    task = tasks.heat_basis(path=str(path))
    return eval(task, model=model, log_dir=str(tmp), display="none", max_connections=1)[0]


def test_summary_scores_each_question_and_names_the_traps_the_misses_fell_into(log):
    s = report.summarize(log, ITEMS)
    assert (s["n"], s["parse_failures"], s["errors"]) == (3, 1, 0)
    assert s["reward"] == pytest.approx(1 / 3)
    by = {r["question"]: r for r in s["questions"]}
    assert (by["trigger_days"]["accuracy"], by["events"]["accuracy"]) == (0.0, 1.0)
    assert by["trigger_days"]["traps"] == {
        "above, not at, the threshold": 0,
        "the site's column": 1,
    }
    assert s["cost"] == pytest.approx((3000 * 2 + 300 * 10) / 1e6)


def test_render_lists_the_model_the_constant_and_the_careless_readings(log):
    text = report.render(report.summarize(log, ITEMS))
    assert "| trigger_days | model | 1 | 0.000 |" in text
    assert "| trigger_days | the site's column | 1 | 0.000 |" in text
    assert "| events | best constant (2) | 1 | 1.000 |" in text
    assert "## Limits" in text
