"""Jev (TypeSafe System One) client for the ClimaQA third reader (decision 0008).

Two vetted providers, as in climate-risk-agent at d5d7c84: TypeSafe direct, on the pinned
jev-1.14.0, and the Experiential Labs gateway, which grants only the jev-latest alias and relays the
request to TypeSafe (amendment 2026-11-19). JEV_BASE_URL picks one of the two, and any other value
is refused before a key is read. When it is unset the choice falls back: TypeSafe direct if
TYPESAFE_API_KEY is set, else the gateway if JEV_API_KEY is set, else nothing runs. Each provider
reads its own key and no other: TYPESAFE_API_KEY from the environment, else from the repo-root
.env; the gateway's JEV_API_KEY only from where its JEV_BASE_URL came from, .env for the fallback,
and an exported JEV_API_KEY that does not match is refused, as a shell set up for
climate-risk-agent at d5d7c84 exports a TypeSafe key under that name. Every other variable comes
from the environment, else from .env.

Plain urllib, one item per request, no redirect followed. The key is never printed or logged.
"""

import http.client
import json
import math
import os
import time
import urllib.error
import urllib.request
from fractions import Fraction
from pathlib import Path

TYPESAFE = "https://api.typesafe.ai"
GATEWAY = "https://api.experientiallabs.ai"
URL = TYPESAFE + "/v1/systemone"
MODEL = "jev-1.14.0"  # pinned on TypeSafe direct
# The two vetted providers of climate-risk-agent at d5d7c84 (rag/jev_client.py:95-117,
# DEPLOY.md:162-168), each with the header its request id comes back in (rag/jev_client.py:103,
# 115), and the places its key may come from, in order (`provider` binds the gateway's to where
# JEV_BASE_URL came from). The gateway grants only the jev-latest alias. Its Free plan shares 10
# requests a minute
# (experientiallabs.ai/pricing, read 2026-11-19), so calls through it start 7.5 s apart. Its Jev
# page says "Use a bounded timeout, surface HTTP and transport errors, and do not add automatic
# retries or Idempotency-Key: an unknown outcome may already be charged."
# (platform.experientiallabs.ai/models/jev-latest, read 2026-11-19), so a call through it gets one
# try; TypeSafe direct tries again after HTTP 429 and 5xx, TRIES tries at most.
TRIES = 4  # at most, on TypeSafe direct
PROVIDERS = {
    TYPESAFE: {
        "name": "typesafe",
        "url": URL,
        "model": MODEL,
        "key_variable": "TYPESAFE_API_KEY",
        "request_id_header": "x-typesafe-request-id",
        "min_interval_s": 0.0,
        "tries": TRIES,
        "key_sources": ("environment", ".env"),
    },
    GATEWAY: {
        "name": "experientiallabs",
        "url": GATEWAY + "/v1/systemone",
        "model": "jev-latest",
        "key_variable": "JEV_API_KEY",
        "request_id_header": "x-request-id",
        "min_interval_s": 7.5,
        "tries": 1,
        "key_sources": (".env",),
    },
}
BACKOFF_S = 10.0  # waits of 10, 20 and 40 s: together longer than a per-minute rate window
# No tokenizer is published, so a request's input tokens are estimated from its JSON length, as
# climate-risk-agent at d5d7c84 does (rag/jev_client.py:125-129, 397-398), whose 2 characters a
# token is not pessimistic here. Over the 2026-10-31 study's 626 calls, each request rebuilt with
# `request` from reports/climaqa/expert_review_v2.csv against the input_tokens in
# reports/climaqa/results/2026-10-31-jev-third-reader.jsonl (measured 2026-11-19), a token took
# 1.634 characters at least (gold/cloze/19: 737 for 451), 1.873 at the median and 2.418 at most
# (gold/mcq/204). 0.2 below the least, rounded down to one decimal, keeps the estimate above
# every count the run reported.
CHARS_PER_TOKEN = Fraction(7, 5)  # 1.4, exact, so a whole multiple is not rounded up
BODY_CHARS = 2000  # of an unusable reply, kept in its failure record
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


