import email.message
import http.client
import inspect
import io
import json
import traceback
import urllib.error
import urllib.request
import urllib.response
from fractions import Fraction

import pytest

from earthgym.climaqa import jev

CLOZE = {"sentence": "The <MASK> rises.", "key": "sun", "reply": "Sun"}
GATEWAY = "https://api.experientiallabs.ai"
CHECKOUT_ENV_FILE = jev.ENV_FILE  # taken before the fixture below points it elsewhere
DIRECT = {
    "name": "typesafe",
    "url": "https://api.typesafe.ai/v1/systemone",
    "model": "jev-1.14.0",
    "key_variable": "TYPESAFE_API_KEY",
    "request_id_header": "x-typesafe-request-id",
    "min_interval_s": 0.0,
    "tries": 4,
    "key_sources": ("environment", ".env"),
}
THROUGH_GATEWAY = {  # as JEV_BASE_URL in .env, or the fallback, picks it: its key from .env
    "name": "experientiallabs",
    "url": GATEWAY + "/v1/systemone",
    "model": "jev-latest",
    "key_variable": "JEV_API_KEY",
    "request_id_header": "x-request-id",
    "min_interval_s": 7.5,
    "tries": 1,
    "key_sources": (".env",),
}
ENV_GATEWAY = THROUGH_GATEWAY | {"key_sources": ("environment",)}  # JEV_BASE_URL exported


@pytest.fixture(autouse=True)
def no_checkout_env_file(monkeypatch, tmp_path):
    """No test reads the checkout's .env, which holds the keys."""
    monkeypatch.setattr(jev, "ENV_FILE", tmp_path / "absent.env")


def test_jev_base_url_picks_one_of_the_two_vetted_providers_and_refuses_any_other(tmp_path):
    assert jev.provider({"JEV_BASE_URL": "https://api.typesafe.ai"}) == DIRECT
    assert jev.provider({"JEV_BASE_URL": GATEWAY + "/"}) == ENV_GATEWAY
    env_file = tmp_path / ".env"
    for other in ["https://api.example.com", "http://api.typesafe.ai", "/", "//", " / "]:
        with pytest.raises(ValueError, match="JEV_BASE_URL"):
            jev.provider({"JEV_BASE_URL": other})
        env_file.write_text(f'JEV_BASE_URL="{other}"\n', "utf-8")
        with pytest.raises(ValueError, match="JEV_BASE_URL"):
            jev.provider({}, env_file)


def test_jev_base_url_comes_from_the_environment_else_from_the_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(f"export JEV_BASE_URL='{GATEWAY}'\n", "utf-8")
    assert jev.provider({}, env_file) == THROUGH_GATEWAY
    assert jev.provider({"JEV_BASE_URL": " https://api.typesafe.ai "}, env_file) == DIRECT


class Watched(dict):
    """An environment that notes each variable asked of it."""

    def __init__(self, **variables):
        super().__init__(variables)
        self.asked = []

    def get(self, name, default=None):
        self.asked.append(name)
        return super().get(name, default)


def test_an_unvetted_jev_base_url_is_refused_before_any_key_is_read(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "JEV_BASE_URL=https://api.example.com\nTYPESAFE_API_KEY=ts-hidden\n", "utf-8"
    )
    environ = Watched(JEV_API_KEY="jev-hidden")
    with pytest.raises(ValueError, match="JEV_BASE_URL") as refused:
        jev.provider(environ, env_file)
    assert environ.asked == ["JEV_BASE_URL"] and "hidden" not in str(refused.value)


