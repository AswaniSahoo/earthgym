"""GRPO with a LoRA on one Kaggle T4 (decision 0024).

Built by earthgym.grpo.kernel, which fills the four constants below: the run's config, the
climaqa-v1 MCQ items with their split, the environment's own answer contract and the reward
wrapper (earthgym/grpo/rollout.py), each as the repo holds it. The script installs the pinned
packages, samples the items before training, trains, samples them again, and writes everything
it measured to /kaggle/working/metrics.json as it goes.
"""

import json
import os
import subprocess
import sys
import time
import traceback
from importlib import metadata
from pathlib import Path

CONFIG_JSON = "{}"
ITEMS_JSON = "[]"
CONTRACT_SOURCE = ""
ROLLOUT_SOURCE = ""

OUT = Path("/kaggle/working")
RECORD = {"events": []}
START = time.time()
PACKAGES = [
    "torch",
    "transformers",
    "trl",
    "peft",
    "accelerate",
    "datasets",
    "unsloth",
    "unsloth_zoo",
    "bitsandbytes",
    "triton",
    "huggingface_hub",
]


def note(event: str, **fields) -> None:
    """Record one step of the run with the seconds since the start, and save the record."""
    RECORD["events"].append({"seconds": round(time.time() - START, 1), "event": event, **fields})
    (OUT / "metrics.json").write_text(json.dumps(RECORD, indent=1, default=str), "utf-8")
    print(event, fields, flush=True)


def libraries() -> None:
    """Write the environment's contract and the reward wrapper where Python imports them."""
    lib = OUT / "lib"
    (lib / "climaqa_v1").mkdir(parents=True, exist_ok=True)
    (lib / "climaqa_v1" / "__init__.py").write_text("", "utf-8")
    (lib / "climaqa_v1" / "contract.py").write_text(CONTRACT_SOURCE, "utf-8")
    (lib / "rollout.py").write_text(ROLLOUT_SOURCE, "utf-8")
    sys.path.insert(0, str(lib))


