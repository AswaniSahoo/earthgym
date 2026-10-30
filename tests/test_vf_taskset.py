import asyncio
from types import SimpleNamespace

from climaqa_v1 import contract
from climaqa_v1 import taskset as ts


def test_taskset_loads_the_bundled_set_with_contract_prompts():
    tasks = ts.ClimaqaTaskset(ts.ClimaqaConfig()).load()
    mcq = [t for t in tasks if t.data.kind == "mcq"]
    assert (len(tasks), len(mcq)) == (350, 222)
    for task in mcq:
        assert f"{task.data.answer}) {task.data.key_text}" in task.data.prompt
        assert "ANSWER: X" in task.data.prompt


def test_config_can_restrict_the_taskset_to_one_kind():
    cloze = ts.ClimaqaTaskset(ts.ClimaqaConfig(kinds=["cloze"])).load()
    assert len(cloze) == 128 and {t.data.kind for t in cloze} == {"cloze"}
    assert cloze[0].data.prompt == contract.cloze_prompt(cloze[0].data.question)


def test_reward_uses_the_contract_on_the_last_reply():
    task = ts.ClimaqaTaskset(ts.ClimaqaConfig(kinds=["mcq"])).load()[0]
    right = SimpleNamespace(last_reply=f"Reasoning.\nANSWER: {task.data.answer}")
    wrong = SimpleNamespace(last_reply=task.data.answer)  # bare letter breaks the format
    assert asyncio.run(task.correct(right)) == 1.0
    assert asyncio.run(task.correct(wrong)) == 0.0
