"""Pinned download and loading of the ClimaQA CSV files from Hugging Face."""

import csv
import hashlib
import urllib.request
from pathlib import Path

REPO = "Rose-STL-Lab/ClimaQA"
REVISION = "3f084a0202c6260e588fb5b681d2e4ec859a3845"  # dataset commit of 2025-03-17

# (config, task) -> (path inside the dataset repo, sha256 of that file at REVISION)
FILES: dict[tuple[str, str], tuple[str, str]] = {
    ("gold", "mcq"): (
        "climaqa_gold/mcq/mcq_benchmark.csv",
        "c05a8babb0fe56d3322344a14e8146a77c84a9882fbaf68a0a6ffd0a74dd3986",
    ),
    ("gold", "cloze"): (
        "climaqa_gold/cloze/cloze_benchmark.csv",
        "dc3061990b92b1252df55e51b1fb0fddacca50caec6f0829c771c3b13730f93a",
    ),
    ("gold", "ffq"): (
        "climaqa_gold/ffq/ffq_benchmark.csv",
        "68b9b8d1544f355fbe4796488e1d65dc30ae23e05c75fe7ba801f3b0dd5a42af",
    ),
    ("silver", "mcq"): (
        "climaqa_silver/mcq/mcq_benchmark_silver.csv",
        "1bfbbba6687077efa54a8b3d4da1c698fb8352e41514a2f45d017b33c01ff6f3",
    ),
    ("silver", "cloze"): (
        "climaqa_silver/cloze/cloze_benchmark_silver.csv",
        "d324b237af89be5228c43222c737c940f35eefeaaf22b677161679f894e50e90",
    ),
    ("silver", "ffq"): (
        "climaqa_silver/ffq/ffq_benchmark_silver.csv",
        "502b5cb1617296d3f8dd14ece7d5b74b821ca19058625573d95fc7b28d17b66a",
    ),
}


def fetch(cache_dir: Path) -> dict[tuple[str, str], Path]:
    """Download missing files into cache_dir and check every file against its pinned hash."""
    paths = {}
    for key, (rel, sha256) in FILES.items():
        path = cache_dir / rel
        body = path.read_bytes() if path.exists() else download(rel)
        digest = hashlib.sha256(body).hexdigest()
        if digest != sha256:
            path.unlink(missing_ok=True)  # never keep a bad copy; the next run downloads again
            raise ValueError(f"{rel}: sha256 {digest} does not match pinned {sha256}")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        paths[key] = path
    return paths


def download(rel: str) -> bytes:
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{rel}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def load(path: Path) -> list[dict[str, str]]:
    """Read one benchmark CSV; the unnamed index column becomes 'id'."""
    with path.open(newline="", encoding="utf-8") as fh:
        return [{k or "id": v for k, v in row.items()} for row in csv.DictReader(fh)]
