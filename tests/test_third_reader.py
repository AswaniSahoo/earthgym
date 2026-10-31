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


def test_run_calls_each_item_five_times_and_logs_raw_responses_but_never_the_key(tmp_path):
    out = tmp_path / "responses.jsonl"
    records = third_reader.run(
        [CLOZE_ROW, CLOZE_ROW | {"id": "gold/cloze/5"}], "secret-key", out, opener=opener
    )
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(records) == len(lines) == 10 and "secret-key" not in out.read_text(encoding="utf-8")
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
    mine, fable = third_reader.mine(), third_reader.fable()
    assert (len(mine), len(fable)) == (61, 33)
    assert set(mine.values()) <= {n for task in jev.BUCKETS.values() for n in task}
    agree = sum(mine[i] == fable[i] for i in fable)
    assert agree == 32  # 31 of 33 at the review; 157 has since moved to the blind sort's label
