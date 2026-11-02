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


def run(model, rewards_by_item):
    head = {"model": model, "epochs": 8, "settings": {"temperature": 0.7}}
    head |= {"started": "2026-11-02T00:15:48+00:00", "completed": "2026-11-02T00:45:10+00:00"}
    return head, [r | {"tokens": [100, 0, 0, 40, 0]} for r in rows(rewards_by_item)]


def test_the_report_gives_each_model_and_each_question_its_own_row():
    a = run("m/one", {"ace/1": [1.0] * 8, "hours/2": [0.0, 1.0] * 4})
    b = run("m/two", {"ace/1": [0.0] * 8, "hours/2": [0.0] * 8})
    text = samples.render("ibtracs", [a, b], date="2026-11-02")
    assert "| m/one | 2 | 8 | 0.750 | 0.500 | 0.750 | 1.000 |" in text
    assert "| m/two | 2 | 8 | 0.000 | 0.000 | 0.000 | 0.000 |" in text
    assert "| m/one | hours | 1 | 8 | 0.500 | 1.000 | 0.500 | 1.000 |" in text
    assert "temperature 0.7" in text and "a sample passes at reward 1" in text


def test_a_forecast_sample_passes_when_it_beats_the_better_baseline():
    a = run("m/one", {"2m_temperature/x": [0.0] * 7 + [0.4]})
    text = samples.render("era5", [a], date="2026-11-02")
    assert "a sample passes at a reward above 0" in text
    assert "| m/one | 1 | 8 | 0.050 | 1.000 | 0.125 | 1.000 |" in text


def test_a_strict_variant_leaves_the_near_matches_out_of_its_own_table():
    a = run("m/one", {"gold/mcq/1": [1.0] * 8, "gold/mcq/2": [0.0] * 8})
    text = samples.render("climaqa", [a], date="2026-11-02", strict={"gold/mcq/2"})
    assert "## Strict variant: the near matches of Silver left out" in text
    assert "| m/one | 1 | 8 | 1.000 | 0.000 | 1.000 | 1.000 |" in text


def test_main_merges_each_models_files_and_writes_the_report(tmp_path, monkeypatch):
    from earthgym import results

    head = {"model": "m/one", "epochs": 8, "settings": {}, "started": "2026-11-02T00:15:48Z"}
    head["completed"] = "2026-11-02T00:20:00Z"
    for kind, item in (("mcq", "gold/mcq/1"), ("cloze", "gold/cloze/1")):
        results.write(tmp_path / f"r-{kind}.jsonl", head, rows({item: [1.0] * 8}))
    out = tmp_path / "report.md"
    files = [str(tmp_path / "r-mcq.jsonl"), str(tmp_path / "r-cloze.jsonl")]
    monkeypatch.setattr("sys.argv", ["samples", "climaqa", *files, "--out", str(out)])
    samples.main()
    text = out.read_text("utf-8")
    assert "| m/one | 2 | 8 | 1.000 | 0.000 | 1.000 | 1.000 |" in text
    assert "| m/one | cloze | 1 |" in text and "Dated 2026-11-02" in text


def test_the_report_says_what_each_run_cost_in_tokens_and_time():
    a = run("m/one", {"ace/1": [1.0] * 8})
    text = samples.render("ibtracs", [a], date="2026-11-02")
    assert "- m/one: temperature 0.7; 8 samples, 320 output tokens, from" in text
    assert "2026-11-02T00:15:48+00:00 to 2026-11-02T00:45:10+00:00" in text
