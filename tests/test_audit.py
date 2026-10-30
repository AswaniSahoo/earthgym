from rlenv.climaqa import audit, checks

OPTS = checks.SEP.join(
    ["a) Warm air rises.", "b) Cold air rises.", "c) Still air.", "d) Sinking air."]
)
QUESTION = "Why does convection start?"


def tiny_rows():
    mcq = {"Question": QUESTION, "Options": OPTS, "Answer": "a", "Complexity": "BASE"}
    return {
        ("gold", "mcq"): [mcq | {"id": "0", "Validation": "True"}],
        ("gold", "cloze"): [
            {"id": "0", "Question": "<MASK> lifts warm air.", "Answer": "Buoyancy"}
        ],
        ("gold", "ffq"): [
            {
                "id": "0",
                "Question": "What is ENSO?",
                "Answer": "A coupled cycle.",
                "Complexity": "BASE",
                "Validation": "False",
            }
        ],
        ("silver", "mcq"): [mcq | {"id": "3"}],
        ("silver", "cloze"): [],
        ("silver", "ffq"): [
            {"id": "9", "Question": QUESTION, "Answer": "Heating.", "Complexity": "BASE"}
        ],
    }


def test_audit_reports_same_task_and_other_task_leaks_without_io():
    report = audit.audit(tiny_rows())
    leaks = {(f["check"], f["split"], tuple(f["refs"])) for f in report["findings"]}
    assert ("leak.gold_in_silver", "gold/mcq", ("silver/mcq:3",)) in leaks
    assert ("leak.gold_in_other_silver_task", "gold/mcq", ("silver/ffq:9",)) in leaks
    assert report["inventory"]["gold/ffq"]["validation"] == {"False": 1}


def test_write_once_keeps_an_existing_hand_check_sheet(tmp_path):
    sheet = tmp_path / "review_sample.csv"
    sheet.write_text("id,verdict\n0,ok\n", encoding="utf-8")
    audit.write_once(sheet, ["id", "verdict"], [["1", ""]])
    assert sheet.read_text(encoding="utf-8") == "id,verdict\n0,ok\n"


def test_render_shows_paper_rows_and_findings():
    text = audit.render(audit.audit(tiny_rows()))
    assert "## Paper check" in text and "leak.gold_in_silver" in text
