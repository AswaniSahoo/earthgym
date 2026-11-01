from heat_basis_v1 import contract

ITEM = {
    "id": "events/A/B/2020/110/3",
    "question": "events",
    "index": "A",
    "site": "B",
    "index_name": "Scottsdale Municipal Airport",
    "site_name": "Phoenix Sky Harbor",
    "year": 2020,
    "threshold": 110,
    "k": 3,
    "dates": ["05-01", "05-02"],
    "index_f": [110, None],
    "site_f": [112, 108],
    "key": 0,
}


def test_prompt_shows_both_stations_by_name_with_dashes_and_no_year():
    text = contract.prompt(ITEM)
    assert "05-01 | 110 | 112" in text and "05-02 | - | 108" in text
    assert "Scottsdale Municipal Airport" in text and "Phoenix Sky Harbor" in text
    assert "2020" not in text
    assert text.rstrip().endswith("The last line of your response must be 'ANSWER: <number>'.")


def test_each_question_carries_its_own_rule_with_its_numbers():
    events = contract.prompt(ITEM)
    assert "at or above 110 F" in events and "at least 3 consecutive trigger days" in events
    assert "pays once" in events and "ends a run" in events
    days = contract.prompt(ITEM | {"question": "trigger_days", "k": None})
    assert "at or above 110 F" in days and "consecutive" not in days
    missed = contract.prompt(ITEM | {"question": "missed_days", "k": None})
    assert "insured site" in missed and "a missing index value counts as not" in missed


def test_answer_takes_the_last_answer_line_and_the_reward_is_exact():
    assert contract.answer("Counting.\nANSWER: 12\nANSWER: 13.") == 13.0
    assert contract.answer("13 days") is None
    assert contract.reward(13.0, 13) == 1.0
    assert contract.reward(12.0, 13) == contract.reward(None, 13) == 0.0
