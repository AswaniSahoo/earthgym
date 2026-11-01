import json

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelOutput, ModelUsage, get_model

from earthgym.era5 import report, tasks

ROW = {
    "id": "2m_temperature/2020-07-01T00/24h/0-0",
    "variable": "2m_temperature",
    "latitude": 47.8125,
    "longitude": 8.4375,
    "init_time": "2020-07-01T00",
    "valid_time": "2020-07-02T00",
    "lead_hours": 24,
    "history_times": ["2020-06-30T18", "2020-07-01T00"],
    "history": [291.0, 292.0],
    "climatology": 289.0,
    "truth": 290.0,
    "hres": 290.4,
    "area_weight": 1.0,
    "floor": 2.0,
}
# better-baseline error 1 for both answered items, floor 2: rewards (1 - 0.5) / 2 and 1 / 2
ITEMS = [
    ROW,
    ROW | {"id": "2m_temperature/2020-07-01T00/24h/0-1", "truth": 291.0},
    ROW | {"id": "2m_temperature/2020-07-01T00/24h/0-2"},
]
REPLIES = ["Reasoning.\nANSWER: 289.5", "ANSWER: 291.0 K", "I cannot say."]


@pytest.fixture(scope="module")
def log(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("era5")
    path = tmp / "items.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ITEMS), encoding="utf-8")
    outputs = []
    for text in REPLIES:
        out = ModelOutput.from_content("mockllm/model", text)
        out.usage = ModelUsage(input_tokens=100, output_tokens=50, reasoning_tokens=30)
        outputs.append(out)
    model = get_model("mockllm/model", custom_outputs=outputs)
    task = tasks.era5_forecast(path=str(path))
    return eval(task, model=model, log_dir=str(tmp), display="none", max_connections=1)[0]


def test_summary_counts_parse_failures_and_scores_every_item(log):
    s = report.summarize(log, ITEMS)
    assert (s["n"], s["parsed"], s["parse_failures"], s["errors"]) == (3, 2, 1, 0)
    assert s["reward"] == pytest.approx(0.25)  # (0.25 + 0.5 + 0) / 3
    assert s["reward"] == pytest.approx(log.results.scores[0].metrics["mean"].value)


def test_model_row_is_graded_like_the_baselines_on_the_answered_items(log):
    rows = {r["baseline"]: r for r in report.summarize(log, ITEMS)["table"]}
    model = rows["model"]
    assert model["n"] == 2 and rows["persistence"]["n"] == 2
    assert model["rmse"] == pytest.approx((0.25 / 2) ** 0.5)  # errors 0.5 and 0
    # anomalies (0.5, 2) and (1, 2): 2.25 / sqrt(2.125 * 2.5)
    assert model["acc"] == pytest.approx(2.25 / (2.125 * 2.5) ** 0.5)
    assert model["reward"] == pytest.approx(0.375)


def test_tokens_and_cost_come_from_the_log_at_the_page_prices(log):
    s = report.summarize(log, ITEMS)
    assert (s["tokens"]["input"], s["tokens"]["output"]) == (300, 150)
    assert s["batch"] is False and s["cost"] == pytest.approx((300 * 2 + 150 * 10) / 1e6)
    assert s["item_costs"] == pytest.approx([(100 * 2 + 50 * 10) / 1e6] * 3)


def test_a_log_from_other_items_is_refused(log):
    with pytest.raises(ValueError, match="truth"):
        report.summarize(log, [r | {"truth": 0.0} for r in ITEMS])


def test_render_shows_the_model_row_parse_failures_and_limits(log):
    text = report.render(report.summarize(log, ITEMS))
    assert "| 2m_temperature | 24 | model | 2 | 0.354 | 0.976 | 0.375 |" in text
    assert "Replies without a parseable answer line: 1 of 3" in text
    assert "## Limits" in text


def test_the_model_is_compared_with_the_midpoint_item_by_item(log):
    s = report.summarize(log, ITEMS)
    # midpoint 290.5 earns 0.25 on all three items; the model 0.25, 0.5 and 0
    assert s["paired"] == {
        "diff": pytest.approx(0.0),
        "se": pytest.approx(0.25 / 3**0.5),
        "higher": 1,
        "lower": 1,
        "tied": 1,
    }
    text = report.render(s)
    assert "Against the midpoint (persistence + climatology) / 2, item by item: +0.0000" in text
    assert "not significant at two standard errors" in text
    assert "| 2m_temperature | 24 | midpoint | 2 |" in text


def test_a_run_with_no_samples_is_refused(log):
    with pytest.raises(ValueError, match="no samples"):
        report.summarize(log.model_copy(update={"samples": []}), ITEMS)


def test_a_one_item_run_has_no_standard_error_and_no_test(log):
    s = report.summarize(log.model_copy(update={"samples": log.samples[:1]}), ITEMS)
    assert (s["n"], s["stderr"], s["paired"]["se"]) == (1, None, None)
    text = report.render(s)
    assert "(stderr n/a, one item)" in text and "(SE n/a)" in text
    assert "too few items to test" in text and "significant" not in text


def test_items_that_left_the_set_are_left_out_of_every_number(log):
    s = report.summarize(log, ITEMS[:2])  # the third item failed a later gold check, say
    assert (s["n"], s["left_out"], s["parse_failures"]) == (2, 1, 0)
    assert "1 of them failed the gold check (decision 0021)" in report.render(s)
    assert report.summarize(log, ITEMS)["left_out"] == 0
