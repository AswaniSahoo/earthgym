import email.message
import hashlib
import inspect
import io
import itertools
import json
import subprocess
import urllib.error

import pytest

from earthgym import results
from earthgym.climaqa import jev, third_reader

THROUGH_GATEWAY = jev.PROVIDERS["https://api.experientiallabs.ai"]
UNPACED_GATEWAY = THROUGH_GATEWAY | {"min_interval_s": 0.0}
GIT_REVISION = third_reader.git_revision  # taken before the fixture below stands in for git
# what render reads of a results file's first line
HEAD = {"items_sha256": "f" * 64, "planned": 6, "answered": 6, "complete": True}
PROMPT = "786f7d55f63e44c22435de4ee95e9359b7f073400f850e36330bf54c4982c4a4"  # at 2ed5f18


@pytest.fixture(autouse=True)
def no_checkout_env_file(monkeypatch, tmp_path):
    """No test reads the checkout's .env, which holds the keys, or asks git about the checkout."""
    monkeypatch.setattr(jev, "ENV_FILE", tmp_path / "absent.env")
    monkeypatch.setattr(third_reader, "git_revision", lambda: ("abc1234", False))


def rendered(a):
    return third_reader.render(a, HEAD, third_reader.RESULTS)


MCQ_ROW = {
    "id": "gold/mcq/36",
    "task": "mcq",
    "question": "Which program?",
    "options": "A) w\nB) x\nC) y\nD) z",
    "key": "B) x",
    "model_answer": "A) w",
    "flag": "ambiguous",
    "our_note": "a reason",
}
CLOZE_ROW = {"id": "gold/cloze/4", "task": "cloze", "question": "The <MASK> rises.", "key": "sun"}
CLOZE_ROW |= {"model_answer": "Sun", "flag": "strictness", "our_note": "a reason"}
# every call on CLOZE_ROW: its rotations list the same criteria, so the body has the same length
ESTIMATE = jev.estimate(jev.request("cloze", third_reader.state(CLOZE_ROW)))


def test_state_holds_the_item_and_the_model_answer_but_no_notes_or_labels():
    assert third_reader.state(MCQ_ROW) == {
        "question": "Which program?",
        "options": {"A": "w", "B": "x", "C": "y", "D": "z"},
        "key": "B",
        "model_answer": "A",
    }
    assert third_reader.state(CLOZE_ROW) == {
        "sentence": "The <MASK> rises.",
        "key": "sun",
        "reply": "Sun",
    }


class Canned(io.BytesIO):
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


def reply(headers=None, **fields):
    answer = {"type": "choice", "choice": "same_answer", "confidence": 0.5}
    answer["probabilities"] = {"same_answer": 0.75, "other_correct_word": 0.25, "wrong_reply": 0.0}
    body = {"model": "jev-1.14.0", "answers": {"bucket": answer}, "usage": {"input_tokens": 100}}
    return Canned(json.dumps(body | fields).encode(), headers)


def opener(request, timeout):
    return reply()


class FakeTime:
    """A monotonic clock from 0 and a UTC wall clock from 2026-11-19T00:00:00Z that only `sleep`
    and the calls move, so no test waits for real; each call through `opener` takes `latency`
    seconds. `kwargs` hands a run the two clocks and `sleep`."""

    def __init__(self, latency=1.0):
        self.mono, self.wall_now, self.latency = 0.0, 1795046400.0, latency
        self.sleeps, self.starts = [], []

    def clock(self):
        return self.mono

    def wall(self):
        return self.wall_now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.mono += seconds
        self.wall_now += seconds

    def opener(self, request, timeout):
        self.starts.append(self.mono)
        self.mono += self.latency
        self.wall_now += self.latency
        return reply()

    def kwargs(self):
        return {"sleep": self.sleep, "clock": self.clock, "wall": self.wall}


def cut_off_after(calls):
    """An opener that answers `calls` times, then is refused with HTTP 401."""
    answered = []

    def cut(request, timeout):
        if len(answered) == calls:
            raise urllib.error.HTTPError("https://jev.test", 401, "no", {}, io.BytesIO())
        answered.append(1)
        return reply()

    return cut


def never(request, timeout):
    raise AssertionError("no call may be made")


def busy(status=429, headers=None):
    """A refusal TypeSafe direct tries again, HTTP 429 or 5xx; through the gateway none is."""
    return urllib.error.HTTPError("https://jev.test", status, "busy", headers or {}, io.BytesIO())


def failing(failures, body=None):
    """An opener that raises each of `failures` in turn, then answers with the raw `body`, or
    with a usable reply when it is None."""
    tries = []

    def fail(request, timeout):
        tries.append(1)
        if len(tries) <= len(failures):
            raise failures[len(tries) - 1]
        return reply() if body is None else Canned(body)

    return fail


def study_record(kind, k, retries=0):
    """A record with the fields the 2026-10-31 study's log holds: through the gateway, answered."""
    order = third_reader.rotations("cloze")[0 if kind == "fixed" else k]
    answer = {"type": "choice", "choice": "same_answer", "confidence": 0.5}
    answer["probabilities"] = {"same_answer": 0.75, "other_correct_word": 0.25, "wrong_reply": 0.0}
    usage = {"cost": 4.2e-06, "input_tokens": 100, "is_byok": False, "output_tokens": 50}
    response = {"answers": {"bucket": answer}, "id": f"{kind}-{k}", "model": "jev-latest"}
    response |= {"provider": "typesafe", "usage": usage}
    record = {"at": "2026-11-19T00:00:00Z", "id": "gold/cloze/4", "model_requested": "jev-latest"}
    record |= {"order": order, "pass": kind, "provider": "experientiallabs", "response": response}
    return record | {"retries": retries, "run": k, "seconds": 1.0, "task": "cloze"}


def failed_record(kind, k, retries):
    """What a call that stayed busy through its tries leaves in the log."""
    kept = {
        name: v for name, v in study_record(kind, k).items() if name not in ("response", "seconds")
    }
    failure = {"error": "HTTPError", "status": 429, "estimate": ESTIMATE, "body": None}
    return kept | {"retries": retries, "request_id": None} | failure


