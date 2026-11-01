import pytest

from rlenv import ablation


def run(model="anthropic/claude-sonnet-5-5", ids=("a", "b")):
    q = {"question": "q", "n": len(ids), "accuracy": 1.0, "traps": {}}
    return {"model": model, "n": len(ids), "reward": 1.0, "questions": [q], "ids": list(ids)}


def render(shown, hidden):
    return ablation.render_pair(shown, hidden, "env", "rules hidden", "flag", "hidden", "clause")


def test_a_pair_renders_when_both_runs_cover_the_same_items_on_one_model():
    assert render(run(ids=("a", "b")), run(ids=("b", "a"))).startswith("# env: rules shown")


@pytest.mark.parametrize(
    ("hidden", "message"),
    [
        (run(ids=("a", "c")), "not over the same items"),
        (run(ids=("a", "b", "b")), "repeats an item id"),
        (run(model="anthropic/claude-opus-5-5"), "different models"),
    ],
)
def test_a_pair_is_refused_unless_the_runs_match(hidden, message):
    with pytest.raises(ValueError, match=message):
        render(run(), hidden)
