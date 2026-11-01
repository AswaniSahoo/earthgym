from earthgym.climaqa import expert_sheet

NOTE = """\
| N | key | reply | bucket | note |
|---|---|---|---|---|
| 4 | density | temperature | other, debatable | a reason |
| 22 | (τa) | (AOD) | strictness: symbol | two notations |
"""

RECORDS = [
    {"id": "gold/cloze/4", "task": "cloze", "question": "The <MASK> rises.", "answer": "density"},
    {"id": "gold/cloze/22", "task": "cloze", "question": "AOD <MASK> is used.", "answer": "(τa)"},
    {"id": "gold/cloze/30", "task": "cloze", "question": "A <MASK> forms.", "answer": "cloud"},
    {
        "id": "gold/mcq/56",
        "task": "mcq",
        "question": "Which publication?",
        "options": ["w", "x", "y", "z"],
        "answer": "B",
    },
]


def test_note_rows_give_each_flagged_item_its_reply_bucket_and_note():
    assert expert_sheet.note_rows(NOTE, "cloze") == [
        ("gold/cloze/4", "temperature", "other, debatable", "a reason"),
        ("gold/cloze/22", "(AOD)", "strictness: symbol", "two notations"),
    ]


def test_sheet_lists_flags_and_extras_then_sampled_hits_with_empty_expert_columns():
    flags = expert_sheet.note_rows(NOTE, "cloze")
    rows = expert_sheet.sheet(RECORDS, flags, {"gold/mcq/56": "tests the source"}, hits=1, seed=1)
    assert [r["id"] for r in rows] == [
        "gold/cloze/4",
        "gold/cloze/22",
        "gold/mcq/56",
        "gold/cloze/30",
    ]
    assert rows[2]["key"] == "B) x" and rows[2]["options"] == "A) w\nB) x\nC) y\nD) z"
    assert rows[3]["flag"] == "sampled hit" and rows[3]["model_answer"] == "cloud"
    assert all(r["verdict"] == r["accepted_answers"] == r["expert_note"] == "" for r in rows)


def test_write_once_keeps_a_sheet_the_expert_may_have_filled(tmp_path):
    path = tmp_path / "sheet.csv"
    path.write_text("filled", encoding="utf-8")
    assert expert_sheet.write_once([], path) is False
    assert path.read_text(encoding="utf-8") == "filled"


def test_mcq_notes_have_six_columns_and_the_sheet_shows_the_chosen_option():
    note = "| 36 | HYPOTHETICAL | A | D | ambiguous | a reason |\n"
    flags = expert_sheet.note_rows(note, "mcq")
    assert flags == [("gold/mcq/36", "D", "ambiguous", "a reason")]
    record = {**RECORDS[3], "id": "gold/mcq/36"}
    assert expert_sheet.sheet([record], flags, {}, hits=0)[0]["model_answer"] == "D) z"


def test_sheet_restores_a_reply_the_note_could_not_write_verbatim():
    record = {
        "id": "gold/cloze/37",
        "task": "cloze",
        "question": "<MASK> interactions.",
        "answer": "x",
    }
    flags = [("gold/cloze/37", "Aerosol-cloud", "strictness: word order", "a reason")]
    row = expert_sheet.sheet([record], flags, {}, hits=0)[0]
    assert row["model_answer"] == "Aerosol\u2013cloud"  # the logged reply has an en dash
