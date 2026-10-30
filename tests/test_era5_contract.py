import pytest
from era5_forecast_v1 import contract

# truth 100, persistence 103 (error 3), climatology 98 (error 2): the better baseline errs by 2
CASE = {"truth": 100.0, "persistence": 103.0, "climatology": 98.0, "floor": 0.5}


@pytest.mark.parametrize(
    ("forecast", "want"),
    [(98.0, 0.0), (103.0, 0.0), (99.0, 0.5), (100.0, 1.0), (90.0, 0.0), (None, 0.0)],
)
def test_reward_is_skill_over_the_better_baseline_clipped_to_zero_and_one(forecast, want):
    assert contract.reward(forecast, **CASE) == pytest.approx(want)


def test_floor_caps_the_reward_when_both_baselines_are_nearly_right():
    near = {"truth": 100.0, "persistence": 100.1, "climatology": 100.2, "floor": 0.5}
    assert contract.reward(100.0, **near) == pytest.approx(0.2)  # 0.1 of skill over a 0.5 floor
    assert contract.reward(100.2, **near) == 0.0  # copying climatology still earns nothing


def test_reward_pays_nothing_and_does_not_crash_when_a_baseline_is_exact_and_the_floor_is_zero():
    assert contract.reward(5.0, 5.0, 5.0, 5.0, 0.0) == 0.0


@pytest.mark.parametrize(
    ("reply", "want"),
    [
        ("Pressure falls ahead of the low.\nANSWER: 101325.5", 101325.5),
        ("ANSWER: -3.2 K", -3.2),
        ("**ANSWER: 285**", 285.0),
        ("ANSWER: 280\nOn reflection:\nANSWER: 281.5", 281.5),
        ("ANSWER: about 285", None),
        ("The answer is 285.", None),
        ("ANSWER: 1013 hPa", None),
    ],
)
def test_answer_reads_the_last_answer_line_with_an_optional_unit(reply, want):
    assert contract.answer(reply) == want


ITEM = {
    "variable": "2m_temperature",
    "latitude": 47.8125,
    "longitude": 8.4375,
    "init_time": "2020-07-01T00",
    "valid_time": "2020-07-02T00",
    "lead_hours": 24,
    "history_times": ["2020-06-30T18", "2020-07-01T00"],
    "history": [290.12, 288.47],
    "climatology": 289.05,
    "truth": 291.33,
    "hres": 290.88,
}


def test_prompt_gives_history_and_climatology_but_never_the_truth_or_hres():
    text = contract.prompt(ITEM)
    for shown in ["290.12", "288.47", "289.05", "24 hours", "2020-07-02T00", "K", "ANSWER:"]:
        assert shown in text
    assert "291.33" not in text and "290.88" not in text