def write_log(out, records):
    out.write_text("".join(json.dumps(r) + "\n" for r in records), "utf-8")


def test_rotations_put_each_option_first_once():
    assert third_reader.rotations("cloze") == [
        ["same_answer", "other_correct_word", "wrong_reply"],
        ["other_correct_word", "wrong_reply", "same_answer"],
        ["wrong_reply", "same_answer", "other_correct_word"],
    ]


def test_run_makes_five_fixed_calls_and_one_per_other_rotation_per_item(tmp_path):
    out = tmp_path / "responses.jsonl"
    records = third_reader.run([CLOZE_ROW], "k", out, opener=opener)
    assert [(r["pass"], r["run"]) for r in records] == [("fixed", k) for k in range(1, 6)] + [
        ("rotated", 1),
        ("rotated", 2),
    ]
    assert records[5]["order"] == third_reader.rotations("cloze")[1]


def test_run_calls_each_item_five_times_and_logs_raw_responses_but_never_the_key(tmp_path):
    out = tmp_path / "responses.jsonl"
    records = third_reader.run(
        [CLOZE_ROW, CLOZE_ROW | {"id": "gold/cloze/5"}], "secret-key", out, opener=opener
    )
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(records) == len(lines) == 14 and "secret-key" not in out.read_text(encoding="utf-8")
    first = json.loads(lines[0])
    assert (first["id"], first["run"], first["response"]["usage"]["input_tokens"]) == (
        "gold/cloze/4",
        1,
        100,
    )


def test_run_starts_a_call_only_if_four_tries_at_its_own_estimate_fit_the_budget(tmp_path):
    budget = jev.Budget(limit_usd=150 + 4 * ESTIMATE, usd_per_input_token=1.0)  # two 100s fit
    records = third_reader.run([CLOZE_ROW], "k", tmp_path / "r.jsonl", opener=opener, budget=budget)
    assert len(records) == 2 and budget.spent == 200


def test_through_the_gateway_a_call_needs_one_try_at_its_estimate_to_fit_the_budget(tmp_path):
    budget = jev.Budget(limit_usd=150 + ESTIMATE, usd_per_input_token=1.0)  # two 100s fit
    records = third_reader.run(
        [CLOZE_ROW],
        "k",
        tmp_path / "r.jsonl",
        opener=opener,
        budget=budget,
        provider=UNPACED_GATEWAY,
    )
    assert len(records) == 2 and budget.spent == 200


def test_run_counts_each_retried_try_against_the_budget_as_charged(tmp_path):
    fake = FakeTime()
    budget = jev.Budget(limit_usd=250 + 4 * ESTIMATE, usd_per_input_token=1.0)
    records = third_reader.run(
        [CLOZE_ROW],
        "k",
        tmp_path / "r.jsonl",
        opener=failing([busy()]),
        budget=budget,
        **fake.kwargs(),
    )
    assert [r["retries"] for r in records] == [1, 0] and budget.spent == 300
    assert fake.sleeps == [10.0]


def test_run_sends_the_gateways_model_and_records_provider_model_time_and_request_id(tmp_path):
    fake, sent = FakeTime(), []

    def gateway(request, timeout):
        sent.append((request.full_url, json.loads(request.data)["model"]))
        return reply({"X-Request-Id": f"gw-{len(sent)}"}, model="jev-latest", provider="typesafe")

    out = tmp_path / "r.jsonl"
    third_reader.run(
        [CLOZE_ROW], "k", out, opener=gateway, provider=UNPACED_GATEWAY, **fake.kwargs()
    )
    assert sent == [("https://api.experientiallabs.ai/v1/systemone", "jev-latest")] * 7
    logged = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert (logged[0]["provider"], logged[0]["model_requested"], logged[0]["at"]) == (
        "experientiallabs",
        "jev-latest",
        "2026-11-19T00:00:00Z",
    )
    assert [r["request_id"] for r in logged] == [f"gw-{n}" for n in range(1, 8)]
    assert (logged[0]["response"]["model"], logged[0]["response"]["provider"]) == (
        "jev-latest",
        "typesafe",
    )


def test_run_starts_gateway_calls_7_5_s_apart_without_sleeping_for_real(tmp_path):
    fake = FakeTime(latency=1.0)
    third_reader.run(
        [CLOZE_ROW],
        "k",
        tmp_path / "r.jsonl",
        opener=fake.opener,
        provider=THROUGH_GATEWAY,
        **fake.kwargs(),
    )
    assert [b - a for a, b in itertools.pairwise(fake.starts)] == [7.5] * 6
    assert fake.sleeps == [6.5] * 6
    fake.sleeps.clear()
    third_reader.run([CLOZE_ROW], "k", tmp_path / "d.jsonl", opener=fake.opener, **fake.kwargs())
    assert fake.sleeps == []  # TypeSafe direct is not paced


def test_pacing_follows_the_monotonic_clock_and_at_the_utc_wall_clock(tmp_path):
    fake, out = FakeTime(latency=1.0), tmp_path / "r.jsonl"

    def set_back(request, timeout):  # the wall clock is set back an hour during each call
        fake.wall_now -= 3600
        return fake.opener(request, timeout)

    third_reader.run(
        [CLOZE_ROW], "k", out, opener=set_back, provider=THROUGH_GATEWAY, **fake.kwargs()
    )
    assert fake.sleeps == [6.5] * 6
    at = [json.loads(line)["at"] for line in out.read_text(encoding="utf-8").splitlines()]
    assert at[:2] == ["2026-11-19T00:00:00Z", "2026-11-18T23:00:07Z"]


def test_run_picks_up_where_a_cut_off_run_stopped_and_sends_only_the_failed_call_again(tmp_path):
    out = tmp_path / "r.jsonl"
    with pytest.raises(jev.CallError, match="HTTP 401"):
        third_reader.run([CLOZE_ROW], "k", out, opener=cut_off_after(3))
    assert len(out.read_text(encoding="utf-8").splitlines()) == 4  # 3 answered, 1 failed
    fake, budget = FakeTime(), jev.Budget(limit_usd=10_000, usd_per_input_token=1.0)
    records = third_reader.run(
        [CLOZE_ROW], "k", out, opener=fake.opener, budget=budget, **fake.kwargs()
    )
    assert len(fake.starts) == 4 and budget.spent == 300 + ESTIMATE + 400
    plan = [("fixed", k) for k in range(1, 6)] + [("rotated", 1), ("rotated", 2)]
    assert [(r["pass"], r["run"]) for r in records if "error" not in r] == plan
    logged = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(r["pass"], r["run"]) for r in logged if "error" not in r] == plan
    assert [(r["pass"], r["run"]) for r in logged if "error" in r] == [("fixed", 4)]


