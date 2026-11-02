import pytest

from earthgym.grpo import report


def rows(rewards_by_item, cut=()):
    return [
        {"id": i, "epoch": e + 1, "answer": "A", "reward": r, "tokens": 300, "cut": (i, e) in cut}
        for i, rewards in rewards_by_item.items()
        for e, r in enumerate(rewards)
    ]


def metrics():
    steps = [
        {"step": s, "reward": r, "frac_reward_zero_std": z, "completions/clipped_ratio": c}
        | {"step_time": t, "loss": 0.1}
        for s, r, z, c, t in [
            (1, 0.25, 0.0, 0.25, 300.0),
            (2, 1.0, 1.0, 0.0, 40.0),
            (3, 0.5, 0.0, 0.125, 60.0),
            (4, 0.75, 0.0, 0.0, 50.0),
        ]
    ]
    return {
        "config": {"model": "Qwen/Qwen3.5-2B", "revision": "abc", "steps": 4, "seed": 3407}
        | {"num_generations": 8, "learning_rate": 5e-5, "lora_rank": 16, "eval_samples": 2}
        | {"max_completion_length": 1024, "temperature": 0.7, "top_p": 0.8, "top_k": 20},
        "versions": {"python": "3.13.15", "torch": "2.11.0", "trl": "1.15.0", "unsloth": "x"},
        "events": [
            {
                "seconds": 20.0,
                "event": "installed",
                "gpu": "Tesla T4, 580, 15360 MiB\nTesla T4, 580, 15360 MiB",
            },
            {"seconds": 120.0, "event": "loaded", "dtype": "torch.float16", "gpu": "Tesla T4"},
            {"seconds": 900.0, "event": "trained", "peak_gib": 5.36},
            {"seconds": 1000.0, "event": "done"},
        ],
        "log_history": [*steps, {"train_runtime": 450.0, "step": 4}],
        "eval": {
            "before": {"test": rows({"t1": [1.0, 0.0], "t2": [0.0, 0.0], "t3": [1.0, 1.0]})},
            "after": {
                "test": rows({"t1": [1.0, 1.0], "t2": [1.0, 0.0], "t3": [1.0, 1.0]}, {("t2", 1)})
            },
        },
    }


def test_the_train_reward_is_read_per_step_with_the_steps_that_had_no_signal():
    curve = report.curve(metrics()["log_history"])
    assert [c["reward"] for c in curve] == [0.25, 1.0, 0.5, 0.75]
    s = report.training(metrics(), window=2)
    assert (s["first"], s["last"]) == (pytest.approx(0.625), pytest.approx(0.625))
    assert s["no_signal"] == 1 and s["clipped"] == pytest.approx(0.09375)
    assert s["step_seconds"] == pytest.approx(50.0)  # the median, past the first step's warmup


def test_the_held_out_split_is_compared_item_by_item_before_and_after():
    c = report.compare(metrics()["eval"]["before"]["test"], metrics()["eval"]["after"]["test"])
    assert (c["before"]["mean_reward"], c["after"]["mean_reward"]) == (0.5, pytest.approx(5 / 6))
    assert (c["better"], c["worse"], c["same"]) == (2, 0, 1)
    assert c["p"] == pytest.approx(0.5)  # two-sided sign test on 2 items that moved, both up
    assert c["cut_after"] == 1


def test_the_report_gives_the_config_the_curve_and_the_held_out_change():
    text = report.render(metrics(), name="smoke", date="2026-11-02", window=2)
    assert text.startswith("# GRPO on climaqa-v1 MCQ: smoke")
    assert "`Qwen/Qwen3.5-2B` at abc" in text and "trl 1.15.0" in text
    assert "- GPU: Tesla T4, 580, 15360 MiB; Tesla T4, 580, 15360 MiB; peak" in text  # one line
    assert "5.36 GiB" in text
    assert "| 1 | 0.250 |" in text and "| 4 | 0.750 |" in text
    assert "1 of 4 steps had the same reward on all 8 completions" in text
    assert "| test | 3 | before | 0.500 |" in text and "| test | 3 | after | 0.833 |" in text
    assert "2 items better, 0 worse, 1 the same (two-sided sign test p 0.500)" in text
