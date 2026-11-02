import asyncio
import json
from collections import Counter
from types import SimpleNamespace

import pytest
import verifiers.v1 as vf
from ibtracs_storm_v1 import contract
from ibtracs_storm_v1 import taskset as ts
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.tool import ToolDef
from mcp.server.mcpserver import MCPServer

from earthgym.ibtracs import tasks

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

    right = min(contract._roundings(task.data.key)) / 10  # the key rounded to one decimal
    assert paid(f"Summing.\nANSWER: {right:.1f}") == 1.0
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


def test_both_harnesses_pay_the_same_on_every_item():
    for task in ts.StormTaskset(ts.StormConfig()).load():
        d = task.data
        for reply in (f"ANSWER: {d.key}", f"ANSWER: {d.key + 2}", "no answer"):
            paid = asyncio.run(task.exact(SimpleNamespace(last_reply=reply)))
            assert paid == contract.reward(d.question, contract.answer(reply), d.key)


def test_taskset_tools_mode_puts_the_rows_behind_one_query_tool():
    config = ts.StormConfig(tools=True)
    assert config.task.tools and not ts.StormConfig().task.tools  # what Task.toolsets reads
    loaded = ts.StormTaskset(config).load()
    rows = {r["id"]: r for r in ts.records()}
    assert len(loaded) == 300
    for t in loaded:
        assert t.data.prompt == contract.tools_prompt(rows[t.data.id])
        assert [list(row) for row in t.data.rows] == rows[t.data.id]["rows"]
        assert asyncio.run(t.validate(None))  # the gold check
    (server,) = type(loaded[0]).toolsets(loaded[0].config)  # as each rollout asks
    assert isinstance(server, ts.TrackToolset) and server.server_name == ""  # no prefix
    default = ts.StormTaskset(ts.StormConfig()).load()
    assert type(default[0]).toolsets(default[0].config) == []
    assert all(t.data.rows is None for t in default)


def test_query_tool_serves_its_own_storm_to_the_model():
    server = ts.TrackToolset(vf.ToolsetConfig())

    async def serve():
        await server.setup_task(ts.to_data(ROW, tools=True))  # as the /task channel hands it
        mcp = MCPServer("track")
        server.register(mcp)
        sql = "SELECT count(*), sum(wind) FROM track WHERE status = 'HU'"
        return await mcp.list_tools(), await mcp.call_tool("query", {"sql": sql})

    (tool,), result = asyncio.run(serve())
    assert tool.name == "query" and list(tool.input_schema["properties"]) == ["sql"]
    assert result.content[0].text == "count(*) | sum(wind)\n2 | 145"


def test_both_harnesses_offer_the_same_query_tool():
    tool = ToolDef(tasks.query())
    assert tool.name == "query" and list(tool.parameters.properties) == ["sql"]
    assert tool.description == ts.TrackToolset.query.__doc__


def eval_tools_mode(tmp_path, outputs):
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(ROW) + "\n", encoding="utf-8")
    model = get_model("mockllm/model", custom_outputs=outputs)
    task = tasks.ibtracs_storm(path=str(path), tools=True)
    return eval(task, model=model, log_dir=str(tmp_path), display="none")[0]


@pytest.mark.parametrize(  # a bare number is what the probe's model submitted (decision 0023)
    ("answer", "expected"), [("ANSWER: 6", 1.0), ("ANSWER: 12", 0.0), ("6", 1.0), ("12", 0.0)]
)
def test_inspect_tools_mode_scores_the_final_reply_after_a_query(tmp_path, answer, expected):
    hours = "SELECT 6 * count(*) FROM track WHERE status = 'HU' AND substr(time, 7, 2) % 6 = 0"
    log = eval_tools_mode(
        tmp_path,
        [
            ModelOutput.for_tool_call("mockllm/model", "query", {"sql": hours}),
            ModelOutput.from_content("mockllm/model", answer),
        ],
    )
    assert log.results.scores[0].metrics["mean"].value == pytest.approx(expected)
    sample = log.samples[0]
    assert sample.input == contract.tools_prompt(ROW)
    (reply,) = [m for m in sample.messages if m.role == "tool" and m.function == "query"]
    assert reply.text == "6 * count(*)\n6"  # read from this sample's rows in the store


def test_inspect_tools_mode_sends_the_prompt_and_one_tool_as_verifiers_does(tmp_path):
    # no agent system prompt and no submit tool (review of phase 6, M1): the user prompt, the
    # query tool, and the final reply scored, as verifiers' null harness sends it
    log = eval_tools_mode(
        tmp_path,
        [
            ModelOutput.for_tool_call("mockllm/model", "query", {"sql": "SELECT 1"}),
            ModelOutput.from_content("mockllm/model", "ANSWER: 6"),
        ],
    )
    sample = log.samples[0]
    assert [m.role for m in sample.messages] == ["user", "assistant", "tool", "assistant"]
    offered = [e.tools for e in sample.events if e.event == "model"]
    assert [[t.name for t in tools] for tools in offered] == [["query"], ["query"]]


def test_inspect_tools_mode_stops_a_model_at_the_turn_limit_of_verifiers(tmp_path):
    def queries():
        while True:
            yield ModelOutput.for_tool_call("mockllm/model", "query", {"sql": "SELECT 1"})

    log = eval_tools_mode(tmp_path, queries())
    sample = log.samples[0]
    assert sample.limit.type == "turn"
    assert sum(m.role == "assistant" for m in sample.messages) == tasks.TURN_LIMIT == 14
    assert log.results.scores[0].metrics["mean"].value == 0.0


def test_taskset_tools_mode_pays_a_final_reply_that_is_the_number_alone():
    tools = ts.StormTaskset(ts.StormConfig(tools=True)).load()[0]
    plain = ts.StormTaskset(ts.StormConfig()).load()[0]
    gold = contract.gold(tools.data.question, tools.data.key).removeprefix("ANSWER: ")
    assert asyncio.run(tools.exact(SimpleNamespace(last_reply=gold))) == 1.0
    assert asyncio.run(plain.exact(SimpleNamespace(last_reply=gold))) == 0.0
