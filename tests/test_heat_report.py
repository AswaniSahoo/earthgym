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
# events at 110, k 2: a run of 4, then a run of 2; blocks of k days count 2 + 1
LONG = item("events", [110, 111, 112, 113, 109, 110, 111], [100] * 7, 2, k=2)


def test_careless_readings_fall_into_each_trap():
    assert report.careless(ITEMS[0]) == {
        "above, not at, the threshold": 1,
        "the site's column": 3,
    }
    assert report.careless(ITEMS[1]) == {
        "trigger days, not events": 4,
        "every run, whatever its length": 2,
        "missing days skipped": 1,
        "blocks of k days": 2,
        "runs longer than k": 0,
        "runs of exactly k": 2,
    }
    assert report.careless(LONG) == {
        "trigger days, not events": 6,
        "every run, whatever its length": 2,
        "missing days skipped": 2,
        "blocks of k days": 3,
        "runs longer than k": 1,
        "runs of exactly k": 1,
    }
    assert report.careless(ITEMS[2]) == {
        "both ways": 3,
        "every hot site day": 3,
        "missing index days left out": 1,
        "site strictly above the threshold": 1,  # 05-02 at 111; 05-03 is at 110, not above
        "the other way round": 1,  # 05-01: the index at 110, the site at 108
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
    for text in ("ANSWER: 3", "In 2020 it ran twice.\nANSWER: 2", "Two days."):
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
    assert by["trigger_days"]["off_by_one"] == 1 and s["recognized"] == 1  # 3 for 2; "2020"
    assert by["trigger_days"]["matched"] == {"the site's column": [ITEMS[0]["id"]]}
    assert by["events"]["where"] == {"missing days skipped": {"Index 2020": 1}}


def test_render_lists_the_model_the_constant_and_the_careless_readings(log):
    text = report.render(report.summarize(log, ITEMS))
    assert "| trigger_days | model | 1 | 0.000 |" in text
    assert "| trigger_days | the site's column | 1 | 0.000 |" in text
    assert "| events | best constant (2) | 1 | 1.000 |" in text
    assert "## Limits" in text
    assert "Matches are by value. Misses off by exactly one: 1 of 1" in text
    assert "1 of 3 replies name a season from 2015 to 2024" in text
    assert "'missing days skipped' gives another answer than the key on 1 of 1 events items" in text
    assert "Index 2020 (1)" in text and "policyholder's side of basis risk only" in text
    assert "storm" not in text


def test_pair_report_names_the_terms_only_ablation():
    shown = {"model": "m/x", "n": 300, "reward": 1.0, "questions": []}
    shown["questions"] = [{"question": "events", "n": 100, "accuracy": 1.0, "traps": {}}]
    hidden = shown | {"reward": 0.7}
    hidden["questions"] = [
        {"question": "events", "n": 100, "accuracy": 0.7, "traps": {"trigger days, not events": 5}}
    ]
    text = report.render_pair(shown, hidden)
    assert "# heat-basis-v1: rules shown against terms only" in text
    assert "| events | 100 | 1.000 | 0.700 |" in text and "room to learn" in text


def test_a_terms_only_log_says_so_and_counts_explained_misses(tmp_path):
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(ITEMS[0]) + "\n", encoding="utf-8")
    model = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("m", "ANSWER: 3")])
    hidden = eval(
        tasks.heat_basis(path=str(path), rules=False), model=model, log_dir=str(tmp_path)
    )[0]
    s = report.summarize(hidden, ITEMS)
    assert s["rules"] is False and s["questions"][0]["explained"] == 1  # 3 is the site's column
    text = report.render(s)
    assert text.startswith("# heat-basis-v1 on model (terms only)")
    assert ", with the policy terms alone in the prompt." in text
    assert "the rules-shown run is the control" in text and "not run here" not in text


def test_a_small_drop_that_one_reading_explains_is_a_convention_gap():
    q = {"question": "missed_days", "n": 100, "accuracy": 0.96, "traps": {}, "explained": 0}
    shown = {"model": "m/x", "n": 100, "reward": 0.96, "questions": [q]}
    h = q | {"accuracy": 0.89, "traps": {"missing index days left out": 6}, "explained": 6}
    text = report.render_pair(shown, {"model": "m/x", "n": 100, "reward": 0.89, "questions": [h]})
    assert "6 of the 11 misses follow a careless reading" in text and "convention gap" in text
    assert "constant offset" not in text and "in a few steps" in text


def test_pair_report_says_where_the_differing_items_sit():
    q = {"question": "missed_days", "n": 100, "accuracy": 0.96, "traps": {}, "explained": 0}
    shown = {"model": "m/x", "n": 100, "reward": 0.96, "questions": [q]}
    where = {"missing index days left out": {"Phoenix Deer Valley Municipal Airport 2019": 8}}
    h = q | {"accuracy": 0.89, "traps": {}, "explained": 7, "where": where}
    text = report.render_pair(shown, {"model": "m/x", "n": 100, "reward": 0.89, "questions": [h]})
    assert "Phoenix Deer Valley Municipal Airport 2019 (8)" in text


def test_heat_pair_report_never_mentions_storms(log):
    s = report.summarize(log, ITEMS)
    assert s["recognized_what"] == "name a season from 2015 to 2024"
    assert "storm" not in report.render_pair(s, s)


def test_a_log_from_other_items_is_refused(log):
    with pytest.raises(ValueError, match="differs"):
        report.summarize(log, [i | {"key": -1} for i in ITEMS])
