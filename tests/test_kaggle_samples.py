import ast
import json
import subprocess

import pytest

from earthgym.kaggle import samples_kernel as k


def test_every_model_runs_every_environment_with_the_tasks_of_the_laptop_runs():
    assert [m.name for m in k.MODELS] == ["qwen3.5-2b-q8_0", "granite-4.0-h-1b-q8_0"]
    assert k.ENVS == {
        "climaqa": [
            "src/earthgym/climaqa/tasks.py@climaqa_mcq",
            "src/earthgym/climaqa/tasks.py@climaqa_cloze",
        ],
        "ibtracs": ["src/earthgym/ibtracs/tasks.py@ibtracs_storm"],
        "heat": ["src/earthgym/heat/tasks.py@heat_basis"],
        "era5": ["src/earthgym/era5/tasks.py@era5_forecast"],
    }


def test_the_models_and_the_runner_are_the_pins_of_decision_0022():
    qwen, granite = k.MODELS
    assert (qwen.repo, qwen.revision, qwen.file) == (
        "unsloth/Qwen3.5-2B-GGUF",
        "f6d5376be1edb4d416d56da11e5397a961aca8ae",
        "Qwen3.5-2B-Q8_0.gguf",
    )
    assert qwen.sha256 == "1b04acba824817554f4ce23639bc8495ff70453b8fcb047900c731521021f2c1"
    assert (granite.repo, granite.revision) == (
        "ibm-granite/granite-4.0-h-1b-GGUF",
        "c2cb1972f511add21f3bae244990b8ff3a3ffb23",
    )
    assert granite.sha256 == "f29248184ca766350e56e6d161c2a637ad302a6d595e15d4a62cd58327a0ac0e"
    assert {a["sha256"] for a in k.LLAMA} == {
        "64d57beb9abb637c177c6afb313760a0c0782224cac71e74869eed5b8f9a1ea4",
        "7c4d5974bd39649df649649e5d71950688a70e37aaae00bf11afbb656ea2cc56",
    }
    assert all(a["url"].startswith(k.RELEASE) for a in k.LLAMA)


def test_the_inspect_command_samples_as_the_laptop_runs_did_and_resumes_as_an_eval_set():
    cmd = k.inspect_command("qwen3.5-2b-q8_0", "climaqa", "logs/x")
    assert cmd[:6] == ["uv", "run", "--with", "openai==3.42.1", "inspect", "eval-set"]
    assert cmd[6:8] == k.ENVS["climaqa"]
    flags = dict(zip(cmd[8::2], cmd[9::2], strict=False))
    assert flags["--model"] == "openai-api/llamacpp/qwen3.5-2b-q8_0"
    assert (flags["--epochs"], flags["--temperature"], flags["--top-p"]) == ("8", "0.7", "0.8")
    assert json.loads(flags["--extra-body"]) == {
        "top_k": 20,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    assert (flags["--max-tokens"], flags["--fail-on-error"]) == ("4096", "0.05")
    assert flags["--max-connections"] == str(k.SLOTS) and flags["--log-dir"] == "logs/x"


def test_the_server_keeps_four_thousand_tokens_a_slot_on_its_own_gpu():
    cmd = k.server_command("/m.gguf", 8081)
    assert cmd[cmd.index("-c") + 1] == str(k.SLOTS * 4096) and cmd[cmd.index("-np") + 1] == "32"
    assert "-kvu" in cmd and cmd[cmd.index("-dev") + 1] == "CUDA0"  # one GPU visible a server
    assert cmd[cmd.index("--port") + 1] == "8081" and cmd[cmd.index("--host") + 1] == "127.0.0.1"


def constants(script: str) -> dict:
    tree = ast.parse(script)
    return {
        n.targets[0].id: ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
    }


def test_the_kernel_is_private_on_two_t4s_and_mounts_the_source_and_any_earlier_logs(tmp_path):
    k.write(tmp_path, user="someone", commit="abc123", resume=True)
    meta = json.loads((tmp_path / "kernel-metadata.json").read_text("utf-8"))
    assert meta["id"] == "someone/earthgym-small-models"
    assert (meta["is_private"], meta["enable_gpu"], meta["enable_internet"]) == (True, True, True)
    assert meta["machine_shape"] == "NvidiaTeslaT4"
    assert meta["dataset_sources"] == ["someone/earthgym-src", "someone/earthgym-small-models-logs"]
    script = (tmp_path / "run.py").read_text("utf-8")
    compile(script, "run.py", "exec")
    config = json.loads(constants(script)["CONFIG_JSON"])
    assert config["commit"] == "abc123" and config["deadline_hours"] < 12
    assert [j["model"] for j in config["workers"]] == [m.name for m in k.MODELS]
    assert config["workers"][0]["gpu"] != config["workers"][1]["gpu"]
    assert config["workers"][0]["commands"]["climaqa"] == k.inspect_command(
        "qwen3.5-2b-q8_0", "climaqa", "/kaggle/working/logs/2026-11-02-climaqa-qwen3.5-2b-q8_0-8"
    )
    k.write(tmp_path / "fresh", user="someone", commit="abc123", resume=False)
    fresh = json.loads((tmp_path / "fresh" / "kernel-metadata.json").read_text("utf-8"))
    assert fresh["dataset_sources"] == ["someone/earthgym-src"]


def test_the_source_dataset_is_a_bundle_of_the_commit_and_private_by_default(tmp_path):
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"], capture_output=True, text=True
    ).stdout.strip()
    if shallow == "true":  # CI checks out one commit, which git cannot bundle with its history
        pytest.skip("a shallow clone")
    commit = k.source(tmp_path, user="someone")
    meta = json.loads((tmp_path / "dataset-metadata.json").read_text("utf-8"))
    assert meta["id"] == "someone/earthgym-src" and "isPrivate" not in meta  # the CLI's default
    heads = subprocess.run(
        ["git", "bundle", "list-heads", str(tmp_path / "earthgym.bundle")],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert commit in heads and (tmp_path / "COMMIT").read_text().strip() == commit
