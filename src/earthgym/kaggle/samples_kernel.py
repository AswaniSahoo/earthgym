"""Build the Kaggle kernel for the small-model runs (decision 0025), and the private dataset that
carries the repo to it.

uv run python -m earthgym.kaggle.samples_kernel source <folder> --user <kaggle user>
uv run python -m earthgym.kaggle.samples_kernel kernel <folder> --user <kaggle user> \
    --commit <sha> [--resume]

`source` writes a git bundle of HEAD for `kaggle datasets create -p <folder>` (private unless
told otherwise); `kernel` writes run.py, the template samples_job.py with its config filled in,
and a private GPU kernel's metadata for `kaggle kernels push -p <folder>`. With --resume the
kernel also mounts the earlier sessions' logs (decision 0025).
"""

import argparse
import dataclasses
import json
import subprocess
from pathlib import Path

TEMPLATE = Path(__file__).with_name("samples_job.py")
PLACEHOLDER = 'CONFIG_JSON = "{}"'
DATE = "2026-11-02"  # in every log directory's name, the same across resumed sessions
SLOTS = 32  # parallel requests a server, with 4,096 cache tokens each, as on the laptop
UV = "uv==0.12.18"  # the uv that wrote uv.lock
RELEASE = "https://github.com/ggml-org/llama.cpp/releases/download/b11960/"
LLAMA = [  # build b11960, CUDA 12.8, and its runtime (decision 0022)
    {
        "url": RELEASE + "llama-b11960-bin-ubuntu-cuda-12.8-x64.tar.gz",
        "sha256": "64d57beb9abb637c177c6afb313760a0c0782224cac71e74869eed5b8f9a1ea4",
    },
    {
        "url": RELEASE + "cudart-llama-b11960-bin-ubuntu-cuda-12.8-x64.tar.gz",
        "sha256": "7c4d5974bd39649df649649e5d71950688a70e37aaae00bf11afbb656ea2cc56",
    },
]


@dataclasses.dataclass(frozen=True)
class Model:
    name: str
    repo: str
    revision: str
    file: str
    sha256: str

    @property
    def url(self) -> str:
        return f"https://huggingface.co/{self.repo}/resolve/{self.revision}/{self.file}"


MODELS = [  # the GGUF files of decision 0022
    Model(
        "qwen3.5-2b-q8_0",
        "unsloth/Qwen3.5-2B-GGUF",
        "f6d5376be1edb4d416d56da11e5397a961aca8ae",
        "Qwen3.5-2B-Q8_0.gguf",
        "1b04acba824817554f4ce23639bc8495ff70453b8fcb047900c731521021f2c1",
    ),
    Model(
        "granite-4.0-h-1b-q8_0",
        "ibm-granite/granite-4.0-h-1b-GGUF",
        "c2cb1972f511add21f3bae244990b8ff3a3ffb23",
        "granite-4.0-h-1b-Q8_0.gguf",
        "f29248184ca766350e56e6d161c2a637ad302a6d595e15d4a62cd58327a0ac0e",
    ),
]
ENVS = {  # the shortest replies first, ERA5's long ones last
    "climaqa": [
        "src/earthgym/climaqa/tasks.py@climaqa_mcq",
        "src/earthgym/climaqa/tasks.py@climaqa_cloze",
    ],
    "ibtracs": ["src/earthgym/ibtracs/tasks.py@ibtracs_storm"],
    "heat": ["src/earthgym/heat/tasks.py@heat_basis"],
    "era5": ["src/earthgym/era5/tasks.py@era5_forecast"],
}


def inspect_command(
    model: str, env: str, log_dir: str, sample_ids: list[str] | None = None
) -> list[str]:
    """The laptop runs' Inspect command (decision 0022) as an eval set, which a second run on
    the same log directory resumes; sample_ids limits it to those items."""
    extra = json.dumps({"top_k": 20, "chat_template_kwargs": {"enable_thinking": False}})
    only = ["--sample-id", ",".join(sample_ids)] if sample_ids else []
    return [
        *("uv", "run", "--with", "openai==3.42.1", "inspect", "eval-set", *ENVS[env]),
        *("--model", f"openai-api/llamacpp/{model}", "--epochs", "8"),
        *("--max-connections", str(SLOTS), "--temperature", "0.7", "--top-p", "0.8"),
        *("--extra-body", extra, "--max-tokens", "4096", "--retry-on-error", "3"),
        *("--fail-on-error", "0.05", "--retry-attempts", "3"),
        *only,
        *("--log-dir", log_dir, "--display", "none"),
    ]