def found(name: str, environ, env_file: Path) -> tuple[str, str]:
    """`name` and where it was found: from the environment ("environment"), else from `env_file`
    (".env"), stripped of whitespace and, in the file, of quotes; ("", "") when it is blank or
    unset in both."""
    value = environ.get(name, "").strip()
    if value:
        return value, "environment"
    if env_file.exists():
        for line in env_file.read_text("utf-8").splitlines():
            left, _, right = line.strip().removeprefix("export ").partition("=")
            if left.strip() == name and (value := right.strip().strip("'\"").strip()):
                return value, ".env"
    return "", ""


def setting(name: str, environ, env_file: Path) -> str:
    """`name` from the environment, else from `env_file` (see `found`); "" when it is unset."""
    return found(name, environ, env_file)[0]


def _seconds(text: str) -> float:
    """JEV_MIN_INTERVAL_S in seconds: a finite number of 0 or more, or a ValueError."""
    try:
        seconds = float(text)
    except ValueError:
        seconds = math.nan
    if not (math.isfinite(seconds) and seconds >= 0):
        raise ValueError("JEV_MIN_INTERVAL_S must be a finite number of seconds, 0 or more")
    return seconds


def provider(environ=os.environ, env_file: Path | None = None) -> dict:
    """The vetted provider JEV_BASE_URL names: its name, URL, model, key variable, request id
    header, pacing, tries and the places its key may come from. Any other value that is set, even
    one of only slashes, is refused before a key is read, so where the items go is a code change,
    not a typo, and a JEV_BASE_URL that was found always names a vetted base. When it is unset:
    TypeSafe direct if TYPESAFE_API_KEY is set, else the gateway if JEV_API_KEY is set. The
    gateway's key then comes only from where its JEV_BASE_URL came from, the repo-root .env for the
    fallback, and an exported JEV_API_KEY that does not match is refused: climate-risk-agent at
    d5d7c84 reads JEV_API_KEY for TypeSafe direct when JEV_BASE_URL is unset
    (rag/jev_client.py:975-985), so a shell set up for it exports a TypeSafe key under that name.
    JEV_MIN_INTERVAL_S overrides the pacing. Every variable but the gateway's key comes from
    `environ`, else from `env_file` (default ENV_FILE); a blank one counts as unset."""
    env_file = env_file or ENV_FILE
    found_base, base_source = found("JEV_BASE_URL", environ, env_file)
    base = found_base.rstrip("/")
    if found_base and base not in PROVIDERS:  # "/" is set, so not the fallback: refused
        raise ValueError(f"JEV_BASE_URL must be one of {sorted(PROVIDERS)}")
    if not base:  # the fallback, by which key is set
        if setting("TYPESAFE_API_KEY", environ, env_file):
            base = TYPESAFE
        elif setting("JEV_API_KEY", environ, env_file):
            base = GATEWAY
        else:
            raise RuntimeError(
                "neither TYPESAFE_API_KEY nor JEV_API_KEY is set in the environment or in "
                f"{env_file}, and no JEV_BASE_URL names a provider"
            )
    chosen = dict(PROVIDERS[base])
    if base == GATEWAY and base_source == "environment":
        chosen["key_sources"] = ("environment",)
    elif base == GATEWAY and environ.get("JEV_API_KEY", "").strip():
        came = "comes from .env" if base_source == ".env" else "is unset"
        raise ValueError(
            f"JEV_API_KEY is set in the environment but JEV_BASE_URL {came}, and the gateway's "
            "key must come from where JEV_BASE_URL does. If the exported JEV_API_KEY is an "
            "Experiential Labs key, export JEV_BASE_URL=https://api.experientiallabs.ai with it. "
            "If it is a TypeSafe key, as a shell set up for climate-risk-agent has, unset "
            "JEV_API_KEY in this shell and keep the gateway key in .env."
        )
    if interval := setting("JEV_MIN_INTERVAL_S", environ, env_file):
        chosen["min_interval_s"] = _seconds(interval)
    return chosen


def _key(chosen: dict, environ, env_file: Path) -> tuple[str, str]:
    """The chosen provider's key and the place it came from, trying its key_sources in order;
    ("", "") when none holds it."""
    name = chosen["key_variable"]
    for source in chosen["key_sources"]:
        if source == "environment":
            value = environ.get(name, "").strip()
        else:  # the .env file alone
            value = found(name, {}, env_file)[0]
        if value:
            return value, source
    return "", ""


