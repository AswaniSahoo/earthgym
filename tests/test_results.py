from types import SimpleNamespace

from inspect_ai.model import ModelUsage
from inspect_ai.scorer import CORRECT, INCORRECT, Score

from earthgym import results


def sample(sid, value, answer, error=None):
    usage = {"m": ModelUsage(input_tokens=10, output_tokens=4, reasoning_tokens=1)}
    scores = {} if error else {"s": Score(value=value, answer=answer)}
    return SimpleNamespace(id=sid, scores=scores, error=error, model_usage=usage)


def test_a_row_keeps_the_id_the_parsed_answer_the_reward_and_the_tokens():
    assert results.row(sample("a", 0.25, "289.5")) == {
        "id": "a",
        "answer": "289.5",
        "reward": 0.25,
        "tokens": [10, 0, 0, 4, 1],  # input, cache write, cache read, output, reasoning
    }
    assert results.row(sample("b", CORRECT, "B"))["reward"] == 1.0
    assert results.row(sample("c", INCORRECT, None))["answer"] == ""
    assert results.row(sample("d", None, None, error="boom")) == {
        "id": "d",
        "error": True,
        "tokens": [10, 0, 0, 4, 1],
    }


def test_results_round_trip_through_one_json_line_per_item(tmp_path):
    head = {"model": "m/x", "items_sha256": "abc", "settings": {"batch": True}}
    rows = [{"id": "a", "answer": "1", "reward": 1.0, "tokens": [1, 0, 0, 1, 0]}]
    path = tmp_path / "run.jsonl"
    results.write(path, head, rows)
    assert len(path.read_text("utf-8").splitlines()) == 2
    assert results.read(path) == (head, rows)


def test_rows_of_a_multi_sample_run_carry_their_epoch():
    log = SimpleNamespace(
        eval=SimpleNamespace(config=SimpleNamespace(epochs=2)),
        samples=[SimpleNamespace(epoch=1), SimpleNamespace(epoch=2)],
    )
    assert results.with_epochs(log, [{"id": "a"}, {"id": "a"}]) == [
        {"id": "a", "epoch": 1},
        {"id": "a", "epoch": 2},
    ]
    one = SimpleNamespace(eval=SimpleNamespace(config=SimpleNamespace(epochs=None)), samples=[])
    assert results.with_epochs(one, [{"id": "a"}]) == [{"id": "a"}]
