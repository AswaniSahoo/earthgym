"""Jev (TypeSafe System One) client for the ClimaQA third reader (decision 0008).

Plain urllib, one item per request, the model pinned. The key is never printed or logged.
"""

import json
import os
import time
import urllib.request
from pathlib import Path

URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.14.0"  # pinned, not the jev-latest alias
USD_PER_INPUT_TOKEN = 0.042 / 1e6  # docs.typesafe.ai/models, 2026-10-31; output is free
LIMIT_USD = 0.10  # my cap for the study (0008)


def repo_root(module: Path) -> Path:
    """The checkout that holds this module: src/earthgym/climaqa/jev.py sits four levels down."""
    return module.parents[3]


ENV_FILE = repo_root(Path(__file__).resolve()) / ".env"
INSTRUCTIONS = {
    "mcq": (
        "A multiple choice item: `question`, its `options`, the answer `key` and the "
        "`model_answer` a model gave. Which description fits the item best?"
    ),
    "cloze": (
        "A cloze item: the `sentence` has a blank marked <MASK>, `key` is the answer key and "
        "`reply` is the fill a model gave. Which description fits best?"
    ),
}
BUCKETS = {  # the miss notes' buckets, restated as properties of the item
    "mcq": {
        "key_right": "The key is the one right answer; a model answer that differs is wrong.",
        "ambiguous": "The key and another option are both defensible answers as written.",
        "flawed_item": (
            "The key is wrong, no option is fully right, or the question refers to "
            "information it does not give."
        ),
        "source_only": (
            "The question tests a source document, such as a book's acknowledgments or a "
            "number from one text, rather than climate science."
        ),
    },
    "cloze": {
        "same_answer": (
            "The reply names the same thing as the key, perhaps in another string: a symbol, "
            "a word order, a plural or a synonym."
        ),
        "other_correct_word": (
            "The reply names something else, but the sentence with the reply is still "
            "correct, and nothing in it rules the reply out."
        ),
        "wrong_reply": "The sentence with the reply is wrong.",
    },
}


def request(task: str, state: dict, order: list[str] | None = None) -> dict:
    """One item as the state and one choice question over its task's buckets, listed in
    `order` (default: the order of BUCKETS)."""
    names = list(BUCKETS[task]) if order is None else list(order)
    if sorted(names) != sorted(BUCKETS[task]):
        raise ValueError(f"the order must list each {task} bucket once: {names}")
    criteria = {name: BUCKETS[task][name] for name in names}
    question = {"type": "choice", "instructions": INSTRUCTIONS[task], "criteria": criteria}
    return {"model": MODEL, "state": state, "questions": {"bucket": question}}


def call(
    body: dict, key: str, opener=urllib.request.urlopen, timeout: float = 30.0
) -> tuple[dict, float]:
    """POST one request; the response payload and the wall time in seconds."""
    data = json.dumps(body).encode("utf-8")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    sent = urllib.request.Request(URL, data=data, headers=headers, method="POST")
    start = time.monotonic()
    with opener(sent, timeout=timeout) as response:
        payload = json.loads(response.read())
    return payload, time.monotonic() - start


def load_key(environ=os.environ, env_file: Path = ENV_FILE) -> str:
    """TYPESAFE_API_KEY from the environment, else from the .env file."""
    if environ.get("TYPESAFE_API_KEY"):
        return environ["TYPESAFE_API_KEY"]
    if env_file.exists():
        for line in env_file.read_text("utf-8").splitlines():
            name, _, value = line.strip().removeprefix("export ").partition("=")
            if name.strip() == "TYPESAFE_API_KEY" and value.strip():
                return value.strip().strip("'\"")
    raise RuntimeError(f"TYPESAFE_API_KEY is not set in the environment or in {env_file}")


class Budget:
    """Input tokens spent so far, against a dollar limit."""

    def __init__(
        self, limit_usd: float = LIMIT_USD, usd_per_input_token: float = USD_PER_INPUT_TOKEN
    ):
        self.limit, self.price, self.tokens = limit_usd, usd_per_input_token, 0

    @property
    def spent(self) -> float:
        return self.tokens * self.price

    def allows(self, tokens: int) -> bool:
        return (self.tokens + tokens) * self.price <= self.limit

    def charge(self, tokens: int) -> None:
        self.tokens += tokens
