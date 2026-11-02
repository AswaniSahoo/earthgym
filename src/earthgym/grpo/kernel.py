"""Build the Kaggle kernel for the Phase 7 GRPO run (decision 0024).

uv run python -m earthgym.grpo.kernel <folder> --user <kaggle user> [--steps N] [--slug S]

The folder gets train.py, the template train_kernel.py with its four constants filled from the
repo, and a private GPU kernel's kernel-metadata.json, ready for `kaggle kernels push -p`.
"""

import argparse
import dataclasses
import json
from dataclasses import asdict
from pathlib import Path

from climaqa_v1 import contract
from climaqa_v1.taskset import ClimaqaConfig, ClimaqaTaskset

from earthgym.grpo import rollout

TEMPLATE = Path(__file__).with_name("train_kernel.py")
PLACEHOLDERS = {
    "CONFIG_JSON": 'CONFIG_JSON = "{}"',
    "ITEMS_JSON": 'ITEMS_JSON = "[]"',
    "CONTRACT_SOURCE": 'CONTRACT_SOURCE = ""',
    "ROLLOUT_SOURCE": 'ROLLOUT_SOURCE = ""',
}


@dataclasses.dataclass(frozen=True)
class Config:
    slug: str = "earthgym-grpo-smoke"
    model: str = "Qwen/Qwen3.5-2B"
    revision: str = "15852e8c16360a2fea060d615a32b45270f8a8fc"
    pip: tuple[str, ...] = ("unsloth==2026.10.11",)
    steps: int = 10
    seed: int = 3407
    learning_rate: float = 5e-5
    lora_rank: int = 16
    target_modules: tuple[str, ...] = (
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    )
    num_generations: int = 8
    per_device_train_batch_size: int = 8  # one prompt and its 8 completions a step
    gradient_accumulation_steps: int = 1
    max_completion_length: int = 1024
    max_seq_length: int = 2048
    temperature: float = 0.7  # the sampling of the small-model runs (decision 0022)
    top_p: float = 0.8
    top_k: int = 20
    enable_thinking: bool = False
    eval_splits: tuple[str, ...] = ("train", "test")
    eval_items: int | None = 4  # the first items of each split; None: all of them
    eval_samples: int = 2
    save_adapter: bool = False


def items() -> list[dict]:
    """climaqa-v1's MCQ items as its taskset loads them, train split first: id, prompt, key."""
    out = []
    for split in ("train", "test"):
        for task in ClimaqaTaskset(ClimaqaConfig(kinds=["mcq"], split=split)).load():
            d = task.data
            out.append({"id": d.id, "prompt": d.prompt, "answer": d.answer, "split": split})
    return out


def script(config: Config) -> str:
    """The kernel's train.py: the template with the config, the items and the repo's own
    contract and reward wrapper written into its constants."""
    text = TEMPLATE.read_text("utf-8")
    values = {
        "CONFIG_JSON": json.dumps(asdict(config)),
        "ITEMS_JSON": json.dumps(items()),
        "CONTRACT_SOURCE": Path(contract.__file__).read_text("utf-8"),
        "ROLLOUT_SOURCE": Path(rollout.__file__).read_text("utf-8"),
    }
    for name, line in PLACEHOLDERS.items():
        if text.count(f"\n{line}\n") != 1:
            raise ValueError(f"the template must hold the line {line!r} once")
        text = text.replace(f"\n{line}\n", f"\n{name} = {values[name]!r}\n")
    return text


def metadata(config: Config, user: str) -> dict:
    """A private script kernel on Kaggle's T4 x2 machine, with internet for the installs and
    the model download (kaggle-cli docs/kernels_metadata.md)."""
    return {
        "id": f"{user}/{config.slug}",
        "title": config.slug.replace("-", " "),
        "code_file": "train.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }


def write(folder: Path, config: Config, user: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "train.py").write_text(script(config), "utf-8")
    meta = json.dumps(metadata(config, user), indent=1) + "\n"
    (folder / "kernel-metadata.json").write_text(meta, "utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the GRPO kernel for Kaggle.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--user", required=True, help="the Kaggle user that owns the kernel")
    parser.add_argument("--slug", default=Config.slug)
    parser.add_argument("--steps", type=int, default=Config.steps)
    args = parser.parse_args()
    config = Config(slug=args.slug, steps=args.steps)
    write(args.folder, config, args.user)
    print(f"kernel {args.user}/{config.slug} written to {args.folder}")


if __name__ == "__main__":
    main()
