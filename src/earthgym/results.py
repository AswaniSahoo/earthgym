"""Compact per-item results of the reported runs, committed so that every published number can
be recomputed without the logs, which are not in git (decision 0019). Each file is one JSON line
for the run (model, task, settings, tokens, the items' sha256) and one per item (id, the answer
the scorer parsed, the reward and the tokens, plus the few flags a report reads from the reply).

uv run python -m earthgym.results <env> <log dir> <name>  # reports/<env>/results/<name>.jsonl
"""

import argparse
import hashlib
import importlib
import json
from importlib.resources import files
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log
from inspect_ai.scorer import CORRECT

from earthgym import spend

ITEMS = {  # environment: (package, bundled items file)
    "climaqa": ("climaqa_v1", "climaqa_clean_v1.jsonl"),
    "era5": ("era5_forecast_v1", "era5_forecast_v1.jsonl"),
    "ibtracs": ("ibtracs_storm_v1", "ibtracs_storm_v1.jsonl"),
    "heat": ("heat_basis_v1", "heat_basis_v1.jsonl"),
}


MANIFESTS = {  # environment: the manifest of its bundled items
    "climaqa": Path("reports/climaqa/clean_v1_manifest.json"),
    "era5": Path("reports/era5/items_v1_manifest.json"),
    "ibtracs": Path("reports/ibtracs/items_v1_manifest.json"),
    "heat": Path("reports/heat/items_v1_manifest.json"),
}


def items_sha256(env: str) -> str:
    package, name = ITEMS[env]
    return hashlib.sha256(files(package).joinpath(name).read_bytes()).hexdigest()


def scored_on(env: str) -> set[str]:
    """The items files a run of this environment may have been scored on: the bundled one and,
    where the gold check dropped items from a draw, that draw (decision 0021)."""
    drawn = json.loads(MANIFESTS[env].read_text("utf-8")).get("drawn_sha256")
    return {items_sha256(env)} | ({drawn} if drawn else set())


def header(log, items: str = "") -> dict:
    """What the reports print about the run itself; items is the items file's sha256."""
    config = log.eval.model_generate_config.merge(log.plan.config)  # eval-level settings win
    rev = log.eval.revision
    return {
        "task": log.eval.task.split("/")[-1],
        "task_args": log.eval.task_args,
        "model": log.eval.model,
        "items_sha256": items,
        "created": log.eval.created,
        "started": log.stats.started_at,
        "completed": log.stats.completed_at,
        "commit": f"{rev.commit}{' (dirty)' if rev.dirty else ''}" if rev else "unknown",
        "settings": config.model_dump(exclude_none=True),
        "inspect_ai": log.eval.packages.get("inspect_ai", ""),
        "tokens": spend.tokens([log]),
        "log": Path(log.location).name,
    }


def row(sample) -> dict:
    """One item as the run scored it: id, parsed answer, reward and tokens."""
    tokens = list(spend.count([sample.model_usage]).values())
    if sample.error or not sample.scores:
        return {"id": sample.id, "error": True, "tokens": tokens}
    score = next(iter(sample.scores.values()))
    value = score.value
    reward = float(value == CORRECT) if isinstance(value, str) else float(value)
    return {"id": sample.id, "answer": score.answer or "", "reward": reward, "tokens": tokens}


def with_epochs(log, rows: list[dict]) -> list[dict]:
    """The rows of a run with several samples per item, each tagged with its sample (Inspect's
    epoch); a one-sample run's rows stay as they are."""
    if (log.eval.config.epochs or 1) < 2:
        return rows
    return [r | {"epoch": s.epoch} for r, s in zip(rows, log.samples, strict=True)]


def write(path: Path, head: dict, rows: list[dict]) -> None:
    lines = [json.dumps(x, default=str) for x in (head, *rows)]  # keys keep their order
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", "utf-8")


def read(path: Path) -> tuple[dict, list[dict]]:
    first, *rest = path.read_text("utf-8").splitlines()
    return json.loads(first), [json.loads(line) for line in rest]


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a run's per-item results.")
    parser.add_argument("env", choices=sorted(ITEMS))
    parser.add_argument("log_dir")
    parser.add_argument("name", help="the report's file name without .md")
    parser.add_argument(
        "--partial",
        action="store_true",
        help="also write a run that stopped early, with its status in the header",
    )
    args = parser.parse_args()
    report = importlib.import_module(f"earthgym.{args.env}.report")
    out = Path("reports") / args.env / "results"
    for info in list_eval_logs(args.log_dir):
        log = read_eval_log(info)
        if log.status != "success" and not args.partial:
            continue
        head = header(log, items_sha256(args.env)) | {"log_dir": args.log_dir}
        if log.status != "success":
            head["status"] = log.status
        head |= {"epochs": log.eval.config.epochs or 1}
        rows = with_epochs(log, report.rows(log))
        kind = f"-{head['task'].split('_')[-1]}" if args.env == "climaqa" else ""
        write(out / f"{args.name}{kind}.jsonl", head, rows)
        print(f"{len(rows)} items written to {out / f'{args.name}{kind}.jsonl'}")


if __name__ == "__main__":
    main()
