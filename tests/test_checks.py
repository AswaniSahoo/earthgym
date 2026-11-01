from earthgym.climaqa import checks

OPTS = checks.SEP.join(
    [
        "a) Warm air rises.",
        "b) Cold air rises.",
        "c) Air does not move.",
        "d) Air sinks everywhere.",
    ]
)


def mcq_row(**fields):
    return {
        "id": "0",
        "Question": "Why does convection start?",
        "Options": OPTS,
        "Answer": "a",
    } | fields


def test_parse_options_reads_four_labelled_options():
    assert [label for label, _ in checks.parse_options(OPTS)] == checks.LABELS


def test_clean_mcq_item_has_no_findings():
    assert checks.mcq([mcq_row()], "gold/mcq") == []


def test_mcq_flags_bad_key_duplicate_options_and_leaked_answer():
    rows = [
        mcq_row(id="1", Answer="e"),
        mcq_row(id="2", Options=OPTS.replace("Cold air rises.", "Warm air rises.")),
        mcq_row(id="3", Question="Is it true that warm air rises?"),
    ]
    found = {(f.item, f.check) for f in checks.mcq(rows, "gold/mcq")}
    assert found == {
        ("1", "mcq.answer_not_an_option"),
        ("2", "mcq.duplicate_options"),
        ("3", "mcq.answer_in_question"),
    }


def test_mcq_flags_missing_option_labels():
    three = OPTS.rsplit(checks.SEP, 1)[0]
    assert [f.check for f in checks.mcq([mcq_row(Options=three)], "s")] == ["mcq.option_labels"]


def test_options_that_differ_only_in_operators_are_not_duplicates():
    signs = checks.SEP.join(["a) (s - e)", "b) (e - s)", "c) (s + e)", "d) (e + s)"])
    assert checks.mcq([mcq_row(Options=signs)], "s") == []


def test_cloze_checks_masks_and_answer_outside_the_blank():
    rows = [
        {"id": "0", "Question": "<MASK> drives convection in the tropics.", "Answer": "Heating"},
        {"id": "1", "Question": "Heating by the sun causes <MASK>.", "Answer": "heating"},
        {"id": "2", "Question": "No blank here.", "Answer": "x"},
        {"id": "3", "Question": "The <MASK> number, named after <MASK>.", "Answer": "Froude"},
    ]
    found = {(f.item, f.check) for f in checks.cloze(rows, "gold/cloze")}
    assert found == {
        ("1", "cloze.answer_in_question"),
        ("2", "cloze.no_mask"),
        ("3", "cloze.multiple_masks"),
    }


def test_duplicates_note_when_the_keyed_answer_differs():
    rows = [mcq_row(id="0"), mcq_row(id="1", Question="why does  CONVECTION start?", Answer="b")]
    assert [(f.check, f.item) for f in checks.duplicates(rows, "s")] == [
        ("dup.question", "0"),
        ("dup.answer_differs", "0"),
    ]


def test_gold_in_silver_compares_the_keyed_answer_text_not_the_letter():
    gold = [mcq_row(id="0")]
    shuffled = checks.SEP.join(["a) Cold air rises.", "b) Warm air rises", "c) x", "d) y"])
    silver = [mcq_row(id="7", Options=shuffled, Answer="b"), mcq_row(id="8", Answer="c")]
    same = checks.overlap(gold, silver[:1], "g")
    assert [(f.check, f.refs, f.detail) for f in same] == [
        ("leak.gold_in_silver", ("silver:7",), "answer text same")
    ]
    assert [f.detail for f in checks.overlap(gold, silver, "g")] == ["answer text differs"]


def test_answer_text_keeps_operators_but_drops_trailing_punctuation():
    assert checks.answer_text({"Answer": "Emissions,"}) == checks.answer_text(
        {"Answer": "emissions"}
    )
    assert checks.answer_text({"Answer": "(a - b)"}) != checks.answer_text({"Answer": "(a + b)"})


def test_overlap_against_another_task_skips_the_answer_comparison():
    gold = [mcq_row(id="0")]
    other = [{"id": "5", "split": "silver/ffq", "Question": "Why does convection start?"}]
    found = checks.overlap(gold, other, "gold/mcq", check="leak.other_task", compare=False)
    assert [(f.check, f.refs, f.detail) for f in found] == [
        ("leak.other_task", ("silver/ffq:5",), "")
    ]


def test_near_overlap_flags_reworded_questions_only():
    gold = [
        {"id": "0", "Question": "What drives the Hadley circulation in the tropics today?"},
        {"id": "1", "Question": "Why does convection start?"},
        {"id": "2", "Question": "How is sea ice albedo measured from orbit?"},
    ]
    silver = [
        {"id": "4", "Question": "What drives the Hadley circulation in tropics today?"},
        {"id": "5", "Question": "Why does convection start?"},
    ]
    found = checks.near_overlap(gold, silver, "g", threshold=0.8)
    assert [(f.item, f.refs) for f in found] == [("0", ("silver:4",))]


def test_parse_options_ignores_a_trailing_separator():
    assert checks.parse_options(OPTS + checks.SEP)[-1] == ("d", "Air sinks everywhere.")


def test_answer_in_question_respects_word_boundaries():
    row = mcq_row(Question="Explain why lukewarm air rises at night.")
    assert checks.mcq([row], "s") == []


def test_a_short_key_that_alone_appears_in_the_question_is_flagged():
    opts = checks.SEP.join(["a) Amines", "b) Ammonia", "c) H2SO4", "d) Organic molecules"])
    row = mcq_row(Question="What nucleates highly oxidized organic molecules?", Options=opts)
    assert [f.check for f in checks.mcq([row | {"Answer": "d"}], "s")] == ["mcq.answer_in_question"]


def test_a_key_shared_with_a_distractor_in_the_question_is_not_a_leak():
    opts = checks.SEP.join(["a) Ozone", "b) Water vapour", "c) Nitrogen", "d) Argon"])
    row = mcq_row(Question="Is ozone or water vapour the stronger absorber?", Options=opts)
    assert checks.mcq([row], "s") == []


def test_summarize_counts_validation_complexity_and_answers():
    rows = [
        mcq_row(Validation="True", Complexity="BASE"),
        mcq_row(id="1", Validation="False", Complexity="BASE", Answer="b"),
    ]
    assert checks.summarize(rows, "mcq") == {
        "rows": 2,
        "validation": {"True": 1, "False": 1},
        "complexity": {"BASE": 2},
        "validated_complexity": {"BASE": 1},
        "answer": {"a": 1, "b": 1},
    }