def versions() -> dict:
    found = {"python": sys.version.split()[0]}
    for name in PACKAGES:
        try:
            found[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            found[name] = None
    return found


def find(name: str) -> Path | None:
    """A file under /kaggle/input, wherever Kaggle mounted its dataset."""
    return next(Path("/kaggle/input").rglob(name), None)


def stop_tokens(tokenizer) -> list[int]:
    """The tokens a reply stops on, fixed once from the tokenizer: the chat turn's end and the
    padding. The model's own config names only the padding, and the trainer widens its generation
    config when it is built, so reading that config lets two samplings stop on different tokens
    (docs/reviews/phase-7-grpo.md, H1)."""
    return sorted({tokenizer.eos_token_id, tokenizer.pad_token_id} - {None})


def sample(
    model,
    tokenizer,
    items: list[dict],
    config: dict,
    k: int,
    stop: list[int],
    replies: list[dict] | None = None,
) -> list[dict]:
    """k sampled replies to each item, with the settings of the small-model runs (decision
    0022), each with its reward, its length in tokens and whether it stopped at the cap. The
    reply texts go to `replies`, for the kernel's output and not for git."""
    import torch
    from climaqa_v1 import contract

    ends = set(stop)
    rows = []
    for item in items:
        text = tokenizer.apply_chat_template(
            [{"role": "user", "content": item["prompt"]}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=config["enable_thinking"],
        )
        inputs = tokenizer(text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            out = model.generate(
                **inputs,
                do_sample=True,
                temperature=config["temperature"],
                top_p=config["top_p"],
                top_k=config["top_k"],
                max_new_tokens=config["max_completion_length"],
                num_return_sequences=k,
                eos_token_id=stop,
                pad_token_id=tokenizer.pad_token_id,
            )
        for epoch, ids in enumerate(out[:, inputs["input_ids"].shape[1] :].tolist(), start=1):
            end = next((n for n, t in enumerate(ids) if t in ends), None)
            reply = tokenizer.decode(ids if end is None else ids[:end], skip_special_tokens=True)
            rows.append(
                {
                    "id": item["id"],
                    "epoch": epoch,
                    "answer": contract.mcq_choice(reply) or "",
                    "reward": float(contract.mcq_correct(reply, item["answer"])),
                    "tokens": len(ids) if end is None else end,
                    "cut": end is None,
                }
            )
            if replies is not None:
                replies.append({"id": item["id"], "epoch": epoch, "text": reply})
    return rows


def prepare(config: dict):
    """The pinned packages, the libraries, the pinned weights and Unsloth's model and tokenizer."""
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *config["pip"]], check=True)
    libraries()
    RECORD["versions"] = versions()
    query = ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"]
    note("installed", gpu=subprocess.run(query, capture_output=True, text=True).stdout.strip())

    from huggingface_hub import snapshot_download

    path = snapshot_download(config["model"], revision=config["revision"])
    note("downloaded", path=path)

    from unsloth import FastLanguageModel

    note("imported unsloth")  # first, so that it patches trl and transformers
    model, processor = FastLanguageModel.from_pretrained(
        path,
        max_seq_length=config["max_seq_length"],
        load_in_4bit=False,
        fast_inference=False,
    )
    tokenizer = getattr(processor, "tokenizer", processor)
    RECORD["stop_tokens"] = stop_tokens(tokenizer)
    return FastLanguageModel, model, tokenizer


def picked(config: dict, items: list[dict]) -> tuple[dict, dict]:
    """The items of each split, and the ones each sampling takes: the first of each split."""
    split = {s: [i for i in items if i["split"] == s] for s in ("train", "test")}
    n = config["eval_items"]
    return split, {s: v if n is None else v[:n] for s, v in split.items()}


def sampling(when: str, model, tokenizer, chosen: dict, config: dict) -> None:
    """One sampling of every chosen split, seeded, its rows in the record and its texts in
    replies.jsonl."""
    import torch

    torch.manual_seed(config["seed"])
    for s in config["eval_splits"]:
        replies: list[dict] = []
        rows = sample(
            model,
            tokenizer,
            chosen[s],
            config,
            config["eval_samples"],
            RECORD["stop_tokens"],
            replies,
        )
        RECORD.setdefault("eval", {}).setdefault(when, {})[s] = rows
        with open(OUT / "replies.jsonl", "a", encoding="utf-8") as f:
            for reply in replies:
                f.write(json.dumps(reply | {"when": when, "split": s}) + "\n")
        mean = sum(r["reward"] for r in rows) / len(rows)
        note(f"sampled {s} {when}", mean=mean, cut=sum(r["cut"] for r in rows), n=len(rows))


def run(config: dict, items: list[dict]) -> None:
    """Sample, train with GRPO, sample again."""
    FastLanguageModel, model, tokenizer = prepare(config)
    import rollout
    import torch
    from datasets import Dataset
    from trl import GRPOConfig, GRPOTrainer

    model = FastLanguageModel.get_peft_model(
        model,
        r=config["lora_rank"],
        lora_alpha=2 * config["lora_rank"],
        target_modules=config["target_modules"],
        use_gradient_checkpointing="unsloth",
        random_state=config["seed"],
    )
    note("loaded", dtype=str(model.dtype), gpu=torch.cuda.get_device_name(0))
    split, chosen = picked(config, items)
    FastLanguageModel.for_inference(model)
    sampling("before", model, tokenizer, chosen, config)
    FastLanguageModel.for_training(model)
    prompts = [
        {"prompt": [{"role": "user", "content": i["prompt"]}], "answer": i["answer"]}
        for i in split["train"]
    ]
    args = GRPOConfig(
        output_dir=str(OUT / "grpo"),
        max_steps=config["steps"],
        learning_rate=config["learning_rate"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        num_generations=config["num_generations"],
        max_completion_length=config["max_completion_length"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        top_k=config["top_k"],
        chat_template_kwargs={"enable_thinking": config["enable_thinking"]},
        mask_truncated_completions=True,
        optim="adamw_8bit",
        lr_scheduler_type="linear",
        warmup_ratio=0.1,
        logging_steps=1,
        save_strategy="no",
        report_to="none",
        seed=config["seed"],
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
    )
    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        reward_funcs=[rollout.reward],
        args=args,
        train_dataset=Dataset.from_list(prompts),
    )
    torch.cuda.reset_peak_memory_stats()
    trainer.train()
    RECORD["log_history"] = trainer.state.log_history
    RECORD["train_args"] = args.to_dict()
    note("trained", peak_gib=round(torch.cuda.max_memory_allocated() / 2**30, 2))
    FastLanguageModel.for_inference(model)
    sampling("after", model, tokenizer, chosen, config)
    if config["save_adapter"]:
        model.save_pretrained(str(OUT / "adapter"))
        note("saved adapter")


def resample(config: dict, items: list[dict]) -> None:
    """The two samplings alone, from a saved adapter, under one stop set: the adapter disabled
    for "before" (its LoRA starts at zero, so that is the base model), enabled for "after"."""
    FastLanguageModel, model, tokenizer = prepare(config)
    import torch
    from peft import PeftModel

    adapter = find("adapter_model.safetensors")
    model = PeftModel.from_pretrained(model, str(adapter.parent))
    note("loaded", dtype=str(model.dtype), gpu=torch.cuda.get_device_name(0), adapter=adapter.name)
    FastLanguageModel.for_inference(model)
    _, chosen = picked(config, items)
    with model.disable_adapter():
        sampling("before", model, tokenizer, chosen, config)
    sampling("after", model, tokenizer, chosen, config)


def main() -> None:
    config, items = json.loads(CONFIG_JSON), json.loads(ITEMS_JSON)
    RECORD["config"] = config
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")  # one T4 of the two
    try:
        (resample if config["adapter"] else run)(config, items)
    except BaseException:
        note("failed", error=traceback.format_exc())
        raise
    note("done")


if __name__ == "__main__":
    main()
