import io
import json

import pytest

from rlenv.climaqa import jev

CLOZE = {"sentence": "The <MASK> rises.", "key": "sun", "reply": "Sun"}


def test_request_holds_one_item_and_one_choice_question_on_the_pinned_model():
    body = jev.request("cloze", CLOZE)
    assert body["model"] == "jev-1.14.0" and body["state"] == CLOZE
    assert list(body["questions"]) == ["bucket"]
    question = body["questions"]["bucket"]
    assert question["type"] == "choice"
    assert list(question["criteria"]) == ["same_answer", "other_correct_word", "wrong_reply"]


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_call_posts_json_with_the_key_as_a_bearer_token_and_times_the_call():
    seen = {}

    def opener(request, timeout):
        seen.update(url=request.full_url, method=request.get_method(), timeout=timeout)
        seen.update(auth=request.get_header("Authorization"), body=json.loads(request.data))
        return FakeResponse(json.dumps({"answers": {}, "usage": {"input_tokens": 9}}).encode())

    payload, seconds = jev.call({"model": "m"}, "test-key", opener=opener)
    assert payload["usage"]["input_tokens"] == 9 and seconds >= 0
    assert seen["url"] == "https://api.typesafe.ai/v1/systemone" and seen["method"] == "POST"
    assert seen["auth"] == "Bearer test-key" and seen["body"] == {"model": "m"}


def test_load_key_prefers_the_environment_then_the_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('OTHER=1\nexport TYPESAFE_API_KEY="from-file"\n', encoding="utf-8")
    assert jev.load_key({"TYPESAFE_API_KEY": "from-env"}, env_file) == "from-env"
    assert jev.load_key({}, env_file) == "from-file"
    with pytest.raises(RuntimeError, match="TYPESAFE_API_KEY"):
        jev.load_key({}, tmp_path / "missing.env")


def test_budget_refuses_a_call_that_would_cross_the_limit():
    budget = jev.Budget(limit_usd=0.10, usd_per_input_token=0.042 / 1e6)
    assert budget.allows(2_380_952) and not budget.allows(2_380_953)  # 0.10 / 0.042e-6
    budget.charge(1_000_000)
    assert budget.spent == pytest.approx(0.042)
    assert budget.allows(1_380_952) and not budget.allows(1_400_000)