def summary(chosen: dict, environ=os.environ, env_file: Path | None = None) -> str:
    """What a run sends its calls through, to print before the first: the provider, its base URL,
    the model, and the key's variable and where it was found, never the key."""
    env_file = env_file or ENV_FILE
    source = _key(chosen, environ, env_file)[1]
    where = {"environment": "the environment", ".env": str(env_file)}.get(source, "nowhere")
    base = chosen["url"].removesuffix("/v1/systemone")
    return (
        f"Jev through {chosen['name']} at {base}, model {chosen['model']},"
        f" key {chosen['key_variable']} from {where}"
    )


def request(task: str, state: dict, order: list[str] | None = None, model: str = MODEL) -> dict:
    """One item as the state and one choice question over its task's buckets, listed in
    `order` (default: the order of BUCKETS), for `model`."""
    names = list(BUCKETS[task]) if order is None else list(order)
    if sorted(names) != sorted(BUCKETS[task]):
        raise ValueError(f"the order must list each {task} bucket once: {names}")
    criteria = {name: BUCKETS[task][name] for name in names}
    question = {"type": "choice", "instructions": INSTRUCTIONS[task], "criteria": criteria}
    return {"model": model, "state": state, "questions": {"bucket": question}}


def _named(body) -> str:
    """What an error body names: the gateway's {"error": {"code": ...}}, or TypeSafe's
    {"detail": ...}, a string or a list of objects with a "msg"; nothing else from the body,
    which can echo the request."""
    if not isinstance(body, dict):
        return ""
    error, detail = body.get("error"), body.get("detail")
    if isinstance(error, dict) and isinstance(error.get("code"), str):
        return error["code"]
    if isinstance(detail, list):
        detail = "; ".join(
            d["msg"] for d in detail if isinstance(d, dict) and isinstance(d.get("msg"), str)
        )
    return detail if isinstance(detail, str) else ""


def _refusal(error: urllib.error.HTTPError) -> str:
    """The status and what the error body names. It never raises: a body that cannot be read or
    parsed leaves the status alone."""
    try:
        named = _named(json.loads(error.read()))
    except Exception:
        named = ""
    return f"HTTP {error.code} {named}".rstrip()


def estimate(body: dict) -> int:
    """The input tokens a request may count: one per CHARS_PER_TOKEN characters of its JSON,
    rounded up (climate-risk-agent's way at d5d7c84, with the divisor measured above)."""
    return math.ceil(len(json.dumps(body, ensure_ascii=False)) / CHARS_PER_TOKEN)


def _number(value) -> bool:
    """A finite int or float, and not a bool."""
    if isinstance(value, bool):
        return False
    return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))


def count(value) -> int | None:
    """`value` as a count of tokens: an int, or a float with an integer value, of 0 or more, as an
    int; None for a bool, NaN, infinity or anything else."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    if isinstance(value, float) and not (math.isfinite(value) and value.is_integer()):
        return None
    return int(value) if value >= 0 else None


def _answers(reply, body: dict) -> None:
    """Raise unless `reply` answers `body`: a model named by a non-empty string, input and output
    tokens as counts (see `count`), and for each question sent a choice among the options it
    sent, with a probability, a finite number, for exactly those options."""
    model = reply["model"]
    if not (isinstance(model, str) and model.strip()):
        raise TypeError("model is not a non-empty string")
    usage = reply["usage"]
    if count(usage["input_tokens"]) is None:
        raise TypeError("usage.input_tokens is not a whole number of 0 or more")
    # a missing output count is 0, as in climate-risk-agent at d5d7c84 (rag/jev_client.py:483)
    if count(usage.get("output_tokens", 0)) is None:
        raise TypeError("usage.output_tokens is not a whole number of 0 or more")
    for name, question in body.get("questions", {}).items():
        options, answer = list(question["criteria"]), reply["answers"][name]
        if answer["choice"] not in options:
            raise ValueError(f"answers.{name}.choice is not an option the request sent")
        spread = answer["probabilities"]
        if not isinstance(spread, dict) or sorted(spread) != sorted(options):
            raise ValueError(f"answers.{name}.probabilities do not name exactly the options sent")
        if not all(_number(p) for p in spread.values()):
            raise TypeError(f"answers.{name}.probabilities hold a value that is not a number")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Follows no redirect. urllib's own handler sends a POST answered 301, 302 or 303 on to the
    Location with every header but the two content ones, the key's Authorization among them
    (urllib/request.py, HTTPRedirectHandler.redirect_request), so every 3xx is an HTTPError."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


def no_redirect_opener(*handlers):
    """The `open` of urllib's opener with `handlers` added, following no redirect."""
    return urllib.request.build_opener(NoRedirect, *handlers).open


