import asyncio
import json
from collections import Counter
from types import SimpleNamespace

import pytest
from ibtracs_storm_v1 import contract
from ibtracs_storm_v1 import taskset as ts
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from rlenv.ibtracs import tasks

ROW = {
    "id": "hurricane_hours/X",
    "sid": "X",
    "season": 2021,
    "name": "TEST",
    "question": "hurricane_hours",
    "rows": [["2021-08-26 12:00:00", "HU", 70, 990], ["2021-08-26 15:00:00", "HU", 75, 988]],
    "key": 6,
}


def test_taskset_loads_every_item_with_its_prompt_and_key():
    loaded = ts.StormTaskset(ts.StormConfig()).load()
    rows = {r["id"]: r for r in ts.records()}
    assert len(loaded) == 300
    for t in loaded:
        assert t.data.prompt == contract.prompt(rows[t.data.id])
        assert (t.data.question, t.data.key) == (
            rows[t.data.id]["question"],
            rows[t.data.id]["key"],
        )


def test_config_can_restrict_the_taskset_to_one_question():
    loaded = ts.StormTaskset(ts.StormConfig(questions=["ace"])).load()
    assert len(loaded) == 100 and {t.data.question for t in loaded} == {"ace"}


def test_reward_pays_one_for_the_right_last_reply():
    task = next(t for t in ts.StormTaskset(ts.StormConfig()).load() if t.data.question == "ace")

    def paid(reply):
        return asyncio.run(task.exact(SimpleNamespace(last_reply=reply)))

    assert paid(f"Summing.\nANSWER: {task.data.key}") == 1.0
    assert paid(f"ANSWER: {task.data.key + 1}") == 0.0
    assert paid(f"{task.data.key}") == 0.0  # no answer line


def test_probe_takes_the_first_items_of_each_question():
    probe = tasks.probe_ids(n=2)
    questions = Counter(i.split("/")[0] for i in probe)
    assert questions == {"ace": 2, "peak_category": 2, "hurricane_hours": 2}


@pytest.mark.parametrize(("reply", "expected"), [("ANSWER: 6", 1.0), ("ANSWER: 12", 0.0)])
def test_inspect_task_scores_replies_with_the_contract_reward(tmp_path, reply, expected):
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(ROW) + "\n", encoding="utf-8")
    model = get_model(
        "mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", reply)]
    )
    log = eval(
        tasks.ibtracs_storm(path=str(path)), model=model, log_dir=str(tmp_path), display="none"
    )[0]
    assert log.results.scores[0].metrics["mean"].value == pytest.approx(expected)


def test_rules_hidden_reaches_both_harnesses(tmp_path):
    hidden = ts.StormTaskset(ts.StormConfig(rules=False)).load()
    assert len(hidden) == 300 and not any("Rule." in t.data.prompt for t in hidden)
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(ROW) + "\n", encoding="utf-8")
    sample = tasks.samples(str(path), rules=False)[0]
    assert "Rule." not in sample.input and sample.input == contract.prompt(ROW, rules=False)
