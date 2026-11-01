import io
import json

import pytest

from rlenv.climaqa import jev, third_reader

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
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener(request, timeout):
    answer = {"type": "choice", "choice": "same_answer", "confidence": 0.5}
    answer["probabilities"] = {"same_answer": 0.75, "other_correct_word": 0.25, "wrong_reply": 0.0}
    body = {"model": "jev-1.14.0", "answers": {"bucket": answer}, "usage": {"input_tokens": 100}}
    return Canned(json.dumps(body).encode())


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


def test_run_stops_before_the_budget(tmp_path):
    budget = jev.Budget(limit_usd=250, usd_per_input_token=1.0)  # room for two 100-token calls
    records = third_reader.run(
        [CLOZE_ROW], "k", tmp_path / "r.jsonl", opener=opener, budget=budget, first_estimate=100
    )
    assert len(records) == 2 and budget.spent == 200


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


def record(item, task, k, choice, probabilities, seconds):
    answer = {"type": "choice", "choice": choice, "confidence": 0.0, "probabilities": probabilities}
    payload = {"model": "jev-1.14.0", "answers": {"bucket": answer}, "usage": {"input_tokens": 100}}
    return {"id": item, "task": task, "run": k, "seconds": seconds, "response": payload}


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
    text = third_reader.render(third_reader.analyse(RECORDS, MINE, BLIND))
    assert "| Jev against the first sort | 3 | 1.000 |" in text
    assert "| Jev against the reviewer's blind sort | 2 | 1.000 |" in text
    assert "Brier score where both sorts agree: 0.256 over 2 items" in text


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
    text = third_reader.render(a)
    assert "first-listed option in 4 of 6 rotated-order calls (0.667; 0.333 if order" in text
