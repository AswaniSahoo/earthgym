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
    assert [r["id"] for r in kept] == ["gold/mcq/0", "gold/cloze/0"]
    assert excluded == [
        {"id": "gold/mcq/1", "reasons": ["rejected by experts"]},
        {"id": "gold/mcq/2", "reasons": ["leak.gold_in_silver"]},
    ]


def test_mcq_record_lists_option_texts_in_order_and_the_key_letter():
    kept, _ = clean.clean({("gold", "mcq"): [mcq("0")], ("gold", "cloze"): []}, {"findings": []})
    assert kept[0]["options"] == [
        "Warm air rises.",
        "Cold air rises.",
        "Still air.",
        "Sinking air.",
    ]
    assert kept[0]["answer"] == "a" and kept[0]["task"] == "mcq"


def test_manifest_counts_kept_and_excluded_by_reason():
    kept = [{"task": "mcq"}, {"task": "cloze"}, {"task": "mcq"}]
    excluded = [{"id": "gold/mcq/1", "reasons": ["rejected by experts", "leak.gold_in_silver"]}]
    assert clean.manifest(kept, excluded)["kept"] == {"cloze": 1, "mcq": 2}
    assert clean.manifest(kept, excluded)["excluded_by_reason"] == {
        "leak.gold_in_silver": 1,
        "rejected by experts": 1,
    }