def test_run_refuses_to_resume_a_log_made_through_another_provider(tmp_path):
    out = tmp_path / "r.jsonl"
    with pytest.raises(jev.CallError, match="HTTP 401"):
        third_reader.run([CLOZE_ROW], "k", out, opener=cut_off_after(2))  # TypeSafe direct
    with pytest.raises(ValueError, match="typesafe"):
        third_reader.run([CLOZE_ROW], "k", out, opener=never, provider=THROUGH_GATEWAY)


SPREAD = {"same_answer": 1.0, "other_correct_word": 0.0, "wrong_reply": 0.0}
NOT_OFFERED = json.dumps(
    {
        "model": "jev-latest",
        "answers": {"bucket": {"choice": "ambiguous", "probabilities": SPREAD}},
        "usage": {"input_tokens": 100},
    }
).encode()
FAILURES = {  # each way a call can end without a usable reply, and what its record then says
    "all tries busy": (
        [busy(headers={"x-typesafe-request-id": "ts-4"})] * 4,
        None,
        "HTTPError",
        429,
        3,
        "ts-4",
    ),
    "a timeout after a retry": (
        [busy(503), TimeoutError("timed out")],
        None,
        "TimeoutError",
        None,
        1,
        None,
    ),
    "no route": ([urllib.error.URLError("no route to host")], None, "URLError", None, 0, None),
    "a reset": (
        [ConnectionResetError("reset by peer")],
        None,
        "ConnectionResetError",
        None,
        0,
        None,
    ),
    "a 200 not JSON": ([], b"<html>busy</html>", "JSONDecodeError", 200, 0, None),
    "a 200 without usage": (
        [],
        b'{"model": "jev-latest", "answers": {}}',
        "KeyError",
        200,
        0,
        None,
    ),
    "a 200 whose choice was not offered": ([], NOT_OFFERED, "ValueError", 200, 0, None),
}


@pytest.mark.parametrize(
    ("failures", "body", "error", "status", "retries", "request_id"),
    FAILURES.values(),
    ids=FAILURES,
)
def test_a_failed_call_is_logged_with_its_error_retries_and_estimate_then_raised(
    tmp_path, failures, body, error, status, retries, request_id
):
    out, fake = tmp_path / "r.jsonl", FakeTime()
    budget = jev.Budget(limit_usd=10_000, usd_per_input_token=1.0)
    with pytest.raises(jev.CallError):
        third_reader.run(
            [CLOZE_ROW],
            "ts-hidden",
            out,
            opener=failing(failures, body),
            budget=budget,
            **fake.kwargs(),
        )
    (logged,) = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert (logged["error"], logged["status"], logged["retries"]) == (error, status, retries)
    assert (logged["request_id"], logged["body"]) == (request_id, body and body.decode())
    assert logged["estimate"] == ESTIMATE and budget.tokens == ESTIMATE * (1 + retries)
    assert (logged["id"], logged["pass"], logged["run"], logged["provider"]) == (
        "gold/cloze/4",
        "fixed",
        1,
        "typesafe",
    )
    assert "response" not in logged and "hidden" not in out.read_text(encoding="utf-8")


def test_an_unusable_200_keeps_its_raw_body_cut_to_2000_characters(tmp_path):
    out, raw = tmp_path / "r.jsonl", ("<html>" + "x" * 3000).encode()
    with pytest.raises(jev.CallError, match="JSONDecodeError"):
        third_reader.run([CLOZE_ROW], "k", out, opener=failing([], raw))
    (logged,) = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert logged["body"] == raw.decode()[:2000] and logged["status"] == 200


def test_a_resumed_run_charges_every_logged_try_and_sends_only_the_failed_calls_again(tmp_path):
    out, fake = tmp_path / "r.jsonl", FakeTime()
    write_log(out, [study_record("fixed", 1, retries=2), failed_record("fixed", 2, retries=3)])
    budget = jev.Budget(limit_usd=10_000, usd_per_input_token=1.0)
    third_reader.run(
        [CLOZE_ROW],
        "k",
        out,
        opener=fake.opener,
        budget=budget,
        provider=THROUGH_GATEWAY,
        **fake.kwargs(),
    )
    assert len(fake.starts) == 6  # fixed 2 again, fixed 3 to 5, rotated 1 and 2; never fixed 1
    assert budget.tokens == 100 * 3 + ESTIMATE * 4 + 100 * 6
    logged = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(r["pass"], r["run"], "error" in r) for r in logged[:4]] == [
        ("fixed", 1, False),
        ("fixed", 2, True),
        ("fixed", 2, False),
        ("fixed", 3, False),
    ]


GOOD = json.dumps(study_record("fixed", 1))


def without(name):
    """A study record without `name`."""
    return json.dumps({k: v for k, v in study_record("fixed", 2).items() if k != name})


@pytest.mark.parametrize(
    ("lines", "number", "what"),
    [
        ([GOOD, ""], 2, "blank"),
        ([GOOD, "  "], 2, "blank"),
        ([GOOD, GOOD[:40]], 2, "torn"),
        ([without("provider"), GOOD], 1, "provider"),
        ([GOOD, without("retries")], 2, "retries"),
        ([GOOD, without("order")], 2, "order"),
        ([GOOD, "[1, 2]"], 2, "not a JSON object"),
        ([GOOD, json.dumps(study_record("fixed", 2, retries=-1))], 2, "no count of retries"),
        ([GOOD, json.dumps(study_record("fixed", 2) | {"retries": "1"})], 2, "no count of retries"),
    ],
    ids=[
        "blank",
        "spaces",
        "torn",
        "no provider",
        "no retries",
        "no order",
        "not an object",
        "negative retries",
        "retries not a number",
    ],
)
def test_a_torn_or_blank_line_or_a_record_without_provider_or_retries_names_its_line(
    tmp_path, lines, number, what
):
    out = tmp_path / "r.jsonl"
    out.write_text("\n".join(lines) + "\n", "utf-8")
    where = rf"r\.jsonl:{number}: .*{what}"
    with pytest.raises(ValueError, match=where):
        third_reader.run([CLOZE_ROW], "k", out, opener=never, provider=THROUGH_GATEWAY)
    with pytest.raises(ValueError, match=where):
        third_reader.load(out)
    assert not (tmp_path / "r.jsonl.lock").exists()


