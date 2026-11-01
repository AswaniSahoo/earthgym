import json

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelOutput, ModelUsage, get_model

from rlenv.ibtracs import report, tasks


def item(question, sid, rows, key):
    return {"id": f"{question}/{sid}", "sid": sid, "season": 2021, "name": "TEST"} | {
        "question": question,
        "rows": [[f"2021-08-26 {t}:00", s, w, 1000] for t, s, w in rows],
        "key": key,
    }


ITEMS = [
    # ACE: 00:00 SS 40 and 12:00 TS 50 count, 0.41; every row adds the 15:00 60 (0.77); ignoring
    # status adds the 18:00 EX 40 (0.57); TS and HU only drops the SS row (0.25)
    item(
        "ace",
        "A",
        [("00:00", "SS", 40), ("12:00", "TS", 50), ("15:00", "TS", 60), ("18:00", "EX", 40)],
        0.41,
    ),
    # peak category 1 from the HU row; the EX row's 100 kt would make it 3
    item("peak_category", "B", [("06:00", "HU", 70), ("12:00", "EX", 100)], 1),
    # hours: 06:00 and 12:00 count, 12; the 09:00 row would make every HU row 18
    item(
        "hurricane_hours", "C", [("06:00", "HU", 70), ("09:00", "HU", 70), ("12:00", "HU", 70)], 12
    ),
]


def test_careless_readings_fall_into_each_trap():
    assert report.careless(ITEMS[0]) == {
        "ACE over every row": 0.8,
        "ACE ignoring status": 0.6,
        "ACE from TS and HU only": 0.2,  # 0.25 rounded half to even
    }
    assert report.careless(ITEMS[1]) == {
        "category ignoring status": 3,
        "category from synoptic rows only": 1,
        "category by the mph thresholds": 0,  # 70 kt is under 74, the mph floor of category 1
    }
    landfall = item("peak_category", "J", [("06:00", "HU", 90), ("17:45", "HU", 96)], 3)
    assert report.careless(landfall)["category from synoptic rows only"] == 2


def test_hours_readings_split_on_a_track_with_two_hurricane_spells():
    rows = [("00:00", "HU", 70), ("03:00", "HU", 70), ("06:00", "TS", 60)]
    rows += [("09:00", "TS", 60), ("12:00", "HU", 70), ("15:00", "TS", 60)]
    two = item("hurricane_hours", "K", rows, 12)  # 00:00 and 12:00 count
    assert report.careless(two) == {
        "hours over every HU row": 18,
        "each row's status holds until the next row": 9,  # 3 + 3 + 3
        "elapsed time of each hurricane spell": 3,  # 00:00 to 03:00, then 12:00 to 12:00
    }


def test_best_constant_is_the_single_answer_right_most_often():
    keys = zip("DEF", (1, 1, 3), strict=True)
    rows = [item("peak_category", s, [("06:00", "HU", 70)], k) for s, k in keys]
    assert report.best_constant(rows) == (1, pytest.approx(2 / 3))
    keys = zip("GHI", (0.16, 0.17, 0.9), strict=True)
    ace = [item("ace", s, [("06:00", "TS", 40)], k) for s, k in keys]
    assert report.best_constant(ace) == (0.2, pytest.approx(2 / 3))  # within 0.05 of 0.16, 0.17


