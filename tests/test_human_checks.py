import csv

from earthgym.climaqa import human_checks

SAMPLE = {
    "id": "158",
    "complexity": "BASE",
    "question": "What method is used?",
    "options": human_checks.DIVIDER.join(["a) One way", "b) The right way", "c) A third"]),
    "answer": "b",
    "verdict": "",
    "note": "",
}
LEAK = {
    "check": "leak.near_match",
    "gold": "gold/mcq:61",
    "gold_question": "What is it called?",
    "gold_answer": "forcing",
    "silver": "silver/mcq:114",
    "silver_question": "What is this called?",
    "silver_answer": "forcing",
    "verdict": "",
    "note": "",
}


def test_the_sample_sheet_spells_out_the_key_and_leaves_the_verdict_empty():
    header, rows = human_checks.sample_sheet([SAMPLE])
    assert header == ["id", "question", "options", "gold_answer", "verdict", "note"]
    assert rows == [
        [
            "158",
            "What method is used?",
            "a) One way\nb) The right way\nc) A third",
            "b) The right way",
            "",
            "",
        ]
    ]


def test_the_leak_sheet_puts_gold_and_silver_side_by_side():
    header, rows = human_checks.leak_sheet([LEAK])
    assert header == [
        "id",
        "question",
        "gold_answer",
        "silver_id",
        "silver_question",
        "silver_answer",
        "verdict",
        "note",
    ]
    assert rows == [
        [
            "gold/mcq:61",
            "What is it called?",
            "forcing",
            "silver/mcq:114",
            "What is this called?",
            "forcing",
            "",
            "",
        ]
    ]


def test_main_writes_both_sheets_once_and_never_overwrites_a_verdict(tmp_path, monkeypatch):
    sample, leaks = tmp_path / "s.csv", tmp_path / "l.csv"
    for path, row in ((sample, SAMPLE), (leaks, LEAK)):
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, list(row))
            writer.writeheader()
            writer.writerow(row)
    monkeypatch.setattr(human_checks, "SAMPLE_IN", sample)
    monkeypatch.setattr(human_checks, "LEAKS_IN", leaks)
    monkeypatch.setattr(human_checks, "OUT", tmp_path / "out")
    monkeypatch.setattr("sys.argv", ["human_checks"])
    human_checks.main()
    out = tmp_path / "out" / "climaqa-sample.csv"
    filled = out.read_text("utf-8").replace(",,\r\n", ",yes,checked\r\n", 1)
    out.write_text(filled, "utf-8")
    human_checks.main()
    assert out.read_text("utf-8") == filled
    assert (tmp_path / "out" / "leak-pairs.csv").exists()
