import re

from ibtracs_storm_v1 import contract
from ibtracs_storm_v1.taskset import records

ITEM = {
    "id": "ace/2021239N17281",
    "sid": "2021239N17281",
    "season": 2021,
    "name": "IDA",
    "question": "ace",
    "rows": [["2021-08-26 12:00:00", "TS", 50, 1006], ["2021-08-27 23:25:00", "HU", 70, None]],
    "key": 0.25,
}


def test_prompt_shows_every_row_without_year_name_or_sid():
    text = contract.prompt(ITEM)
    assert "08-26 12:00 | TS | 50 | 1006" in text and "08-27 23:25 | HU | 70 | -" in text
    assert "2021" not in text and "IDA" not in text
    assert text.rstrip().endswith("The last line of your response must be 'ANSWER: <number>'.")


def test_each_question_carries_its_own_rule():
    ace = contract.prompt(ITEM)
    exact = "at exactly 00:00, 06:00, 12:00 or 18:00 UTC (a row at 12:30 does not count)"
    assert exact in ace and "TS, HU or SS" in ace and "34 kt" in ace
    assert "10^4" in ace and "one decimal" in ace
    category = contract.prompt(ITEM | {"question": "peak_category"})
    assert "137 kt or more is 5" in category and "any time" in category
    assert "A storm with no HU row at 64 kt or more is 0" in category
    hours = contract.prompt(ITEM | {"question": "hurricane_hours"})
    assert "6 hours for each row " + exact in hours
    assert "squares" not in hours


def test_answer_takes_the_last_answer_line_only():
    assert contract.answer("ANSWER: 3\nNo, wait.\nANSWER: 4.") == 4.0
    assert contract.answer("ANSWER: \u221212.5") == -12.5
    assert contract.answer("The answer is 4") is None
    assert contract.answer("ANSWER:\n4") is None  # the number must sit on the answer line


def test_ace_is_right_within_half_a_step_of_the_exact_value():
    assert contract.reward("ace", 12.3, 12.345) == 1.0
    assert contract.reward("ace", 12.4, 12.345) == 0.0  # wrong rounding
    assert contract.reward("ace", 12.3, 12.35) == contract.reward("ace", 12.4, 12.35) == 1.0
    assert contract.reward("ace", 12.35, 12.35) == 1.0
    assert contract.reward("ace", None, 12.35) == 0.0


def test_category_and_hours_must_match_exactly():
    assert contract.reward("peak_category", 3.0, 3) == 1.0
    assert contract.reward("peak_category", 2.0, 3) == 0.0
    assert contract.reward("hurricane_hours", 48, 48) == 1.0
    assert contract.reward("hurricane_hours", 47.9, 48) == 0.0


def test_the_rule_can_be_left_out_for_the_ablation():
    hidden = contract.prompt(ITEM, rules=False)
    assert "Rule." not in hidden and "00:00, 06:00" not in hidden
    assert "08-26 12:00 | TS | 50 | 1006" in hidden and "Statuses:" in hidden
    assert "rounded to one decimal" in hidden  # the question keeps its units and rounding
    assert hidden.rstrip().endswith("'ANSWER: <number>'.")


def test_every_status_in_the_items_is_in_the_legend():
    legend = set(re.findall(r"\b([A-Z]{2}) [a-z]", contract.STATUSES))
    assert {row[1] for item in records() for row in item["rows"]} <= legend
