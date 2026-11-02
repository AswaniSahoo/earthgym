import ast
import json
from pathlib import Path

import pytest
from climaqa_v1 import contract
from climaqa_v1.taskset import ClimaqaConfig, ClimaqaTaskset

from earthgym.grpo import kernel, rollout


def reply(text):
    return [{"role": "assistant", "content": text}]  # a conversational completion, as TRL passes it


def test_the_reward_is_the_environments_own_mcq_rule():
    completions = [reply("Reasoning.\nANSWER: B"), reply("ANSWER: C"), reply("B"), reply("")]
    assert rollout.reward(completions=completions, answer=["B"] * 4) == [1.0, 0.0, 0.0, 0.0]
    assert rollout.reward(completions=["ANSWER: A"], answer=["A"], prompts=["q"]) == [1.0]
    with pytest.raises(ValueError):
        rollout.reward(completions=["ANSWER: A"], answer=["A", "B"])


def test_the_items_are_the_tasksets_mcq_items_on_both_splits():
    items = kernel.items()
    for split in ("train", "test"):
        tasks = ClimaqaTaskset(ClimaqaConfig(kinds=["mcq"], split=split)).load()
        mine = [(i["id"], i["prompt"], i["answer"]) for i in items if i["split"] == split]
        assert mine == [(t.data.id, t.data.prompt, t.data.answer) for t in tasks]
    assert len(items) == len({i["id"] for i in items})


def constants(script: str) -> dict:
    """The script's top-level constant assignments."""
    tree = ast.parse(script)
    return {
        n.targets[0].id: ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
    }


def test_the_kernel_is_private_on_a_t4_and_carries_the_repos_own_code(tmp_path):
    config = kernel.Config(slug="earthgym-grpo-smoke", steps=10)
    kernel.write(tmp_path, config, user="someone")
    meta = json.loads((tmp_path / "kernel-metadata.json").read_text("utf-8"))
    assert meta["id"] == "someone/earthgym-grpo-smoke" and meta["title"] == "earthgym grpo smoke"
    assert (meta["is_private"], meta["enable_gpu"], meta["enable_internet"]) == (True, True, True)
    assert (meta["machine_shape"], meta["kernel_type"], meta["code_file"]) == (
        "NvidiaTeslaT4",
        "script",
        "train.py",
    )
    script = (tmp_path / "train.py").read_text("utf-8")
    compile(script, "train.py", "exec")
    c = constants(script)
    assert c["CONTRACT_SOURCE"] == Path(contract.__file__).read_text("utf-8")
    assert c["ROLLOUT_SOURCE"] == Path(rollout.__file__).read_text("utf-8")
    assert json.loads(c["ITEMS_JSON"]) == kernel.items()
    assert json.loads(c["CONFIG_JSON"]) == json.loads(json.dumps(kernel.asdict(config)))


def test_the_default_config_samples_as_the_small_model_runs_did():
    c = kernel.Config()
    assert (c.model, c.revision) == ("Qwen/Qwen3.5-2B", "15852e8c16360a2fea060d615a32b45270f8a8fc")
    assert (c.temperature, c.top_p, c.top_k) == (0.7, 0.8, 20)  # decision 0022's settings
    assert c.num_generations == 8 and c.enable_thinking is False


def test_the_run_preset_pins_what_the_smoke_resolved_and_samples_the_held_out_split():
    run, smoke = kernel.PRESETS["run"], kernel.PRESETS["smoke"]
    assert smoke == kernel.Config()
    assert run.steps == 250 and run.save_adapter and run.slug == "earthgym-grpo"
    # the train and the held-out reward before and after: every test item, as many train items
    assert (run.eval_splits, run.eval_items, run.eval_samples) == (("train", "test"), 52, 8)
    assert sum(i["split"] == "test" for i in kernel.items()) == 52
    assert set(run.pip) == {  # reports/grpo/2026-11-02-smoke.md, Packages
        "unsloth==2026.10.11",
        "unsloth_zoo==2026.10.11",
        "trl==1.15.0",
        "transformers==5.16.1",
        "peft==0.20.0",
        "accelerate==1.14.0",
        "datasets==4.8.5",
        "bitsandbytes==0.50.2",
        "huggingface_hub==1.29.0",
    }
    a, b = kernel.asdict(run), kernel.asdict(smoke)
    changed = {f for f in a if a[f] != b[f]}  # the rest as in the smoke, so its timings apply
    assert changed == {
        "slug",
        "pip",
        "steps",
        "eval_items",
        "eval_samples",
        "save_adapter",
    }
