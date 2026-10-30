from rlenv.climaqa import checks, clean

OPTS = checks.SEP.join(
    ["a) Warm air rises.", "b) Cold air rises.", "c) Still air.", "d) Sinking air."]
)


def mcq(id_, validation="True"):
    return {
        "id": id_,
        "Question": f"Q{id_}?",
        "Options": OPTS,
        "Answer": "a",
        "Complexity": "BASE",
        "Validation": validation,
    }


def finding(split, item, check):
    return {"check": check, "split": split, "item": item, "kind": checks.kind(check)}


def test_clean_keeps_validated_items_and_logs_every_exclusion():
    rows = {
        ("gold", "mcq"): [mcq("0"), mcq("1", validation="False"), mcq("2")],
        ("gold", "cloze"): [{"id": "0", "Question": "<MASK> lifts air.", "Answer": "Buoyancy"}],
    }
    report = {
        "findings": [
            finding("gold/mcq", "2", "leak.gold_in_silver"),
            finding("gold/cloze", "0", "cloze.answer_in_question"),
        ]
    }
    kept, excluded = clean.clean(rows, report)
    assert [r["id"] for r in kept] == ["gold/mcq/0"]
    assert excluded == [
        {"id": "gold/mcq/1", "reasons": ["rejected by experts"]},
        {"id": "gold/mcq/2", "reasons": ["leak.gold_in_silver"]},
        {"id": "gold/cloze/0", "reasons": ["cloze.answer_in_question"]},
    ]


def test_mcq_options_are_shuffled_once_and_the_key_follows_its_text():
    kept, _ = clean.clean({("gold", "mcq"): [mcq("0")], ("gold", "cloze"): []}, {"findings": []})
    options, key = kept[0]["options"], kept[0]["answer"]
    assert sorted(options) == sorted(
        ["Warm air rises.", "Cold air rises.", "Still air.", "Sinking air."]
    )
    assert options["ABCD".index(key)] == "Warm air rises." and kept[0]["task"] == "mcq"


def test_keys_spread_across_letters_after_the_shuffle():
    rows = {("gold", "mcq"): [mcq(str(i)) for i in range(20)], ("gold", "cloze"): []}
    kept, _ = clean.clean(rows, {"findings": []})
    assert len({r["answer"] for r in kept}) > 1


def test_shuffle_depends_only_on_the_item_id_not_its_neighbours():
    alone, _ = clean.clean({("gold", "mcq"): [mcq("7")], ("gold", "cloze"): []}, {"findings": []})
    crowd, _ = clean.clean(
        {("gold", "mcq"): [mcq("3"), mcq("7"), mcq("9")], ("gold", "cloze"): []}, {"findings": []}
    )
    assert alone[0]["options"] == crowd[1]["options"]


def test_cloze_key_loses_trailing_punctuation_so_exact_match_is_fair():
    rows = {
        ("gold", "mcq"): [],
        ("gold", "cloze"): [{"id": "0", "Question": "<MASK> cools.", "Answer": "evaporation,"}],
    }
    kept, _ = clean.clean(rows, {"findings": []})
    assert kept[0]["answer"] == "evaporation"


def test_manifest_counts_by_reason_and_pins_the_set_by_sha256():
    kept = [{"task": "mcq"}, {"task": "cloze"}, {"task": "mcq"}]
    excluded = [{"id": "gold/mcq/1", "reasons": ["rejected by experts", "leak.gold_in_silver"]}]
    text = clean.serialize(kept)
    summary = clean.manifest(kept, excluded, text)
    assert summary["kept"] == {"cloze": 1, "mcq": 2}
    assert summary["excluded_by_reason"] == {"leak.gold_in_silver": 1, "rejected by experts": 1}
    assert summary["sha256"] == __import__("hashlib").sha256(text.encode()).hexdigest()


def test_bundled_set_matches_its_manifest():
    import hashlib
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    summary = json.loads((root / "reports/climaqa/clean_v1_manifest.json").read_text())
    text = (root / clean.BUNDLE / "climaqa_clean_v1.jsonl").read_text("utf-8")
    assert hashlib.sha256(text.encode()).hexdigest() == summary["sha256"]
    assert len(text.splitlines()) == sum(summary["kept"].values())


def test_main_writes_the_set_and_its_manifest(tmp_path, monkeypatch):
    import json
    import sys

    from rlenv.climaqa import data

    rows = {(c, t): [] for c in ("gold", "silver") for t in ("mcq", "cloze", "ffq")}
    rows["gold", "mcq"] = [mcq("0")]
    monkeypatch.setattr(data, "load_all", lambda cache: rows)
    out, reports = tmp_path / "out", tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(sys, "argv", ["clean", "--out", str(out), "--reports", str(reports)])
    clean.main()
    assert len((out / "climaqa_clean_v1.jsonl").read_text().splitlines()) == 1
    assert json.loads((reports / "clean_v1_manifest.json").read_text())["kept"] == {"mcq": 1}
