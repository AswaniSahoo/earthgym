import pytest

from earthgym.grpo import pick


def rows(rewards_by_item, tokens=100):
    return [
        {"id": i, "epoch": e + 1, "reward": r, "tokens": [10, 0, 0, tokens, 0]}
        for i, rewards in rewards_by_item.items()
        for e, r in enumerate(rewards)
    ]


def test_a_tasks_numbers_are_its_median_reply_and_its_train_items_reward_variance():
    s = pick.stats(rows({"a": [1, 0] * 4, "b": [1] * 8, "c": [0, 0, 0, 1] * 2}), train={"a", "b"})
    assert (s["median_tokens"], s["train_items"]) == (100, 2)
    assert s["mean_variance"] == pytest.approx((0.25 + 0.0) / 2)  # c is not a train item
    assert s["varies"] == pytest.approx(0.5)


def test_the_pick_is_the_eligible_task_with_the_most_reward_variance():
    tasks = {
        "long": {"median_tokens": 1323, "mean_variance": 0.2, "varies": 0.9},
        "mcq": {"median_tokens": 382.5, "mean_variance": 0.0958, "varies": 0.52},
        "cloze": {"median_tokens": 3, "mean_variance": 0.06, "varies": 0.34},
    }
    assert pick.pick(tasks, cap=1024) == "mcq"  # the long one cannot be trained at the cap
    tie = tasks | {"cloze": {"median_tokens": 3, "mean_variance": 0.0958, "varies": 0.6}}
    assert pick.pick(tie, cap=1024) == "cloze"  # a tie goes to the larger varying share
    with pytest.raises(ValueError, match="no task"):
        pick.pick({"long": tasks["long"]}, cap=1024)
