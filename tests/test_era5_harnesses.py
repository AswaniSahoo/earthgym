import asyncio
import json
from collections import Counter
from types import SimpleNamespace

import pytest
from era5_forecast_v1 import contract
from era5_forecast_v1 import taskset as ts
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from rlenv.era5 import tasks


def test_taskset_loads_every_item_with_its_prompt_and_hidden_fields():
    loaded = ts.ForecastTaskset(ts.ForecastConfig()).load()
    rows = {r["id"]: r for r in ts.records()}
    assert len(loaded) == 720
    for t in loaded:
        row = rows[t.data.id]
        assert t.data.prompt == contract.prompt(row)
        assert (t.data.truth, t.data.climatology) == (row["truth"], row["climatology"])
        assert t.data.persistence == row["history"][-1]


def test_config_can_restrict_the_taskset_to_one_variable():
    loaded = ts.ForecastTaskset(ts.ForecastConfig(variables=["2m_temperature"])).load()
    assert len(loaded) == 360 and {t.data.variable for t in loaded} == {"2m_temperature"}


def test_reward_pays_skill_on_the_last_reply_and_nothing_for_a_copy():
    task = ts.ForecastTaskset(ts.ForecastConfig()).load()[0]
    d = task.data

    def paid(reply):
        return asyncio.run(task.skill(SimpleNamespace(last_reply=reply)))

    assert paid(f"ANSWER: {d.climatology}") == 0.0
    assert paid(f"{d.truth}") == 0.0  # no answer line
    assert paid(f"Reasoning.\nANSWER: {d.truth}") > 0.0


ROW = {
    "id": "2m_temperature/2020-07-01T00/24h/0-0",
    "variable": "2m_temperature",
    "latitude": 47.8125,
    "longitude": 8.4375,
    "init_time": "2020-07-01T00",
    "valid_time": "2020-07-02T00",
    "lead_hours": 24,
    "history_times": ["2020-06-30T18", "2020-07-01T00"],
    "history": [291.0, 292.0],
    "climatology": 289.0,
    "truth": 290.0,
    "hres": 290.4,
    "area_weight": 1.0,
    "floor": 2.0,  # above the better-baseline error, so the item's own floor decides the pay
}


def test_probe_takes_the_first_items_of_each_variable_and_lead_in_item_order():
    rows = [
        {"id": f"{v}/{lead}/{k}", "variable": v, "lead_hours": lead}
        for k in range(3)
        for v in ("a", "b")
        for lead in (24, 48)
    ]
    assert tasks.probe_ids(rows, n=2) == [r["id"] for r in rows[:8]]
    bundled = {r["id"]: (r["variable"], r["lead_hours"]) for r in ts.records()}
    probe = tasks.probe_ids()
    assert len(set(probe)) == 12
    assert sorted(Counter(bundled[i] for i in probe).values()) == [2] * 6


def test_inspect_task_scores_replies_with_the_contract_reward(tmp_path):
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(ROW) + "\n", encoding="utf-8")
    output = ModelOutput.from_content("mockllm/model", "ANSWER: 289.5")
    model = get_model("mockllm/model", custom_outputs=[output])
    log = eval(
        tasks.era5_forecast(path=str(path)), model=model, log_dir=str(tmp_path), display="none"
    )[0]
    # better baseline errs by 1 (climatology), the reply by 0.5, floor 2: (1 - 0.5) / 2
    assert log.results.scores[0].metrics["mean"].value == pytest.approx(0.25)
