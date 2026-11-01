import pytest

from earthgym import samples


def rows(rewards_by_item):
    return [
        {"id": i, "epoch": e + 1, "reward": r, "answer": "x"}
        for i, rewards in rewards_by_item.items()
        for e, r in enumerate(rewards)
    ]


def test_pass_at_k_is_the_unbiased_estimator():
    assert samples.pass_at_k(8, 0, 1) == 0.0 and samples.pass_at_k(8, 8, 1) == 1.0
    assert samples.pass_at_k(8, 1, 1) == pytest.approx(1 / 8)
    assert samples.pass_at_k(8, 1, 8) == 1.0 and samples.pass_at_k(8, 0, 8) == 0.0
    assert samples.pass_at_k(8, 2, 4) == pytest.approx(1 - 15 / 70)  # 1 - C(6,4) / C(8,4)


def test_summary_gives_the_mean_the_varying_share_and_pass_at_1_and_8():
    s = samples.summary(
        rows({"a": [1.0] * 8, "b": [0.0] * 8, "c": [1.0, 0.0] * 4, "d": [0.0] * 7 + [1.0]})
    )
    assert (s["items"], s["samples"]) == (4, 8)
    assert s["mean_reward"] == pytest.approx((8 + 0 + 4 + 1) / 32)
    assert s["varies"] == pytest.approx(2 / 4)  # c and d earn different rewards across samples
    assert s["pass@1"] == pytest.approx((1 + 0 + 0.5 + 1 / 8) / 4)
    assert s["pass@8"] == pytest.approx(3 / 4)


def test_a_continuous_reward_passes_where_it_beats_the_baseline():
    s = samples.summary(rows({"a": [0.0] * 7 + [0.3], "b": [0.0] * 8}), passed=lambda r: r > 0)
    assert (s["varies"], s["pass@8"], s["pass@1"]) == (0.5, 0.5, pytest.approx(1 / 16))


def test_an_errored_sample_earns_zero_and_unequal_sample_counts_are_refused():
    s = samples.summary(
        [{"id": "a", "epoch": 1, "error": True}, {"id": "a", "epoch": 2, "reward": 1.0}]
    )
    assert (s["mean_reward"], s["varies"]) == (0.5, 1.0)
    with pytest.raises(ValueError, match="same number of samples"):
        samples.summary(rows({"a": [1.0, 0.0], "b": [1.0]}))
