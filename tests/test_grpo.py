import ast
import json
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from climaqa_v1 import contract
from climaqa_v1.taskset import ClimaqaConfig, ClimaqaTaskset

from earthgym.grpo import kernel, rollout, train_kernel


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


class StubTokenizer:
    """Qwen3.5-2B's two end tokens: the chat turn ends on 248046, the padding is 248044."""

    eos_token_id, pad_token_id = 248046, 248044
    WORDS = {1: "Reasoning.", 2: "ANSWER: A", 7: "text after the turn ended"}

    def apply_chat_template(self, messages, **_):
        return messages[0]["content"]

    def __call__(self, text, return_tensors):
        class Inputs(dict):
            def to(self, device):
                return self

        return Inputs(input_ids=np.zeros((1, 3), dtype=int))

    def decode(self, ids, skip_special_tokens):
        return "\n".join(self.WORDS[i] for i in ids if i in self.WORDS)


class StubModel:
    """No generation_config: `sample` must not take its stop tokens from there (phase 7, H1)."""

    def generate(self, **kwargs):
        self.kwargs = kwargs
        return np.array(
            [
                [
                    0,
                    0,
                    0,
                    1,
                    2,
                    248046,
                    7,
                    7,
                    248044,
                ],  # the turn ends; what follows is not the reply
                [0, 0, 0, 1, 1, 1, 1, 1, 1],  # no end token within the cap
            ]
        )


def test_a_sampled_reply_stops_at_the_end_of_the_turn_and_keeps_its_text(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(no_grad=nullcontext))
    tokenizer, model = StubTokenizer(), StubModel()
    stop = train_kernel.stop_tokens(tokenizer)
    assert stop == [248044, 248046]
    config = {"enable_thinking": False, "temperature": 0.7, "top_p": 0.8, "top_k": 20}
    config["max_completion_length"] = 6
    replies = []
    item = {"id": "gold/mcq/1", "prompt": "q", "answer": "A"}
    rows = train_kernel.sample(model, tokenizer, [item], config, 2, stop, replies)
    assert model.kwargs["eos_token_id"] == stop
    assert model.kwargs["pad_token_id"] == 248044
    first, second = rows
    assert (first["reward"], first["answer"], first["tokens"], first["cut"]) == (1.0, "A", 2, False)
    assert (second["reward"], second["tokens"], second["cut"]) == (0.0, 6, True)
    assert replies[0] == {"id": "gold/mcq/1", "epoch": 1, "text": "Reasoning.\nANSWER: A"}
    assert "text" not in first  # the rows go to git; the texts stay in the kernel's output


def test_the_resample_preset_reuses_the_saved_adapter_for_both_samplings(tmp_path):
    run, again = kernel.PRESETS["run"], kernel.PRESETS["resample"]
    assert again.adapter and not run.adapter and again.slug == "earthgym-grpo-resample"
    assert (again.eval_splits, again.eval_items, again.eval_samples) == (
        run.eval_splits,
        run.eval_items,
        run.eval_samples,
    )
    assert (again.pip, again.revision, again.seed) == (run.pip, run.revision, run.seed)
    kernel.write(tmp_path, again, user="someone")
    meta = json.loads((tmp_path / "kernel-metadata.json").read_text("utf-8"))
    assert meta["dataset_sources"] == ["someone/earthgym-grpo-adapter"] and meta["is_private"]
    compile((tmp_path / "train.py").read_text("utf-8"), "train.py", "exec")
    assert kernel.metadata(run, "someone")["dataset_sources"] == []