def test_a_second_launch_is_refused_while_the_lock_file_exists_and_leaves_it(tmp_path):
    out, lock = tmp_path / "r.jsonl", tmp_path / "r.jsonl.lock"
    lock.touch()
    with pytest.raises(RuntimeError, match="delete it only if no run is active") as refused:
        third_reader.run([CLOZE_ROW], "k", out, opener=never)
    assert str(lock) in str(refused.value) and lock.exists() and not out.exists()


def test_the_lock_file_is_held_while_a_run_calls_and_removed_however_it_ends(tmp_path):
    out, lock, held = tmp_path / "r.jsonl", tmp_path / "r.jsonl.lock", []

    def watching(request, timeout):
        held.append(lock.exists())
        return reply()

    third_reader.run([CLOZE_ROW], "k", out, opener=watching)
    assert held == [True] * 7 and not lock.exists()
    broke = jev.Budget(limit_usd=0)
    third_reader.run([CLOZE_ROW | {"id": "gold/cloze/5"}], "k", out, opener=never, budget=broke)
    assert not lock.exists()
    with pytest.raises(jev.CallError):
        third_reader.run([CLOZE_ROW | {"id": "gold/cloze/6"}], "k", out, opener=cut_off_after(0))
    assert not lock.exists()


def test_main_refuses_an_unvetted_base_url_before_it_reads_a_key_or_calls(monkeypatch):
    touched = []
    monkeypatch.setenv("JEV_BASE_URL", "https://api.example.com")
    monkeypatch.setattr("sys.argv", ["third_reader", "run"])
    monkeypatch.setattr(jev, "load_key", lambda *args: touched.append("key"))
    monkeypatch.setattr(third_reader, "run", lambda *args, **kwargs: touched.append("run"))
    with pytest.raises(ValueError, match="JEV_BASE_URL"):
        third_reader.main()
    assert touched == []


def test_main_reads_only_the_key_of_the_provider_it_picks(monkeypatch, tmp_path):
    sheet = tmp_path / "sheet.csv"
    sheet.write_text("id,task\ngold/cloze/4,cloze\n", "utf-8")
    monkeypatch.setattr(third_reader.expert_sheet, "SHEET", sheet)
    for name in ["JEV_BASE_URL", "JEV_MIN_INTERVAL_S"]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TYPESAFE_API_KEY", "ts-key")
    monkeypatch.setenv("JEV_API_KEY", "gw-key")
    monkeypatch.setattr("sys.argv", ["third_reader", "run"])
    runs = []

    def run(rows, key, provider):
        runs.append((key, provider["name"]))
        return []

    monkeypatch.setattr(third_reader, "run", run)
    third_reader.main()
    monkeypatch.setenv("JEV_BASE_URL", "https://api.experientiallabs.ai")
    third_reader.main()
    assert runs == [("ts-key", "typesafe"), ("gw-key", "experientiallabs")]


def test_kappa_matches_a_hand_computed_case():
    # observed agreement 3/4; chance agreement 0.5 * 0.25 + 0.5 * 0.75 = 0.5; kappa 0.5
    assert third_reader.kappa(["x", "x", "y", "y"], ["x", "y", "y", "y"]) == pytest.approx(0.5)
    assert third_reader.kappa(["x", "x"], ["x", "x"]) == 1.0  # one label throughout


def test_brier_scores_a_probability_spread_against_one_label():
    assert third_reader.brier({"a": 1.0, "b": 0.0}, "a") == 0.0
    assert third_reader.brier({"a": 1.0, "b": 0.0}, "b") == 2.0
    assert third_reader.brier({"a": 0.5, "b": 0.5}, "a") == 0.5


def test_stability_gives_the_modal_choice_and_pairwise_agreement():
    summary = third_reader.stability(["a", "a", "a", "b", "a"])
    assert summary == {"modal": "a", "all_same": False, "agreement": 0.6}  # 6 of 10 pairs


def test_reference_labels_come_from_the_miss_notes_and_the_blind_sort():
    mine, blind = third_reader.mine(), third_reader.blind_sort()
    assert (len(mine), len(blind)) == (61, 33)
    assert set(mine.values()) <= {n for task in jev.BUCKETS.values() for n in task}
    agree = sum(mine[i] == blind[i] for i in blind)
    assert agree == 32  # 31 of 33 at the review; 157 has since moved to the blind sort's label


def test_a_results_row_keeps_only_what_the_report_reads():
    logged = study_record("rotated", 2, retries=1) | {"request_id": "gw-1"}
    assert third_reader.compact(logged) == {
        "id": "gold/cloze/4",
        "task": "cloze",
        "pass": "rotated",
        "run": 2,
        "order": third_reader.rotations("cloze")[2],
        "choice": "same_answer",
        "probabilities": {"same_answer": 0.75, "other_correct_word": 0.25, "wrong_reply": 0.0},
        "retries": 1,
        "input_tokens": 100,
        "output_tokens": 50,
        "seconds": 1.0,
        "provider": "experientiallabs",
        "model_requested": "jev-latest",
        "reply_model": "jev-latest",
        "reply_provider": "typesafe",
        "at": "2026-11-19T00:00:00Z",
    }
    assert third_reader.compact(failed_record("fixed", 2, retries=3)) == {
        "id": "gold/cloze/4",
        "task": "cloze",
        "pass": "fixed",
        "run": 2,
        "error": "HTTPError",
        "retries": 3,
        "estimate": ESTIMATE,
        "provider": "experientiallabs",
        "model_requested": "jev-latest",
        "at": "2026-11-19T00:00:00Z",
    }