def server_command(gguf: str, port: int, per_slot: int = 4096) -> list[str]:
    """llama-server as on the laptop, with twice the slots and per_slot cache tokens each."""
    return [
        *("llama-server", "-m", gguf, "-dev", "CUDA0", "-ngl", "all"),
        *("-c", str(SLOTS * per_slot), "-np", str(SLOTS), "-kvu", "--cache-ram", "1024"),
        *("--host", "127.0.0.1", "--port", str(port)),
    ]


def log_dir(env: str, model: str, part: str = "") -> str:
    return f"/kaggle/working/logs/{DATE}-{env}-{model}-8" + (f"-{part}" if part else "")


def worker(gpu: int, model: Model, commands: dict, per_slot: int) -> dict:
    port = 8080 + gpu
    return (
        {"model": model.name, "gpu": gpu, "port": port, "commands": commands}
        | {"gguf": dataclasses.asdict(model) | {"url": model.url}}
        | {"server": server_command("{gguf}", port, per_slot)}
    )


def plan(name: str) -> list[dict]:
    """The workers of a session. "first": one model a GPU, every environment. "qwen-rest", for
    what the first session left: Qwen3.5-2B on both GPUs, its heat resumed and then the last 188
    ERA5 items on one, the first 460 on the other, with 8,192 cache tokens a slot, the most the
    server grants this model, since the first session's server ran out of KV space (decision
    0025)."""
    if name == "first":
        return [
            worker(
                gpu,
                m,
                {env: inspect_command(m.name, env, log_dir(env, m.name)) for env in ENVS},
                4096,
            )
            for gpu, m in enumerate(MODELS)
        ]
    if name != "qwen-rest":
        raise ValueError(f"no plan {name!r}")
    from era5_forecast_v1.taskset import records

    qwen, ids = MODELS[0], [r["id"] for r in records()]
    era5 = {
        part: inspect_command(qwen.name, "era5", log_dir("era5", qwen.name, part), chunk)
        for part, chunk in (("a", ids[:460]), ("b", ids[460:]))
    }
    heat = inspect_command(qwen.name, "heat", log_dir("heat", qwen.name))
    return [
        worker(0, qwen, {"heat": heat, "era5-b": era5["b"]}, 8192),
        worker(1, qwen, {"era5-a": era5["a"]}, 8192),
    ]


def config(commit: str, name: str = "first") -> dict:
    return {
        "commit": commit,
        "date": DATE,
        "uv": UV,
        "llama": LLAMA,
        "workers": plan(name),
        "deadline_hours": 11.0,  # a Kaggle session stops at 12 hours
    }


def metadata(user: str, resume: bool) -> dict:
    sources = [f"{user}/earthgym-src"] + ([f"{user}/earthgym-small-models-logs"] if resume else [])
    return {
        "id": f"{user}/earthgym-small-models",
        "title": "earthgym small models",
        "code_file": "run.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": sources,
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }


def write(folder: Path, user: str, commit: str, resume: bool, name: str = "first") -> None:
    text = TEMPLATE.read_text("utf-8")
    if text.count(f"\n{PLACEHOLDER}\n") != 1:
        raise ValueError(f"the template must hold the line {PLACEHOLDER!r} once")
    text = text.replace(
        f"\n{PLACEHOLDER}\n", f"\nCONFIG_JSON = {json.dumps(config(commit, name))!r}\n"
    )
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "run.py").write_text(text, "utf-8")
    meta = json.dumps(metadata(user, resume), indent=1) + "\n"
    (folder / "kernel-metadata.json").write_text(meta, "utf-8")


def source(folder: Path, user: str) -> str:
    """A git bundle of HEAD, its commit, and a dataset's metadata; returns the commit."""
    folder.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    bundle = folder / "earthgym.bundle"
    subprocess.run(
        ["git", "bundle", "create", str(bundle), "HEAD"], check=True, capture_output=True
    )
    (folder / "COMMIT").write_text(commit + "\n", "utf-8")
    meta = {"title": "earthgym src", "id": f"{user}/earthgym-src", "licenses": [{"name": "other"}]}
    (folder / "dataset-metadata.json").write_text(json.dumps(meta, indent=1) + "\n", "utf-8")
    return commit


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the small-model kernel or its source.")
    parser.add_argument("what", choices=["source", "kernel"])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--user", required=True)
    parser.add_argument("--commit")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--plan", default="first", help="the session's workers: first, qwen-rest")
    args = parser.parse_args()
    if args.what == "source":
        print(f"bundle of {source(args.folder, args.user)} written to {args.folder}")
        return
    if not args.commit:
        raise SystemExit("kernel needs --commit, the one in the source dataset")
    write(args.folder, args.user, args.commit, args.resume, args.plan)
    print(f"kernel written to {args.folder}")


if __name__ == "__main__":
    main()
