"""One answer-line rule for every environment (Codex review finding 12): the answer sits on the
reply's last non-empty line, as each prompt asks; Markdown bold and code marks and the Unicode
minus read as plain text; the number shares the line with ANSWER; only finite numbers count."""

import pytest
from climaqa_v1 import contract as climaqa
from era5_forecast_v1 import contract as era5
from heat_basis_v1 import contract as heat
from ibtracs_storm_v1 import contract as ibtracs

NUMERIC = {"era5": era5.answer, "ibtracs": ibtracs.answer, "heat": heat.answer}
CASES = [
    ("Working.\nANSWER: 3", 3.0),
    ("**ANSWER: 3**", 3.0),
    ("ANSWER: **3**", 3.0),
    ("`ANSWER: 3`", 3.0),
    ("ANSWER: −3", -3.0),
    ("ANSWER: 3\n\n", 3.0),  # trailing blank lines are fine
    ("ANSWER: 3\nANSWER: 4", 4.0),  # the last line wins
    ("ANSWER: 3\nActually it is 4.", None),  # a trailing contradiction: the answer is not last
    ("ANSWER:\n3", None),  # split across lines
    ("ANSWER: 1e999", None),  # not finite
    ("The answer is 3", None),
]


@pytest.mark.parametrize("name", NUMERIC)
@pytest.mark.parametrize(("reply", "expected"), CASES)
def test_numeric_answer_lines_follow_one_rule(name, reply, expected):
    assert NUMERIC[name](reply) == expected


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("Working.\nANSWER: B", "B"),
        ("**ANSWER: B**", "B"),
        ("ANSWER: (b).", "B"),
        ("ANSWER: B\n\n", "B"),
        ("ANSWER: B\nOn reflection, C.", None),
        ("ANSWER:\nB", None),
    ],
)
def test_the_mcq_answer_line_follows_the_same_rule(reply, expected):
    assert climaqa.mcq_choice(reply) == expected
