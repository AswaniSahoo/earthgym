"""Deterministic integrity checks for ClimaQA items: rows in, findings out."""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass

SEP = "\n--------------------\n"  # separator between options in the Options cell
SEP_RE = re.compile(r"\n-{5,}(?:\n|$)")
LABELS = list("abcd")
MASK = "<MASK>"
ALL_NONE = re.compile(r"\b(all|none) of the above\b")

# Defects mean the item is broken; every other check is a flag for a human to judge.
DEFECTS = {
    "mcq.option_labels",
    "mcq.answer_not_an_option",
    "mcq.empty_option",
    "mcq.duplicate_options",
    "cloze.no_mask",
    "cloze.empty_answer",
    # Silver is the paper's fine-tuning set (arXiv 2410.16701v2, A.3.2), so these are leaks.
    "leak.gold_in_silver",
    "leak.gold_in_other_silver_task",
}


@dataclass(frozen=True)
class Finding:
    check: str
    split: str
    item: str
    detail: str
    refs: tuple[str, ...] = ()


def kind(check: str) -> str:
    return "defect" if check in DEFECTS else "flag"


def norm(text: str) -> str:
    """Casefold and collapse whitespace; punctuation stays, since '(a - b)' is not '(b - a)'."""
    return " ".join(text.casefold().split())


def words(text: str) -> str:
    """Word tokens only, for containment checks where punctuation must not matter."""
    return " ".join(re.findall(r"\w+", text.casefold()))


def parse_options(raw: str) -> list[tuple[str, str]]:
    """'a) text' chunks -> [('a', 'text'), ...]; a chunk without a label gets label ''."""
    pairs = []
    for chunk in filter(None, (c.strip() for c in SEP_RE.split(raw.strip()))):
        head, sep, text = chunk.partition(")")
        if sep and len(head.strip()) == 1:
            pairs.append((head.strip().lower(), text.strip()))
        else:
            pairs.append(("", chunk))
    return pairs


def answer_text(row: dict) -> str:
    """The keyed answer as text (the chosen option for MCQ), minus edge punctuation."""
    if "Options" in row:
        text = dict(parse_options(row["Options"])).get(row["Answer"].strip().lower(), "")
    else:
        text = row["Answer"]
    return norm(text).strip(".,;:!? ")


def ref(row: dict) -> str:
    return f"{row.get('split', 'silver')}:{row['id']}"


def mcq(rows: list[dict], split: str) -> list[Finding]:
    out = []
    for row in rows:
        item = row["id"]
        options = parse_options(row["Options"])
        normed = [norm(text) for _, text in options]
        answer = row["Answer"].strip().lower()
        if [label for label, _ in options] != LABELS:
            out.append(Finding("mcq.option_labels", split, item, f"{len(options)} options"))
        if answer not in dict(options):
            out.append(Finding("mcq.answer_not_an_option", split, item, f"answer {answer!r}"))
        if not all(normed):
            out.append(Finding("mcq.empty_option", split, item, ""))
        if len(set(normed)) < len(normed):
            out.append(Finding("mcq.duplicate_options", split, item, ""))
        if any(ALL_NONE.search(text) for text in normed):
            out.append(Finding("mcq.all_or_none_of_above", split, item, ""))
        key = words(answer_text(row))
        if len(key.split()) >= 3 and f" {key} " in f" {words(row['Question'])} ":
            out.append(Finding("mcq.answer_in_question", split, item, key[:80]))
    return out


def cloze(rows: list[dict], split: str) -> list[Finding]:
    out = []
    for row in rows:
        item, question, answer = row["id"], row["Question"], words(row["Answer"])
        masks = question.count(MASK)
        if masks == 0:
            out.append(Finding("cloze.no_mask", split, item, ""))
        elif masks > 1:
            out.append(Finding("cloze.multiple_masks", split, item, f"{masks} masks"))
        if not answer:
            out.append(Finding("cloze.empty_answer", split, item, ""))
        elif f" {answer} " in f" {words(question.replace(MASK, ' '))} ":
            out.append(Finding("cloze.answer_in_question", split, item, answer))
    return out


def duplicates(rows: list[dict], split: str, compare_answers: bool = True) -> list[Finding]:
    """Repeated questions in one split, noting when the keyed answer text differs."""
    groups = defaultdict(list)
    for row in rows:
        groups[norm(row["Question"])].append(row)
    out = []
    for group in groups.values():
        if len(group) < 2:
            continue
        ids = [row["id"] for row in group]
        out.append(Finding("dup.question", split, ids[0], f"also ids {ids[1:]}"))
        if compare_answers and len({answer_text(row) for row in group}) > 1:
            out.append(Finding("dup.answer_differs", split, ids[0], f"ids {ids}"))
    return out


def overlap(
    gold: list[dict],
    silver: list[dict],
    split: str,
    check: str = "leak.gold_in_silver",
    compare: bool = True,
) -> list[Finding]:
    """Gold questions that appear verbatim in Silver rows."""
    seen = defaultdict(list)
    for row in silver:
        seen[norm(row["Question"])].append(row)
    out = []
    for row in gold:
        matches = seen.get(norm(row["Question"]), [])
        if not matches:
            continue
        detail = ""
        if compare:
            same = all(answer_text(m) == answer_text(row) for m in matches)
            detail = f"answer text {'same' if same else 'differs'}"
        out.append(Finding(check, split, row["id"], detail, tuple(ref(m) for m in matches)))
    return out


def near_overlap(
    gold: list[dict], silver: list[dict], split: str, threshold: float = 0.8
) -> list[Finding]:
    """Gold questions reworded in Silver: word-set Jaccard at or above threshold, not exact."""
    exact = {norm(row["Question"]) for row in silver}
    bags = [(set(words(row["Question"]).split()), row) for row in silver]
    out = []
    for row in gold:
        if norm(row["Question"]) in exact:
            continue
        bag = set(words(row["Question"]).split())
        score, best = max(
            ((len(bag & b) / len(bag | b), s) for b, s in bags if bag | b),
            default=(0.0, None),
            key=lambda pair: pair[0],
        )
        if best is not None and score >= threshold:
            out.append(
                Finding("leak.near_match", split, row["id"], f"jaccard {score:.2f}", (ref(best),))
            )
    return out


def summarize(rows: list[dict], task: str) -> dict:
    summary = {"rows": len(rows)}
    for column in ("Validation", "Complexity"):
        if rows and column in rows[0]:
            summary[column.lower()] = dict(Counter(row[column] for row in rows))
    if rows and {"Validation", "Complexity"} <= rows[0].keys():
        validated = [row["Complexity"] for row in rows if row["Validation"] == "True"]
        summary["validated_complexity"] = dict(Counter(validated))
    if task == "mcq":
        summary["answer"] = dict(Counter(row["Answer"].strip().lower() for row in rows))
    return summary
