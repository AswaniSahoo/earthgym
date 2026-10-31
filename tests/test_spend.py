import contextlib
import importlib.util
from types import SimpleNamespace

import pytest
from inspect_ai.model import ModelUsage

from rlenv import spend


def log(**usage):
    stats = {"model_usage": {"m": ModelUsage(**usage)}, "completed_at": "2026-11-01T05:00:00+05:30"}
    return SimpleNamespace(stats=SimpleNamespace(**stats))


def test_cost_prices_each_kind_of_token_at_the_sonnet_5_5_rate():
    # per million tokens: $2 input, $2.50 cache write, $0.10 cache read, $10 output
    t = dict(input=10**6, cache_write=10**6, cache_read=10**6, output=10**6, reasoning=4 * 10**5)
    assert spend.cost(t) == pytest.approx(14.6)  # reasoning is billed inside output
    assert spend.cost(t, batch=True) == pytest.approx(7.3)  # the Batch API halves each price


def test_projection_scales_the_probe_mean_and_adds_two_standard_errors():
    mid, high = spend.project([1.0, 2.0, 3.0], 10)
    assert mid == pytest.approx(20.0)
    assert high == pytest.approx(10 * (2.0 + 2 * 1.0 / 3**0.5))  # sample sd 1


def test_tokens_sum_over_logs_and_models():
    a = log(input_tokens=10, output_tokens=7, input_tokens_cache_read=3, reasoning_tokens=5)
    b = log(input_tokens=1, output_tokens=2)
    assert spend.tokens([a, b]) == dict(
        input=11, cache_write=0, cache_read=3, output=9, reasoning=5
    )


def test_add_appends_a_row_with_the_running_total_and_check_verifies_it(tmp_path):
    ledger = tmp_path / "spend.md"
    ledger.write_text("# Spend\n\n" + spend.TABLE, "utf-8")
    run = log(input_tokens=500_000, output_tokens=100_000)  # $1 + $1, half in a batch
    assert spend.add("probe", "logs/p", [run], ledger) == pytest.approx(2.0)
    assert spend.add("full", "logs/f", [run], ledger, batch=True) == pytest.approx(3.0)
    text = ledger.read_text("utf-8")
    last = "| full | 2026-11-01 | logs/f | batch | 500000 | 0 | 0 | 100000 | 0 | 1.0000 | 3.0000 |"
    assert text.splitlines()[-1] == last
    assert spend.check(text) == pytest.approx(3.0)
    with pytest.raises(ValueError, match="does not add up"):
        spend.check(text.replace("| 3.0000 |", "| 4.0000 |"))


def test_the_ledger_adds_up_and_stays_under_the_cap():
    assert spend.check(spend.LEDGER.read_text("utf-8")) <= spend.CAP


def test_no_gemini_or_vertex_client_is_installed():
    # Aswani, 2026-11-01: no Vertex AI or Gemini calls of any kind (decision 0010)
    for name in ("google.genai", "google.auth", "vertexai"):
        with contextlib.suppress(ModuleNotFoundError):
            assert importlib.util.find_spec(name) is None, name