def test_the_results_header_gives_the_run_as_decision_0019_lays_out():
    later = study_record("rotated", 1) | {"at": "2026-11-19T00:00:08Z"}
    head = third_reader.header([study_record("fixed", 1), later])
    assert head == {
        "task": "climaqa_third_reader",
        "task_args": {"runs": 5},
        "model": "experientiallabs/jev-latest",
        "items_sha256": third_reader.items_sha256(
            [row for row in third_reader.sheet() if row["id"] == "gold/cloze/4"]
        ),
        "started": "2026-11-19T00:00:00Z",
        "completed": "2026-11-19T00:00:09Z",  # the last call started at 00:00:08 and took 1 s
        "commit": "2ed5f18 (dirty)",
        "settings": {},
        "tokens": {"input": 200, "output": 100},
        "planned": len(list(third_reader.schedule(third_reader.sheet()))),
        "answered": 2,
        "complete": False,
        "log": "responses.jsonl",
        "log_dir": "logs/2026-10-31-jev",
    }


def test_the_results_step_keeps_each_call_and_the_report_step_reads_only_them(
    monkeypatch, tmp_path
):
    log, kept, report = tmp_path / "responses.jsonl", tmp_path / "kept.jsonl", tmp_path / "r.md"
    plan = [("fixed", k) for k in range(1, 6)] + [("rotated", 1), ("rotated", 2)]
    records = [study_record(kind, k) for kind, k in plan]
    write_log(log, records)
    for name, path in [("LOG", log), ("RESULTS", kept), ("REPORT", report)]:
        monkeypatch.setattr(third_reader, name, path)
    monkeypatch.setattr("sys.argv", ["third_reader", "results"])
    third_reader.main()
    head, rows = results.read(kept)
    assert head == third_reader.header(records) and head["log_dir"] == str(tmp_path)
    assert rows == [third_reader.compact(r) for r in records]
    log.unlink()  # the report needs the results file alone
    monkeypatch.setattr("sys.argv", ["third_reader", "report"])
    third_reader.main()
    reference = third_reader.mine(), third_reader.blind_sort()
    expected = third_reader.render(third_reader.analyse(rows, *reference), head, kept)
    assert report.read_text("utf-8") == expected


def git(answers):
    """A stand-in for subprocess.run that answers each git command, by its verb, from `answers`."""

    def runner(args, **kwargs):
        answer = answers[args[1]]
        if isinstance(answer, BaseException):
            raise answer
        return subprocess.CompletedProcess(args, 0, stdout=answer, stderr="")

    return runner


def test_git_revision_gives_the_short_head_and_whether_the_tree_has_changes():
    clean = {"rev-parse": "abc1234\n", "status": ""}
    assert GIT_REVISION(git(clean)) == ("abc1234", False)
    assert GIT_REVISION(git(clean | {"status": " M src/a.py\n"})) == ("abc1234", True)
    no_git = clean | {"rev-parse": FileNotFoundError("git")}
    not_a_checkout = clean | {"rev-parse": subprocess.CalledProcessError(128, ["git"])}
    assert GIT_REVISION(git(no_git)) == GIT_REVISION(git(not_a_checkout)) == ("unknown", "unknown")


def test_each_record_holds_the_commit_and_tree_state_taken_when_the_run_starts(
    monkeypatch, tmp_path
):
    asked = []

    def revision():
        asked.append(1)
        return "abc1234", True

    monkeypatch.setattr(third_reader, "git_revision", revision)
    out = tmp_path / "r.jsonl"
    third_reader.run([CLOZE_ROW], "k", out, opener=opener)
    logged = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert {(r["commit"], r["dirty"]) for r in logged} == {("abc1234", True)} and asked == [1]
    assert "commit" not in third_reader.compact(logged[0])


def test_the_header_reads_the_commit_from_the_records_and_falls_back_for_the_study():
    study = study_record("fixed", 1)
    assert third_reader.header([study])["commit"] == "2ed5f18 (dirty)"  # git reflog
    for revision, commit in [
        (("abc1234", True), "abc1234 (dirty)"),
        (("abc1234", False), "abc1234"),
        (("unknown", "unknown"), "unknown"),
    ]:
        logged = study | dict(zip(("commit", "dirty"), revision, strict=True))
        assert third_reader.header([logged])["commit"] == commit


