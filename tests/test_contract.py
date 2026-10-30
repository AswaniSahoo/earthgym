import pytest
from climaqa_v1 import contract


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("ANSWER: C", "C"),
        ("Warm air is less dense.\nANSWER: B", "B"),
        ("answer: a", "A"),
        ("**ANSWER: D**", "D"),
        ("ANSWER: (B).", "B"),
        ("ANSWER: A\nANSWER: C", "C"),
        ("ANSWER: C. A warm parcel is less dense.", None),
        ("A", None),
        ("The answer is B", None),
        ("", None),
    ],
)
def test_mcq_choice_reads_only_a_clean_answer_line(reply, expected):
    assert contract.mcq_choice(reply) == expected


@pytest.mark.parametrize(
    ("reply", "key", "correct"),
    [
        ("Evaporation.", "evaporation", True),
        ("the evaporation", "evaporation", True),
        ("CO2-driven warming", "co2 driven warming", True),
        ("evaporations", "evaporation", False),
        ("condensation", "evaporation", False),
        ("", "", False),
    ],
)
def test_cloze_correct_is_squad_style_exact_match(reply, key, correct):
    assert contract.cloze_correct(reply, key) is correct


def test_mcq_prompt_lists_lettered_options_and_the_answer_line_rule():
    text = contract.mcq_prompt("Why?", ["w", "x", "y", "z"])
    assert "A) w\nB) x\nC) y\nD) z" in text and "ANSWER: X" in text