def test_a_jev_base_url_of_only_slashes_is_refused_before_any_key_is_read(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("", "utf-8")
    for slashes in ["/", "//", " / "]:  # as from export JEV_BASE_URL="$HOST/" with HOST unset
        environ = Watched(JEV_BASE_URL=slashes, JEV_API_KEY="jev-hidden")
        with pytest.raises(ValueError, match="JEV_BASE_URL") as refused:
            jev.provider(environ, env_file)
        assert environ.asked == ["JEV_BASE_URL"] and "hidden" not in str(refused.value)


def test_unset_jev_base_url_falls_back_to_typesafe_direct_then_the_gateway(tmp_path):
    assert jev.provider({"TYPESAFE_API_KEY": "t"}) == DIRECT
    assert jev.provider({"TYPESAFE_API_KEY": "t", "JEV_API_KEY": "j"}) == DIRECT
    env_file = tmp_path / ".env"
    env_file.write_text("JEV_API_KEY=j\n", "utf-8")
    assert jev.provider({}, env_file) == THROUGH_GATEWAY  # the gateway's key, from .env
    assert jev.provider({"TYPESAFE_API_KEY": " "}, env_file) == THROUGH_GATEWAY
    assert jev.provider({"TYPESAFE_API_KEY": "t"}, env_file) == DIRECT
    with pytest.raises(RuntimeError, match="neither TYPESAFE_API_KEY nor JEV_API_KEY"):
        jev.provider({})


COMBINATIONS = [  # where JEV_BASE_URL comes from, where JEV_API_KEY is set, and what follows
    ("environment", "environment", "jev-env"),
    ("environment", ".env", "not set in the environment"),
    ("environment", "both", "jev-env"),
    ("environment", "neither", "not set in the environment"),
    (".env", "environment", "refused"),
    (".env", ".env", "jev-file"),
    (".env", "both", "refused"),
    (".env", "neither", "not set in"),
    ("unset", "environment", "refused"),
    ("unset", ".env", "jev-file"),
    ("unset", "both", "refused"),
    ("unset", "neither", "neither TYPESAFE_API_KEY nor JEV_API_KEY"),
    ("blank", "environment", "refused"),  # exported as "" or " ": unset, as the rows above
    ("blank", ".env", "jev-file"),
    ("blank", "both", "refused"),
    ("blank", "neither", "neither TYPESAFE_API_KEY nor JEV_API_KEY"),
]
EXPORTED = {"environment": [GATEWAY], "blank": ["", " "]}  # each JEV_BASE_URL exported, in turn
REFUSED = "JEV_API_KEY.*JEV_BASE_URL.*climate-risk-agent"


def gateway_key(environ, env_file):
    return jev.load_key(jev.provider(environ, env_file), environ, env_file)


@pytest.mark.parametrize(("base_from", "key_in", "outcome"), COMBINATIONS)
def test_the_gateways_key_comes_from_where_its_jev_base_url_does(
    tmp_path, base_from, key_in, outcome
):
    env_file = tmp_path / ".env"
    for exported in EXPORTED.get(base_from, [None]):
        environ, lines = {}, []
        if exported is not None:
            environ["JEV_BASE_URL"] = exported
        if base_from == ".env":
            lines.append(f"JEV_BASE_URL={GATEWAY}")
        if key_in in ("environment", "both"):
            environ["JEV_API_KEY"] = "jev-env"
        if key_in in (".env", "both"):
            lines.append("JEV_API_KEY=jev-file")
        env_file.write_text("".join(f"{line}\n" for line in lines), "utf-8")
        if outcome.startswith("jev-"):
            assert gateway_key(environ, env_file) == outcome
        elif outcome == "refused":
            with pytest.raises(ValueError, match=REFUSED) as no:
                gateway_key(environ, env_file)
            assert "jev-env" not in str(no.value)
        else:
            with pytest.raises(RuntimeError, match=outcome) as missing:
                gateway_key(environ, env_file)
            assert "jev-" not in str(missing.value)


def test_summary_names_the_provider_base_url_model_and_where_the_key_was_found(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("JEV_API_KEY=jev-hidden\n", "utf-8")
    assert jev.summary(THROUGH_GATEWAY, {}, env_file) == (
        "Jev through experientiallabs at https://api.experientiallabs.ai, model jev-latest,"
        f" key JEV_API_KEY from {env_file}"
    )
    assert jev.summary(DIRECT, {"TYPESAFE_API_KEY": "ts-hidden"}) == (
        "Jev through typesafe at https://api.typesafe.ai, model jev-1.14.0,"
        " key TYPESAFE_API_KEY from the environment"
    )


def test_jev_min_interval_s_overrides_the_providers_pacing(tmp_path):
    gateway = {"JEV_BASE_URL": GATEWAY, "JEV_MIN_INTERVAL_S": "0"}
    assert jev.provider(gateway)["min_interval_s"] == 0.0
    env_file = tmp_path / ".env"
    env_file.write_text("JEV_MIN_INTERVAL_S=2.5\n", "utf-8")
    assert jev.provider({"JEV_BASE_URL": GATEWAY}, env_file)["min_interval_s"] == 2.5


def test_jev_min_interval_s_paces_typesafe_direct_as_well():
    direct = {"JEV_BASE_URL": "https://api.typesafe.ai", "JEV_MIN_INTERVAL_S": "2"}
    assert jev.provider(direct)["min_interval_s"] == 2.0
    assert (
        jev.provider({"TYPESAFE_API_KEY": "t", "JEV_MIN_INTERVAL_S": "0.5"})["min_interval_s"]
        == 0.5
    )


def test_jev_min_interval_s_must_be_a_finite_number_of_zero_or_more():
    for bad in ["-1", "-0.5", "nan", "inf", "-inf", "1e999", "soon", "7.5s"]:
        with pytest.raises(ValueError, match="JEV_MIN_INTERVAL_S"):
            jev.provider({"JEV_BASE_URL": GATEWAY, "JEV_MIN_INTERVAL_S": bad})


def test_request_names_the_model_it_is_given():
    assert jev.request("cloze", CLOZE, model="jev-latest")["model"] == "jev-latest"


def test_request_holds_one_item_and_one_choice_question_on_the_pinned_model():
    body = jev.request("cloze", CLOZE)
    assert body["model"] == "jev-1.14.0" and body["state"] == CLOZE
    assert list(body["questions"]) == ["bucket"]
    question = body["questions"]["bucket"]
    assert question["type"] == "choice"
    assert list(question["criteria"]) == ["same_answer", "other_correct_word", "wrong_reply"]


def test_request_lists_the_options_in_a_given_order_and_refuses_a_partial_one():
    order = ["wrong_reply", "same_answer", "other_correct_word"]
    assert list(jev.request("cloze", CLOZE, order)["questions"]["bucket"]["criteria"]) == order
    with pytest.raises(ValueError):
        jev.request("cloze", CLOZE, ["wrong_reply", "same_answer"])


class FakeResponse(io.BytesIO):
    """What urlopen answers with: a body, status 200 and headers whose names ignore case."""

    status = 200

    def __init__(self, body, headers=None):
        super().__init__(body)
        self.headers = email.message.Message()
        for name, value in (headers or {}).items():
            self.headers[name] = value

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


USABLE = json.dumps({"model": "jev-1.14.0", "usage": {"input_tokens": 9}}).encode()


def test_call_posts_json_with_the_key_as_a_bearer_token_and_times_the_call():
    seen = {}

    def opener(request, timeout):
        seen.update(url=request.full_url, method=request.get_method(), timeout=timeout)
        seen.update(auth=request.get_header("Authorization"), body=json.loads(request.data))
        return FakeResponse(USABLE)

    payload, seconds, retries, _ = jev.call({"model": "m"}, "test-key", opener=opener)
    assert payload["usage"]["input_tokens"] == 9 and seconds >= 0 and retries == 0
    assert seen["url"] == "https://api.typesafe.ai/v1/systemone" and seen["method"] == "POST"
    assert seen["auth"] == "Bearer test-key" and seen["body"] == {"model": "m"}


def test_call_returns_the_request_id_header_its_provider_names_or_none():
    def answering(headers):
        return lambda request, timeout: FakeResponse(USABLE, headers)

    both = {"X-TypeSafe-Request-Id": "ts-1", "X-Request-Id": "gw-1"}
    assert jev.call({}, "k", opener=answering(both))[3] == "ts-1"
    url, header = THROUGH_GATEWAY["url"], THROUGH_GATEWAY["request_id_header"]
    assert jev.call({}, "k", url=url, opener=answering(both), id_header=header)[3] == "gw-1"
    assert jev.call({}, "k", opener=answering({}))[3] is None


def refusal(status, body=b""):
    return urllib.error.HTTPError("https://jev.test", status, "refused", {}, io.BytesIO(body))


def answers_after(failures, reply=USABLE):
    """An opener that raises each error in `failures` in turn, then answers with `reply`; and the
    URLs it was asked for."""
    urls = []

    def opener(request, timeout):
        urls.append(request.full_url)
        if len(urls) <= len(failures):
            raise failures[len(urls) - 1]
        return FakeResponse(reply)

    return opener, urls


def test_typesafe_direct_retries_429_and_5xx_after_doubling_waits_up_to_four_tries():
    sleeps, url = [], DIRECT["url"]
    opener, urls = answers_after([refusal(429), refusal(503)])
    payload, _, retries, _ = jev.call({}, "k", url=url, opener=opener, sleep=sleeps.append)
    assert (payload["usage"]["input_tokens"], retries, sleeps) == (9, 2, [10.0, 20.0])
    assert urls == [url] * 3
    sleeps.clear()
    opener, urls = answers_after([refusal(500)] * 4)
    with pytest.raises(jev.CallError, match="HTTP 500") as failed:
        jev.call({}, "k", opener=opener, sleep=sleeps.append)
    assert len(urls) == 4 and sleeps == [10.0, 20.0, 40.0]
    assert (failed.value.error, failed.value.status, failed.value.retries) == ("HTTPError", 500, 3)


@pytest.mark.parametrize(
    ("failure", "named"),
    [
        (refusal(429), "HTTP 429"),
        (refusal(503), "HTTP 503"),
        (TimeoutError("timed out"), "TimeoutError"),
    ],
    ids=["429", "503", "timeout"],
)
def test_through_the_gateway_no_error_is_tried_again(failure, named):
    sleeps, url, tries = [], THROUGH_GATEWAY["url"], THROUGH_GATEWAY["tries"]
    opener, urls = answers_after([failure])
    with pytest.raises(jev.CallError, match=named) as failed:
        jev.call({}, "k", url=url, opener=opener, sleep=sleeps.append, tries=tries)
    assert len(urls) == 1 and sleeps == [] and failed.value.retries == 0


REQUEST = jev.request("cloze", CLOZE)


def answer(change=None):
    """A reply to REQUEST, as raw bytes: a usable one, or one that `change` has spoilt."""
    spread = {"same_answer": 0.75, "other_correct_word": 0.25, "wrong_reply": 0.0}
    bucket = {"type": "choice", "choice": "same_answer", "confidence": 0.5, "probabilities": spread}
    reply = {"model": "jev-1.14.0", "answers": {"bucket": bucket}, "usage": {"input_tokens": 9}}
    if change:
        change(reply)
    return json.dumps(reply).encode()


def bucket(reply):
    return reply["answers"]["bucket"]


MALFORMED = {  # a 200 that does not answer REQUEST, and the class of error it fails with
    "no model": (answer(lambda r: r.pop("model")), "KeyError"),
    "a model that is not a string": (answer(lambda r: r.update(model=5)), "TypeError"),
    "no answers": (answer(lambda r: r.pop("answers")), "KeyError"),
    "a choice not offered": (answer(lambda r: bucket(r).update(choice="ambiguous")), "ValueError"),
    "an extra probability": (
        answer(lambda r: bucket(r)["probabilities"].update(ambiguous=0.0)),
        "ValueError",
    ),
    "a missing probability": (
        answer(lambda r: bucket(r)["probabilities"].pop("wrong_reply")),
        "ValueError",
    ),
    "a probability that is not a number": (
        answer(lambda r: bucket(r)["probabilities"].update(same_answer="high")),
        "TypeError",
    ),
    "input tokens that are not a count": (
        answer(lambda r: r["usage"].update(input_tokens="9")),
        "TypeError",
    ),
    "negative input tokens": (answer(lambda r: r["usage"].update(input_tokens=-1)), "TypeError"),
    "input tokens that are true": (
        answer(lambda r: r["usage"].update(input_tokens=True)),
        "TypeError",
    ),
    "NaN input tokens": (
        answer(lambda r: r["usage"].update(input_tokens=float("nan"))),
        "TypeError",
    ),
    "infinite input tokens": (
        answer(lambda r: r["usage"].update(input_tokens=float("inf"))),
        "TypeError",
    ),
    "a probability that is true": (
        answer(lambda r: bucket(r)["probabilities"].update(same_answer=True)),
        "TypeError",
    ),
    "a NaN probability": (
        answer(lambda r: bucket(r)["probabilities"].update(same_answer=float("nan"))),
        "TypeError",
    ),
    "an infinite probability": (
        answer(lambda r: bucket(r)["probabilities"].update(same_answer=float("inf"))),
        "TypeError",
    ),
    "probabilities that are not an object": (
        answer(lambda r: bucket(r).update(probabilities=[0.75, 0.25, 0.0])),
        "ValueError",
    ),
    "an empty model": (answer(lambda r: r.update(model="")), "TypeError"),
    "input tokens of 9.5": (answer(lambda r: r["usage"].update(input_tokens=9.5)), "TypeError"),
    "output tokens of 9.5": (answer(lambda r: r["usage"].update(output_tokens=9.5)), "TypeError"),
    "negative output tokens": (answer(lambda r: r["usage"].update(output_tokens=-1)), "TypeError"),
    "output tokens that are true": (
        answer(lambda r: r["usage"].update(output_tokens=True)),
        "TypeError",
    ),
    "a deeply nested reply": (b"[" * 100_000, "RecursionError"),
    "not JSON": (b"<html>busy</html>", "JSONDecodeError"),
}


def test_a_usable_answer_to_the_request_is_accepted():
    opener, _ = answers_after([], reply=answer())
    payload, _, retries, _ = jev.call(REQUEST, "k", opener=opener)
    assert (bucket(payload)["choice"], retries) == ("same_answer", 0)


def test_token_counts_are_whole_numbers_of_zero_or_more_and_53_0_counts_as_53():
    whole = answer(lambda r: r["usage"].update(input_tokens=53.0, output_tokens=53.0))
    opener, _ = answers_after([], reply=whole)
    assert jev.call(REQUEST, "k", opener=opener)[0]["usage"]["input_tokens"] == 53.0
    assert [jev.count(v) for v in (53.0, 53, 0)] == [53, 53, 0] and type(jev.count(53.0)) is int
    for odd in (9.5, -1, True, float("nan"), float("inf"), "53", None):
        assert jev.count(odd) is None


@pytest.mark.parametrize(("raw", "error"), MALFORMED.values(), ids=MALFORMED)
def test_a_200_that_does_not_answer_the_request_raises_call_error_with_its_raw_body(raw, error):
    opener, _ = answers_after([], reply=raw)
    with pytest.raises(jev.CallError) as failed:
        jev.call(REQUEST, "k", opener=opener)
    assert (failed.value.error, failed.value.status, failed.value.retries) == (error, 200, 0)
    assert failed.value.body == raw.decode()[:2000]


def test_a_200_whose_body_cannot_be_read_raises_call_error_with_its_status():
    class Cut(FakeResponse):
        def read(self, *size):
            raise http.client.IncompleteRead(b"half")

    def opener(request, timeout):
        return Cut(b"", {"X-TypeSafe-Request-Id": "ts-7"})

    with pytest.raises(jev.CallError) as failed:
        jev.call(REQUEST, "k", opener=opener)
    seen = (failed.value.error, failed.value.status, failed.value.request_id, failed.value.body)
    assert seen == ("IncompleteRead", 200, "ts-7", None)


def test_a_bare_http_exception_from_the_opener_is_a_call_error():
    opener, _ = answers_after([http.client.HTTPException("bad status line")])
    with pytest.raises(jev.CallError, match="HTTPException") as failed:
        jev.call(REQUEST, "k", opener=opener)
    assert (failed.value.error, failed.value.status, failed.value.retries) == (
        "HTTPException",
        None,
        0,
    )


class Redirecting(urllib.request.BaseHandler):
    """A transport, first in line, that answers every request with a redirect and notes it."""

    handler_order = 0

    def __init__(self, code):
        self.code, self.seen = code, []

    def answer(self, request):
        self.seen.append((request.full_url, request.get_header("Authorization")))
        headers = email.message.Message()
        headers["Location"] = "http://elsewhere.test/v1/systemone"
        moved = urllib.response.addinfourl(io.BytesIO(b""), headers, request.full_url, self.code)
        moved.msg = "moved"
        return moved

    http_open = https_open = answer


@pytest.mark.parametrize("code", [301, 302, 303, 307, 308])
def test_call_follows_no_redirect_so_the_key_goes_nowhere_else(code, monkeypatch):
    built, init = [], urllib.request.Request.__init__

    def counted(self, url, *args, **kwargs):
        built.append(url)
        init(self, url, *args, **kwargs)

    monkeypatch.setattr(urllib.request.Request, "__init__", counted)
    transport = Redirecting(code)
    with pytest.raises(jev.CallError, match=f"HTTP {code}") as failed:
        jev.call({}, "ts-hidden", opener=jev.no_redirect_opener(transport))
    assert transport.seen == [(jev.URL, "Bearer ts-hidden")] and failed.value.retries == 0
    assert built == [jev.URL]  # no second request was built for the Location


def test_calls_go_through_an_opener_that_follows_no_redirect():
    default = inspect.signature(jev.call).parameters["opener"].default
    redirects = [
        h for h in default.__self__.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)
    ]
    assert default == jev.OPEN and [type(h) for h in redirects] == [jev.NoRedirect]


class Unreadable(io.BytesIO):
    def read(self, *size):
        raise ConnectionResetError("reset while the error body was read")


DETAIL_LIST = [{"loc": ["body"], "msg": "Field required", "input": {}}, {"msg": "and another"}]


@pytest.mark.parametrize(
    ("body", "named"),
    [
        (b'{"detail": "Invalid API key"}', "HTTP 401 Invalid API key"),
        (json.dumps({"detail": DETAIL_LIST}).encode(), "HTTP 401 Field required; and another"),
        (b'{"error": {"code": "model_not_granted"}}', "HTTP 401 model_not_granted"),
        (b"<html>bad gateway</html>", "HTTP 401"),
        (b"", "HTTP 401"),
        (b"[]", "HTTP 401"),
        (b'{"detail": 5}', "HTTP 401"),
        (b'{"detail": [5, {"msg": 7}, {"loc": []}]}', "HTTP 401"),
        (b'{"error": "flat"}', "HTTP 401"),
        (b"[" * 100_000, "HTTP 401"),
        (Unreadable(), "HTTP 401"),
    ],
)
def test_a_refusal_names_the_code_or_typesafes_detail_and_never_raises_on_an_odd_body(body, named):
    fp = body if isinstance(body, io.IOBase) else io.BytesIO(body)
    opener, _ = answers_after([urllib.error.HTTPError("https://jev.test", 401, "no", {}, fp)])
    with pytest.raises(jev.CallError) as refused:
        jev.call({}, "k", opener=opener)
    assert (
        str(refused.value) == f"https://api.typesafe.ai/v1/systemone refused the request: {named}"
    )


def test_a_refused_header_value_never_prints_the_key():
    def strict(request, timeout):  # as http.client refuses an illegal header value: quoting it
        raise ValueError(f"Invalid header value {request.get_header('Authorization').encode()!r}")

    key = "ts-hidden" + "\n"
    with pytest.raises(ValueError) as refused:
        jev.call({}, key, opener=strict)
    assert "hidden" not in "".join(traceback.format_exception(refused.value))


def test_estimate_counts_a_token_per_1_4_characters_of_the_request_rounded_up():
    body = jev.request("cloze", CLOZE)
    chars = len(json.dumps(body, ensure_ascii=False))
    assert Fraction(7, 5) == jev.CHARS_PER_TOKEN and jev.estimate(body) == -(-chars * 5 // 7)
    # 10 characters (15 with the é escaped) and exactly 14
    assert (jev.estimate({"a": "é"}), jev.estimate({"a": "abcde"})) == (8, 10)


def test_the_refusal_of_an_exported_jev_api_key_says_what_to_do_for_either_kind_of_key(tmp_path):
    env_file = tmp_path / ".env"
    advice = (
        "the gateway's key must come from where JEV_BASE_URL does. If the exported JEV_API_KEY is"
        " an Experiential Labs key, export JEV_BASE_URL=https://api.experientiallabs.ai with it."
        " If it is a TypeSafe key, as a shell set up for climate-risk-agent has, unset JEV_API_KEY"
        " in this shell and keep the gateway key in .env."
    )
    for written, came in [(f"JEV_BASE_URL={GATEWAY}\n", "comes from .env"), ("", "is unset")]:
        env_file.write_text(written, "utf-8")
        with pytest.raises(ValueError) as refused:
            jev.provider({"JEV_API_KEY": "jev-hidden"}, env_file)
        text = f"JEV_API_KEY is set in the environment but JEV_BASE_URL {came}, and {advice}"
        assert str(refused.value) == text


def test_call_fails_at_once_on_403_model_not_granted_and_never_names_the_key():
    sleeps = []
    body = json.dumps({"error": {"type": "permission_error", "code": "model_not_granted"}})
    opener, urls = answers_after([refusal(403, body.encode())])
    with pytest.raises(RuntimeError, match="HTTP 403 model_not_granted") as refused:
        jev.call({}, "secret-key", opener=opener, sleep=sleeps.append)
    assert len(urls) == 1 and sleeps == [] and "secret-key" not in str(refused.value)


def test_load_key_prefers_the_environment_then_the_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('OTHER=1\nexport TYPESAFE_API_KEY="from-file"\n', encoding="utf-8")
    assert jev.load_key(DIRECT, {"TYPESAFE_API_KEY": "from-env"}, env_file) == "from-env"
    assert jev.load_key(DIRECT, {}, env_file) == "from-file"
    with pytest.raises(RuntimeError, match="TYPESAFE_API_KEY"):
        jev.load_key(DIRECT, {}, tmp_path / "missing.env")


def test_each_provider_reads_only_its_own_key_from_the_places_it_may_come_from(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("TYPESAFE_API_KEY=ts-file\nexport JEV_API_KEY='jev-file'\n", "utf-8")
    assert jev.load_key(DIRECT, {"JEV_API_KEY": "jev-env"}, env_file) == "ts-file"
    assert jev.load_key(THROUGH_GATEWAY, {"TYPESAFE_API_KEY": "ts-env"}, env_file) == "jev-file"
    assert jev.load_key(DIRECT, {"TYPESAFE_API_KEY": "ts-env"}, env_file) == "ts-env"
    assert jev.load_key(THROUGH_GATEWAY, {"JEV_API_KEY": "jev-env"}, env_file) == "jev-file"
    assert jev.load_key(ENV_GATEWAY, {"JEV_API_KEY": "jev-env"}, env_file) == "jev-env"
    with pytest.raises(RuntimeError, match="TYPESAFE_API_KEY") as missing:
        jev.load_key(DIRECT, {"JEV_API_KEY": "jev-hidden"})
    assert "JEV_API_KEY" not in str(missing.value) and "hidden" not in str(missing.value)
    with pytest.raises(RuntimeError, match="JEV_API_KEY") as missing:
        jev.load_key(THROUGH_GATEWAY, {"TYPESAFE_API_KEY": "ts-hidden"})
    assert "TYPESAFE_API_KEY" not in str(missing.value) and "hidden" not in str(missing.value)


def test_a_key_is_stripped_and_refused_if_it_still_holds_whitespace_or_controls(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('TYPESAFE_API_KEY= " ts-file "\n', "utf-8")
    assert jev.load_key(DIRECT, {}, env_file) == "ts-file"
    assert jev.load_key(DIRECT, {"TYPESAFE_API_KEY": " ts-env\r\n"}, env_file) == "ts-env"
    for bad in ["ts hidden", "ts\thidden", "ts\x00hidden", "ts\x1bhidden", "ts\x7fhidden"]:
        with pytest.raises(ValueError, match="TYPESAFE_API_KEY") as refused:
            jev.load_key(DIRECT, {"TYPESAFE_API_KEY": bad}, env_file)
        assert "hidden" not in str(refused.value)
    env_file.write_text("JEV_API_KEY=jev\u200bhidden\n", "utf-8")  # a zero-width space
    with pytest.raises(ValueError, match="JEV_API_KEY") as refused:
        jev.load_key(THROUGH_GATEWAY, {}, env_file)
    assert "hidden" not in str(refused.value)


def test_budget_refuses_a_call_that_would_cross_the_limit():
    budget = jev.Budget(limit_usd=0.10, usd_per_input_token=0.042 / 1e6)
    assert budget.allows(2_380_952) and not budget.allows(2_380_953)  # 0.10 / 0.042e-6
    budget.charge(1_000_000)
    assert budget.spent == pytest.approx(0.042)
    assert budget.allows(1_380_952) and not budget.allows(1_400_000)


def test_the_env_file_is_found_from_the_checkout_not_a_fixed_path():
    from pathlib import Path

    module = Path("/elsewhere/earthgym/src/earthgym/climaqa/jev.py")
    assert jev.repo_root(module) == Path("/elsewhere/earthgym")
    assert jev.repo_root(Path(jev.__file__).resolve()) / ".env" == CHECKOUT_ENV_FILE