OPEN = no_redirect_opener()  # what every call goes through


class CallError(RuntimeError):
    """A call that ended without a usable reply, with what its log record keeps, none of it the
    key: the class of the error that ended it, the retries before that, the HTTP status and the
    request id if there were any and, for an unusable reply, its raw body cut to BODY_CHARS."""

    def __init__(self, message, error, retries, status=None, request_id=None, body=None):
        super().__init__(message)
        self.error, self.retries, self.status = error, retries, status
        self.request_id, self.body = request_id, body


def call(
    body: dict,
    key: str,
    url: str = URL,
    opener=OPEN,
    timeout: float = 30.0,
    sleep=time.sleep,
    id_header: str = PROVIDERS[TYPESAFE]["request_id_header"],
    tries: int = TRIES,
) -> tuple[dict, float, int, str | None]:
    """POST one request; the response payload, the wall time of the try that answered in seconds,
    the number of retries, and the request id from the `id_header` response header (None if
    absent). HTTP 429 and 5xx are tried again after doubling waits, `tries` tries at most, so with
    one try, as through the gateway, every error surfaces at once. Any other refusal, such as 403
    model_not_granted, a timeout or other transport error, and a 200 that does not answer the
    request (see `_answers`) raise CallError at once. A request header refused before sending
    raises ValueError. No error shows the key."""
    data = json.dumps(body).encode("utf-8")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for retries in range(tries):
        sent = urllib.request.Request(url, data=data, headers=headers, method="POST")
        start = time.monotonic()
        try:
            response = opener(sent, timeout=timeout)
        except urllib.error.HTTPError as error:
            busy = error.code == 429 or 500 <= error.code < 600
            if busy and retries < tries - 1:
                sleep(BACKOFF_S * 2**retries)
                continue
            found = (error.headers or {}).get(id_header)
            message = f"{url} refused the request: {_refusal(error)}"
            raise CallError(message, "HTTPError", retries, error.code, found) from None
        except ValueError:  # http.client quotes a header value it refuses, and so the key
            raise ValueError(
                f"a request header for {url} was refused; the key is not shown"
            ) from None
        except (OSError, http.client.HTTPException) as error:
            name = type(error).__name__
            raise CallError(f"{url}: {name}: {error}", name, retries) from error
        with response:
            status, found = response.status, response.headers.get(id_header)
            try:
                raw = response.read()
            except (OSError, http.client.HTTPException) as error:
                name = type(error).__name__
                raise CallError(f"{url}: {name}: {error}", name, retries, status, found) from error
        seconds = time.monotonic() - start
        try:
            payload = json.loads(raw)
            _answers(payload, body)
        except (ValueError, LookupError, TypeError, RecursionError) as error:
            name, text = type(error).__name__, raw.decode("utf-8", "replace")[:BODY_CHARS]
            message = f"{url} answered HTTP {status} with no usable reply: {name}: {error}"
            raise CallError(message, name, retries, status, found, text) from None
        return payload, seconds, retries, found


def load_key(chosen: dict, environ=os.environ, env_file: Path | None = None) -> str:
    """The `chosen` provider's key and no other: TYPESAFE_API_KEY for TypeSafe direct and
    JEV_API_KEY for the gateway, so one provider's key is never sent to the other. It comes only
    from the places the provider's key_sources name, in order (`environ`, or `env_file`, default
    ENV_FILE), stripped; one that still holds whitespace or an unprintable character, such as a
    control character, is refused. No error shows it."""
    env_file = env_file or ENV_FILE
    name = chosen["key_variable"]
    key = _key(chosen, environ, env_file)[0]
    if not key:
        places = [
            "the environment" if source == "environment" else str(env_file)
            for source in chosen["key_sources"]
        ]
        raise RuntimeError(
            f"{name} is not set in {' or in '.join(places)}, the places {chosen['name']} reads "
            "it from, and it reads no other key"
        )
    if any(c.isspace() or not c.isprintable() for c in key):
        raise ValueError(
            f"{name} still holds whitespace or an unprintable character, such as a control "
            "character, after stripping; set it again"
        )
    return key


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
