import pytest
from climaqa_v1 import taskset as ts


@pytest.mark.parametrize(
    ("reply", "key", "expected"),
    [
        ("B", "B", 1.0),
        ("ANSWER: C", "C", 1.0),
        ("A first, then D", "D", 1.0),
        ("It is a B", "B", 1.0),
        ("b", "B", 0.0),
        ("", "B", 0.0),
    ],
)
def test_mcq_reward_reads_the_last_capital_letter(reply, key, expected):
    assert ts.mcq_reward(reply, key) == expected


def test_cloze_reward_ignores_case_and_punctuation_but_not_meaning():
    assert ts.cloze_reward("Evaporation.", "evaporation") == 1.0
    assert ts.cloze_reward("condensation", "evaporation") == 0.0
    assert ts.cloze_reward("", "") == 0.0


def test_taskset_loads_the_bundled_set_and_keys_point_at_their_text():
    first = ts.ClimaqaTaskset(ts.ClimaqaConfig()).load()
    again = ts.ClimaqaTaskset(ts.ClimaqaConfig()).load()
    mcq = [t for t in first if t.data.kind == "mcq"]
    assert (len(first), len(mcq)) == (350, 222)
    assert [t.data.prompt for t in first] == [t.data.prompt for t in again]
    for task in mcq:
        assert f"{task.data.answer}) {task.data.key_text}" in task.data.prompt


def test_config_can_restrict_the_taskset_to_one_kind():
    cloze = ts.ClimaqaTaskset(ts.ClimaqaConfig(kinds=["cloze"])).load()
    assert len(cloze) == 128 and {t.data.kind for t in cloze} == {"cloze"}