@pytest.fixture(scope="module")
def log(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("storm")
    path = tmp / "items.jsonl"
    path.write_text("".join(json.dumps(i) + "\n" for i in ITEMS), encoding="utf-8")
    outputs = []
    replies = ("Adding every row.\nANSWER: 0.8", "This is Hurricane Test.\nANSWER: 1", "A day.")
    for text in replies:
        out = ModelOutput.from_content("mockllm/model", text)
        out.usage = ModelUsage(input_tokens=200, output_tokens=100)
        outputs.append(out)
    model = get_model("mockllm/model", custom_outputs=outputs)
    task = tasks.ibtracs_storm(path=str(path))
    return eval(task, model=model, log_dir=str(tmp), display="none", max_connections=1)[0]


def test_summary_scores_each_question_and_names_the_traps_the_misses_fell_into(log):
    s = report.summarize(log, ITEMS)
    assert (s["n"], s["parse_failures"], s["errors"]) == (3, 1, 0)
    assert s["reward"] == pytest.approx(1 / 3)
    by = {r["question"]: r for r in s["questions"]}
    assert (by["ace"]["accuracy"], by["peak_category"]["accuracy"]) == (0.0, 1.0)
    assert by["ace"]["traps"] == {
        "ACE over every row": 1,
        "ACE ignoring status": 0,
        "ACE from TS and HU only": 0,
    }
    assert s["cost"] == pytest.approx((600 * 2 + 300 * 10) / 1e6)


def test_render_lists_the_model_the_constant_and_the_careless_readings(log):
    text = report.render(report.summarize(log, ITEMS))
    assert "| ace | model | 1 | 0.000 |" in text
    assert "| ace | ACE over every row | 1 | 0.000 |" in text
    assert "| peak_category | best constant (1) | 1 | 1.000 |" in text
    assert "## Limits" in text
    # a careless reading right on most items means the question tests something else
    line = "- peak_category: 'category from synoptic rows only' is right on 1 of 1 items"
    assert line in text and "reading the Saffir-Simpson scale" in text
    assert "- ace: '" not in text


def summary(reward, accuracies, traps=None, explained=None):
    questions = [
        {"question": q, "n": 100, "accuracy": a, "traps": (traps or {}).get(q, {})}
        | {"explained": (explained or {}).get(q, 0)}
        for q, a in accuracies.items()
    ]
    return {"model": "m/x", "n": 300, "reward": reward, "questions": questions} | {
        "recognized": 2,
        "recognized_what": "name the storm or its season",
    }


def test_pair_report_puts_both_runs_side_by_side_with_a_plain_rl_line():
    shown = summary(0.997, {"ace": 0.99, "peak_category": 1.0, "hurricane_hours": 1.0})
    traps = {"ace": {"ACE over every row": 30}}
    hidden = summary(0.6, {"ace": 0.4, "peak_category": 0.9, "hurricane_hours": 0.5}, traps)
    text = report.render_pair(shown, hidden)
    assert "| ace | 100 | 0.990 | 0.400 |" in text and "| all | 300 | 0.997 | 0.600 |" in text
    assert "| ace | ACE over every row | 30 |" in text
    assert "almost no signal" in text and "room to learn" in text
    close = report.render_pair(shown, summary(0.98, {"ace": 0.97}))
    assert "near the ceiling" in close and "room to learn" not in close


def test_pair_report_names_a_convention_gap_per_question():
    shown = summary(0.997, {"ace": 0.99, "hurricane_hours": 1.0})
    traps = {"hurricane_hours": {"each row's status holds until the next row": 41}}
    hidden = summary(0.56, {"ace": 0.99, "hurricane_hours": 0.13}, traps, {"hurricane_hours": 57})
    text = report.render_pair(shown, hidden)
    assert "- ace: 0.990 with the rules shown, 0.990 hidden: near the ceiling either way" in text
    assert "57 of the 87 misses follow a careless reading" in text and "convention gap" in text
    assert "room to learn" not in text
    assert "name the storm or its season: 2 of 300 with the rules shown, 2 hidden" in text


def test_summary_counts_replies_that_name_the_storm_and_reads_the_rules_flag(log):
    s = report.summarize(log, ITEMS)
    assert (s["recognized"], s["rules"]) == (1, True)
    assert s["questions"][0]["explained"] == 1  # the ACE miss equals a careless reading
    assert "1 of 3 replies name the storm or its season" in report.render(s)


def test_a_rules_hidden_log_says_so_in_its_report(tmp_path):
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(ITEMS[1]) + "\n", encoding="utf-8")
    model = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("m", "ANSWER: 1")])
    task = tasks.ibtracs_storm(path=str(path), rules=False)
    hidden = eval(task, model=model, log_dir=str(tmp_path), display="none")[0]
    text = report.render(report.summarize(hidden, ITEMS))
    assert text.startswith("# ibtracs-storm-v1 on model (rules hidden)")
    assert "the rules-shown run is the control" in text and "not run here" not in text
