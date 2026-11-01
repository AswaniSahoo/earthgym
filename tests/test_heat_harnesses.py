import asyncio
import json
from collections import Counter
from types import SimpleNamespace

import pytest
from heat_basis_v1 import contract
from heat_basis_v1 import taskset as ts
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from rlenv.heat import tasks

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


def test_taskset_loads_every_item_with_its_prompt_and_key():
    loaded = ts.HeatTaskset(ts.HeatConfig()).load()
    rows = {r["id"]: r for r in ts.records()}
    assert len(loaded) == 300
    for t in loaded:
        assert t.data.prompt == contract.prompt(rows[t.data.id])
        assert t.data.key == rows[t.data.id]["key"]


def test_config_can_restrict_the_taskset_to_one_question():
    loaded = ts.HeatTaskset(ts.HeatConfig(questions=["missed_days"])).load()
    assert len(loaded) == 100 and {t.data.question for t in loaded} == {"missed_days"}


def test_reward_pays_one_for_the_exact_count():
    task = ts.HeatTaskset(ts.HeatConfig()).load()[0]

    def paid(reply):
        return asyncio.run(task.exact(SimpleNamespace(last_reply=reply)))

    assert paid(f"Counting.\nANSWER: {task.data.key}") == 1.0
    assert paid(f"ANSWER: {task.data.key + 1}") == 0.0


def test_probe_takes_the_first_items_of_each_question():
    assert Counter(i.split("/")[0] for i in tasks.probe_ids(n=2)) == {
        "trigger_days": 2,
        "events": 2,
        "missed_days": 2,
    }


@pytest.mark.parametrize(("reply", "expected"), [("ANSWER: 0", 1.0), ("ANSWER: 1", 0.0)])
def test_inspect_task_scores_replies_with_the_contract_reward(tmp_path, reply, expected):
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(ITEM) + "\n", encoding="utf-8")
    out = ModelOutput.from_content("mockllm/model", reply)
    model = get_model("mockllm/model", custom_outputs=[out])
    task = tasks.heat_basis(path=str(path))
    log = eval(task, model=model, log_dir=str(tmp_path), display="none")[0]
    assert log.results.scores[0].metrics["mean"].value == pytest.approx(expected)


def test_terms_only_reaches_both_harnesses(tmp_path):
    loaded = ts.HeatTaskset(ts.HeatConfig(rules=False)).load()
    assert len(loaded) == 300 and not any("Rule." in t.data.prompt for t in loaded)
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(ITEM) + "\n", encoding="utf-8")
    sample = tasks.samples(str(path), rules=False)[0]
    assert sample.input == contract.prompt(ITEM, rules=False)


def test_both_harnesses_pay_the_same_on_every_item():
    for task in ts.HeatTaskset(ts.HeatConfig()).load():
        d = task.data
        for reply in (f"ANSWER: {d.key}", f"ANSWER: {d.key + 1}", "no answer"):
            paid = asyncio.run(task.exact(SimpleNamespace(last_reply=reply)))
            assert paid == contract.reward(contract.answer(reply), d.key)