def test_the_items_revision_hashes_what_each_request_sends_in_id_order():
    pair = [row for row in third_reader.sheet() if row["id"] in ("gold/cloze/4", "gold/mcq/36")]
    sent = [third_reader.state(row) for row in sorted(pair, key=lambda row: row["id"])]
    canonical = json.dumps(sent, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert third_reader.items_sha256(pair) == hashlib.sha256(canonical.encode()).hexdigest()
    assert third_reader.items_sha256(pair[::-1]) == third_reader.items_sha256(pair)
    filled = [
        row | {"verdict": "kept", "accepted_answers": "x", "expert_note": "y"} for row in pair
    ]
    assert third_reader.items_sha256(filled) == third_reader.items_sha256(pair)  # never sent
    edited = [pair[0] | {"question": pair[0]["question"] + " Why?"}, pair[1]]
    assert third_reader.items_sha256(edited) != third_reader.items_sha256(pair)
    with pytest.raises(ValueError, match="gold/cloze/99999"):
        third_reader.header([study_record("fixed", 1) | {"id": "gold/cloze/99999"}])


def test_the_headers_token_totals_are_the_sums_of_its_rows():
    records = [study_record("fixed", k) for k in range(1, 4)] + [failed_record("fixed", 4, 1)]
    answered = [third_reader.compact(r) for r in records if "error" not in r]
    sums = {k: sum(r[f"{k}_tokens"] for r in answered) for k in ("input", "output")}
    assert third_reader.header(records)["tokens"] == sums == {"input": 300, "output": 150}


@pytest.mark.parametrize("status", [429, 503])
def test_through_the_gateway_a_refusal_is_logged_and_charged_once_then_sent_on_relaunch(
    tmp_path, status
):
    out, fake = tmp_path / "r.jsonl", FakeTime()
    budget = jev.Budget(limit_usd=10_000, usd_per_input_token=1.0)
    with pytest.raises(jev.CallError, match=f"HTTP {status}"):
        third_reader.run(
            [CLOZE_ROW],
            "k",
            out,
            opener=failing([busy(status)]),
            budget=budget,
            provider=THROUGH_GATEWAY,
            **fake.kwargs(),
        )
    (logged,) = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert (logged["error"], logged["status"], logged["retries"]) == ("HTTPError", status, 0)
    assert budget.tokens == ESTIMATE and fake.sleeps == []
    relaunch = jev.Budget(limit_usd=10_000, usd_per_input_token=1.0)
    third_reader.run(
        [CLOZE_ROW],
        "k",
        out,
        opener=fake.opener,
        budget=relaunch,
        provider=THROUGH_GATEWAY,
        **fake.kwargs(),
    )
    assert len(fake.starts) == 7 and relaunch.tokens == ESTIMATE + 700  # fixed 1 sent again


def test_jev_min_interval_s_paces_typesafe_direct_calls_as_well(tmp_path):
    fake = FakeTime(latency=0.5)
    paced = jev.provider({"JEV_BASE_URL": "https://api.typesafe.ai", "JEV_MIN_INTERVAL_S": "2"})
    third_reader.run(
        [CLOZE_ROW], "k", tmp_path / "r.jsonl", opener=fake.opener, provider=paced, **fake.kwargs()
    )
    assert [b - a for a, b in itertools.pairwise(fake.starts)] == [2.0] * 6
    assert fake.sleeps == [1.5] * 6


def record(item, task, k, choice, probabilities, seconds):
    """A call as the results file keeps it, and so as the analysis reads it."""
    return {
        "id": item,
        "task": task,
        "pass": "fixed",
        "run": k,
        "order": list(jev.BUCKETS[task]),
        "choice": choice,
        "probabilities": probabilities,
        "retries": 0,
        "input_tokens": 100,
        "seconds": seconds,
        "provider": "typesafe",
        "model_requested": "jev-1.14.0",
        "reply_model": "jev-1.14.0",
        "reply_provider": None,
        "at": "2026-11-19T00:00:00Z",
    }


SAME, OTHER, WRONG = "same_answer", "other_correct_word", "wrong_reply"
RECORDS = [
    record("c1", "cloze", 1, SAME, {SAME: 0.8, OTHER: 0.2, WRONG: 0.0}, 0.1),
    record("c1", "cloze", 2, SAME, {SAME: 0.6, OTHER: 0.4, WRONG: 0.0}, 0.2),
    record("c2", "cloze", 1, OTHER, {SAME: 0.1, OTHER: 0.9, WRONG: 0.0}, 0.3),
    record("c2", "cloze", 2, SAME, {SAME: 0.55, OTHER: 0.45, WRONG: 0.0}, 0.4),  # a tie
    record("m1", "mcq", 1, "key_right", {"key_right": 1.0, "ambiguous": 0.0}, 0.5),
    record("m1", "mcq", 2, "key_right", {"key_right": 1.0, "ambiguous": 0.0}, 0.6),
]
MINE = {"c1": SAME, "c2": OTHER, "m1": "key_right"}
BLIND = {"c1": SAME, "c2": OTHER}


def test_analyse_gives_agreement_calibration_stability_cost_and_latency():
    a = third_reader.analyse(RECORDS, MINE, BLIND)
    assert a["modal"] == {"c1": SAME, "c2": OTHER, "m1": "key_right"} and a["others"] == {}
    assert (a["kappa_mine"], a["kappa_blind"], a["kappa_mine_blind"]) == (1.0, 1.0, 1.0)
    assert a["brier"] == pytest.approx((0.20 + 0.3125) / 2) and a["brier_items"] == 2
    assert a["all_same"] == 2 and a["agreement"] == pytest.approx(2 / 3)
    assert (a["calls"], a["input_tokens"]) == (6, 600)
    assert a["usd"] == pytest.approx(600 * 0.042 / 1e6)
    assert a["median_seconds"] == pytest.approx(0.35) and a["models"] == ["jev-1.14.0"]


def test_render_reports_the_headline_numbers():
    text = rendered(third_reader.analyse(RECORDS, MINE, BLIND))
    assert "| Jev against the first sort | 3 | 1.000 |" in text
    assert "| Jev against the reviewer's blind sort | 2 | 1.000 |" in text
    assert "Brier score where both sorts agree: 0.256 over 2 items" in text


def test_render_names_the_provider_the_model_asked_for_what_answered_and_the_dates():
    relayed = {"reply_model": "jev-latest", "reply_provider": "typesafe"}
    sent = {"provider": "experientiallabs", "model_requested": "jev-latest"}
    records = [r | sent | relayed for r in RECORDS]
    records[0] |= {"retries": 1}
    records[-1] |= {"at": "2026-11-20T00:00:07Z"}
    flat = " ".join(rendered(third_reader.analyse(records, MINE, BLIND)).split())
    assert (
        "Provider experientiallabs, model requested jev-latest; the replies name model jev-latest"
        " and provider typesafe. Calls made on 2026-11-19, 2026-11-20 (UTC)." in flat
    )
    assert (
        "Spend against the cap: answered calls 6, failed calls 0, tries 7 (retries 1), input"
        " tokens 700, $0.0000 at TypeSafe's list price (output tokens are free)." in flat
    )


def test_analysis_ignores_failed_calls_and_the_spend_line_counts_every_charged_try():
    kept = ("id", "task", "pass", "run", "provider", "model_requested", "at")
    failed = {k: RECORDS[0][k] for k in kept} | {"error": "TimeoutError", "retries": 1}
    failed |= {"estimate": 300}
    records = [RECORDS[0] | {"retries": 2}, *RECORDS[1:], failed]
    a, plain = (
        third_reader.analyse(records, MINE, BLIND),
        third_reader.analyse(RECORDS, MINE, BLIND),
    )
    for name in ["modal", "kappa_mine", "kappa_blind", "brier", "agreement", "median_seconds"]:
        assert a[name] == plain[name]
    assert (a["calls"], a["failed"], a["tries"], a["retries"]) == (6, 1, 10, 3)
    assert a["input_tokens"] == 600 + 2 * 100 + 2 * 300  # retried tries, and the failed call's
    flat = " ".join(rendered(a).split())
    assert (
        "Spend against the cap: answered calls 6, failed calls 1, tries 10 (retries 3), input"
        " tokens 1400, $0.0001 at TypeSafe's list price (output tokens are free)." in flat
    )


def test_a_log_shaped_like_the_study_loads_resumes_with_no_call_and_reports(tmp_path):
    out = tmp_path / "responses.jsonl"
    plan = [("fixed", k) for k in range(1, 6)] + [("rotated", 1), ("rotated", 2)]
    write_log(out, [study_record(kind, k) for kind, k in plan])
    records = third_reader.load(out)
    budget = jev.Budget(limit_usd=10_000, usd_per_input_token=1.0)
    resumed = third_reader.run(
        [CLOZE_ROW], "k", out, opener=never, budget=budget, provider=THROUGH_GATEWAY
    )
    assert resumed == records and len(records) == 7 and budget.tokens == 700
    rows = [third_reader.compact(r) for r in records]
    a = third_reader.analyse(rows, {"gold/cloze/4": SAME}, {})
    flat = " ".join(rendered(a).split())
    assert (
        "Provider experientiallabs, model requested jev-latest; the replies name model jev-latest"
        " and provider typesafe." in flat
    )
    assert "answered calls 7, failed calls 0, tries 7 (retries 0), input tokens 700," in flat


def rotated_item(item, picks):
    """Fixed run 1 plus two rotated calls; picks maps each order's index to the chosen bucket."""
    orders = third_reader.rotations("cloze")
    out = []
    for r, order in enumerate(orders):
        choice = picks[r]
        spread = {name: float(name == choice) for name in order}
        rec = record(item, "cloze", 1 if r == 0 else r, choice, spread, 0.1)
        out.append(rec | {"pass": "fixed" if r == 0 else "rotated", "order": order})
    return out


def test_analyse_measures_first_position_bias_over_rotated_orders():
    leaning = rotated_item("c3", {0: SAME, 1: OTHER, 2: WRONG})  # always the first listed
    blind = rotated_item("c4", {0: SAME, 1: SAME, 2: SAME})  # the same whatever the order
    a = third_reader.analyse(leaning + blind, {"c4": SAME}, {})
    assert (a["first_hits"], a["rotation_calls"]) == (4, 6)  # 3 of 3 and 1 of 3
    assert a["first_expected"] == pytest.approx(1 / 3) and a["first_gain"] == pytest.approx(0.5)
    assert a["rotated_modal"]["c4"] == SAME
    text = rendered(a)
    assert "first-listed option in 4 of 6 rotated-order calls (0.667; 0.333 if order" in text


def test_render_states_the_items_revision_prompt_results_file_and_reference_sorts(monkeypatch):
    text = rendered(third_reader.analyse(RECORDS, MINE, BLIND))
    sources = [
        "Config and sources:",
        "",
        "- Items: the fields each request sends of the 3 items in"
        f" reports/climaqa/expert_review_v2.csv, sha256 {'f' * 64} of their canonical JSON in id"
        " order.",
        "- Prompt: INSTRUCTIONS and BUCKETS in src/earthgym/climaqa/jev.py, unchanged since"
        f" 2ed5f18 (sha256 {PROMPT} of their canonical JSON). The requests set no seed and no"
        " sampling setting.",
        "- Calls: reports/climaqa/results/2026-10-31-jev-third-reader.jsonl, which this report is"
        " rendered from.",
        "- First sort: reports/climaqa/runs/2026-10-30-gemini-3.8-flash-mcq-misses.md and"
        " reports/climaqa/runs/2026-10-30-gemini-3.8-flash-cloze-misses.md.",
        "- Reviewer's blind sort: docs/reviews/phase-2-climaqa-port.md, section 3.",
        "",
    ]
    assert text.endswith("\n".join(sources))
    monkeypatch.setattr(third_reader, "STUDY_PROMPT_SHA256", "0" * 64)
    assert "jev.py, changed since 2ed5f18 (sha256" in rendered(
        third_reader.analyse(RECORDS, MINE, BLIND)
    )


def test_an_incomplete_rotation_set_is_left_out_of_the_rotation_measures_and_counted():
    leaning = rotated_item("c3", {0: SAME, 1: OTHER, 2: WRONG})
    cut = rotated_item("c4", {0: SAME, 1: SAME, 2: SAME})[:2]  # its last rotation not answered
    a = third_reader.analyse(leaning + cut, {"c3": SAME, "c4": SAME}, {})
    assert (a["first_hits"], a["rotation_calls"], a["incomplete_sets"]) == (3, 3, 1)
    assert set(a["rotated_modal"]) == {"c3"}


def one_item_sheet(monkeypatch, tmp_path):
    """Points the expert sheet at one cloze item, gold/cloze/4, whose plan is 7 calls."""
    sheet = tmp_path / "sheet.csv"
    row = "gold/cloze/4,cloze,The <MASK> rises.,,sun,Sun"
    sheet.write_text(f"id,task,question,options,key,model_answer\n{row}\n", "utf-8")
    monkeypatch.setattr(third_reader.expert_sheet, "SHEET", sheet)


def test_the_header_counts_planned_and_answered_calls_and_whether_all_were_answered(
    monkeypatch, tmp_path
):
    one_item_sheet(monkeypatch, tmp_path)
    plan = [("fixed", k) for k in range(1, 6)] + [("rotated", 1), ("rotated", 2)]
    records = [study_record(kind, k) for kind, k in plan]
    head = third_reader.header(records)
    assert (head["planned"], head["answered"], head["complete"]) == (7, 7, True)
    head = third_reader.header(records[:4] + [failed_record("fixed", 5, 0)])
    assert (head["planned"], head["answered"], head["complete"]) == (7, 4, False)


def test_a_partial_runs_report_says_so_and_a_complete_ones_does_not():
    a = third_reader.analyse(RECORDS, MINE, BLIND)
    partial = third_reader.render(
        a, HEAD | {"answered": 4, "complete": False}, third_reader.RESULTS
    )
    note = (
        "This run is partial: 4 of 6 planned calls answered, so the numbers below cover only"
        " those calls; 0 incomplete rotation sets are left out of the rotation measures."
    )
    assert note in partial and partial.replace(note + "\n\n", "") == rendered(a)
    assert "partial" not in rendered(a)


def test_main_prints_what_it_calls_through_and_says_when_a_run_stopped_early(
    monkeypatch, tmp_path, capsys
):
    one_item_sheet(monkeypatch, tmp_path)
    log = tmp_path / "responses.jsonl"
    monkeypatch.setattr(third_reader, "LOG", log)
    for name in ["TYPESAFE_API_KEY", "JEV_MIN_INTERVAL_S"]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("JEV_BASE_URL", "https://api.experientiallabs.ai")
    monkeypatch.setenv("JEV_API_KEY", "gw-hidden")
    monkeypatch.setattr("sys.argv", ["third_reader", "run"])
    answered = [study_record("fixed", k) for k in (1, 2, 3)]
    monkeypatch.setattr(third_reader, "run", lambda rows, key, provider: answered)  # a budget stop
    third_reader.main()
    out = capsys.readouterr().out
    assert out.splitlines()[0] == (
        "Jev through experientiallabs at https://api.experientiallabs.ai, model jev-latest,"
        " key JEV_API_KEY from the environment"
    )
    assert "the run stopped early: 3 of 7 planned calls answered" in out and "hidden" not in out

    def failed(rows, key, provider):
        write_log(log, [*answered, failed_record("fixed", 4, 0)])
        raise jev.CallError("refused", "HTTPError", 0, 503)

    monkeypatch.setattr(third_reader, "run", failed)
    with pytest.raises(jev.CallError):
        third_reader.main()
    assert "the run stopped early: 3 of 7 planned calls answered" in capsys.readouterr().out


def test_run_goes_through_the_opener_that_follows_no_redirect():
    assert inspect.signature(third_reader.run).parameters["opener"].default == jev.OPEN


def test_a_refused_header_value_writes_no_record_and_frees_the_lock(tmp_path):
    out = tmp_path / "r.jsonl"

    def strict(request, timeout):  # as http.client refuses an illegal header value: quoting it
        raise ValueError(f"Invalid header value {request.get_header('Authorization').encode()!r}")

    with pytest.raises(ValueError, match="the key is not shown"):
        third_reader.run([CLOZE_ROW], "ts-hidden\n", out, opener=strict)
    assert out.read_text(encoding="utf-8") == "" and not (tmp_path / "r.jsonl.lock").exists()


def test_a_whole_float_token_count_is_kept_in_the_row_as_an_int():
    logged = study_record("fixed", 1)
    logged["response"]["usage"] |= {"input_tokens": 53.0, "output_tokens": 53.0}
    row = third_reader.compact(logged)
    assert (row["input_tokens"], row["output_tokens"]) == (53, 53)
    assert type(row["input_tokens"]) is int and type(row["output_tokens"]) is int


def test_the_headers_completed_is_when_the_last_call_ended():
    first = study_record("fixed", 1)  # started 00:00:00, took 1 s
    last = study_record("fixed", 2) | {"at": "2026-11-19T00:00:08Z", "seconds": 2.6}
    assert third_reader.header([first, last])["completed"] == "2026-11-19T00:00:10Z"  # 10.6 s
    failed = failed_record("fixed", 3, 0) | {"at": "2026-11-19T00:01:00Z"}  # no seconds logged
    assert third_reader.header([first, last, failed])["completed"] == "2026-11-19T00:01:00Z"


def test_a_report_with_no_answered_call_still_renders_and_says_so():
    kept = ("id", "task", "pass", "run", "provider", "model_requested", "at")
    failed = {k: RECORDS[0][k] for k in kept} | {"error": "TimeoutError", "retries": 0}
    for rows in ([], [failed | {"estimate": 300}]):
        a = third_reader.analyse(rows, MINE, BLIND)
        none = HEAD | {"answered": 0, "complete": False}
        text = third_reader.render(a, none, third_reader.RESULTS)
        assert "No call was answered: 0 of 6 planned calls, so there is nothing to compare." in text
        assert "Config and sources:" in text and "| comparison |" not in text


def test_a_report_with_one_answered_call_skips_the_p90_and_says_so():
    text = rendered(third_reader.analyse(RECORDS[:1], MINE, BLIND))
    assert "Latency per call: median 0.100 s; the p90 needs two answered calls or more." in text


def test_the_results_step_on_an_empty_log_writes_a_header_and_the_report_says_so(
    monkeypatch, tmp_path
):
    one_item_sheet(monkeypatch, tmp_path)
    log, kept, report = tmp_path / "responses.jsonl", tmp_path / "kept.jsonl", tmp_path / "r.md"
    log.write_text("", "utf-8")
    for name, path in [("LOG", log), ("RESULTS", kept), ("REPORT", report)]:
        monkeypatch.setattr(third_reader, name, path)
    monkeypatch.setattr("sys.argv", ["third_reader", "results"])
    third_reader.main()
    head, rows = results.read(kept)
    assert (head["planned"], head["answered"], head["complete"], rows) == (7, 0, False, [])
    monkeypatch.setattr("sys.argv", ["third_reader", "report"])
    third_reader.main()
    assert "No call was answered: 0 of 7 planned calls" in report.read_text("utf-8")


def test_main_says_when_every_planned_call_was_answered(monkeypatch, tmp_path, capsys):
    one_item_sheet(monkeypatch, tmp_path)
    log = tmp_path / "responses.jsonl"
    monkeypatch.setattr(third_reader, "LOG", log)
    for name in ["JEV_BASE_URL", "JEV_API_KEY", "JEV_MIN_INTERVAL_S"]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TYPESAFE_API_KEY", "ts-hidden")
    monkeypatch.setattr("sys.argv", ["third_reader", "run"])
    plan = [("fixed", k) for k in range(1, 6)] + [("rotated", 1), ("rotated", 2)]
    every = [study_record(kind, k) for kind, k in plan]
    monkeypatch.setattr(third_reader, "run", lambda rows, key, provider: every)
    third_reader.main()
    assert (
        capsys.readouterr().out.splitlines()[-1] == f"all 7 planned calls answered, logged to {log}"
    )
