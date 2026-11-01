from types import SimpleNamespace

import pytest
from inspect_ai.scorer import CORRECT, INCORRECT, Score

from rlenv.climaqa import compare


def sample(sid, right, answer, level="BASE"):
    score = Score(value=CORRECT if right else INCORRECT, answer=answer)
    return SimpleNamespace(
        id=sid, scores={"contract_scorer": score}, metadata={"complexity": level}
    )


def log(model, samples):
    spec = SimpleNamespace(task="climaqa_mcq", model=model)
    return SimpleNamespace(eval=spec, samples=samples)


def test_mcnemar_is_the_exact_two_sided_binomial_test_on_discordant_pairs():
    assert compare.mcnemar(0, 5) == pytest.approx(2 / 32)
    assert compare.mcnemar(2, 8) == pytest.approx(2 * (1 + 10 + 45) / 1024)
    assert compare.mcnemar(3, 3) == 1.0
    assert compare.mcnemar(0, 0) == 1.0


def test_compare_pairs_items_by_id_and_finds_shared_wrong_answers():
    a = log("a", [sample(1, True, "A"), sample(2, False, "B"), sample(3, False, "C")])
    b = log("b", [sample(3, False, "c"), sample(2, False, "D"), sample(1, False, "B")])
    r = compare.compare(a, b)
    assert (r["n"], r["accuracy_a"], r["accuracy_b"]) == (3, pytest.approx(1 / 3), 0.0)
    assert (r["both_right"], r["both_wrong"], r["only_a"], r["only_b"]) == (0, 2, 1, 0)
    assert r["same_wrong"] == [3]  # both answered C, ignoring case
    assert r["p"] == pytest.approx(1.0)


def test_compare_refuses_logs_over_different_items():
    with pytest.raises(ValueError, match="same items"):
        compare.compare(log("a", [sample(1, True, "A")]), log("b", [sample(2, True, "A")]))


def test_accuracy_by_complexity_for_each_model():
    a = log("a", [sample(1, True, "A", "BASE"), sample(2, False, "B", "REASONING")])
    b = log("b", [sample(1, True, "A", "BASE"), sample(2, True, "A", "REASONING")])
    assert compare.by_level(a, b) == {"BASE": (1, 1.0, 1.0), "REASONING": (1, 0.0, 1.0)}


def test_render_shows_paired_counts_the_test_and_shared_wrong_answers():
    a = log("a", [sample(1, True, "A"), sample(2, False, "B")])
    b = log("b", [sample(1, True, "A"), sample(2, False, "b")])
    text = compare.render([compare.compare(a, b)], {"climaqa_mcq": compare.by_level(a, b)})
    assert "| climaqa_mcq | 2 | 0.500 | 0.500 | 1 | 1 | 0 | 0 | 1.000 |" in text
    assert "climaqa_mcq: 1 item (2)" in text


def replied(sid, right, completion, target="hematite"):
    s = sample(sid, right, "")
    s.output, s.target = SimpleNamespace(completion=completion), target
    return s


def test_format_misses_are_wrong_replies_whose_last_line_alone_is_the_key():
    a = log(
        "a",
        [
            replied(1, False, "Some reasoning.\n\n**hematite**"),
            replied(2, False, "magnetite"),
            replied(3, True, "hematite"),
            replied(4, False, "Reasoning.\nmagnetite"),
        ],
    )
    assert compare.format_misses(a) == [1]
    assert compare.multiline(a) == 2
