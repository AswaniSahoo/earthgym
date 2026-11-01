"""One answer contract for the heat policy questions: the prompt with its rules, the answer
line and the reward (decisions 0012 and 0013).

The Inspect task and the verifiers taskset both import this module, so they read the same
replies and pay the same reward.
"""

import hashlib
import math
import re

TRIGGER = (
    "A trigger day is a day on which the index station's maximum is at or above {threshold} F. "
    "A missing value is never a trigger day"
)
RULES = {
    "trigger_days": TRIGGER + ".",
    "events": TRIGGER + " and ends a run. An event is a run of at least {k} consecutive "
    "trigger days; it pays once, however long it lasts.",
    "missed_days": "A missed day is a day on which the insured site's maximum is at or above "
    "{threshold} F while the index station's maximum is not; a missing index value counts as "
    "not at or above the threshold. A missing site value is never a missed day.",
}
TERMS = {  # the terms-only ablation: a term sheet's wording, with no clarifying rules
    "trigger_days": "A trigger day is a day on which the index station's maximum reaches "
    "{threshold} F.",
    "events": "A trigger day is a day on which the index station's maximum reaches {threshold} "
    "F. An event is {k} or more consecutive trigger days.",
    "missed_days": "A missed day is a day on which the insured site's maximum reaches "
    "{threshold} F but the index station's does not.",
}
QUESTIONS = {
    "trigger_days": "How many trigger days did the index station have from 1 May to 30 September?",
    "events": "How many events did the policy pay for?",
    "missed_days": "How many missed days were there?",
}
PROMPT = (
    "A parametric heat policy pays from the daily maximum temperature at an index weather "
    "station, {index_name}; the insured worker is at {site_name}. The cover runs from 1 May to 30 "
    "September. Below are both stations' daily maximum temperatures in whole degrees F from "
    "GHCN-Daily, with the year left out; a dash means no value.\n\n"
    "date | index: {index_name} | site: {site_name}\n{rows}\n\n"
    "{rule}\n\n"
    "{question} The last line of your response must be 'ANSWER: <number>'."
)
NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
ANSWER_LINE = re.compile(  # horizontal space only, so the number sits on the answer line
    rf"^[ \t]*ANSWER[ \t]*:[ \t]*({NUMBER})[ \t]*\.?[ \t]*$", re.MULTILINE | re.IGNORECASE
)


def _cell(value: int | None) -> str:
    return "-" if value is None else str(value)


def prompt(item: dict, rules: bool = True) -> str:
    """The task text: both stations' maxima over the window and the rule for the question, or
    for the terms-only ablation the policy terms alone; never the key or the year."""
    triples = zip(item["dates"], item["index_f"], item["site_f"], strict=True)
    rows = "\n".join(f"{d} | {_cell(i)} | {_cell(s)}" for d, i, s in triples)
    text = (RULES if rules else TERMS)[item["question"]]
    rule = text.format(threshold=item["threshold"], k=item["k"])
    rule = f"Rule. {rule}" if rules else f"Policy terms. {rule}"
    return PROMPT.format(
        index_name=item["index_name"],
        site_name=item["site_name"],
        rows=rows,
        rule=rule,
        question=QUESTIONS[item["question"]],
    )


def last_line(reply: str) -> str:
    """The reply's last non-empty line, with Markdown bold and code marks and the Unicode minus
    read as plain text: the one line an answer may sit on, as the prompt asks (decision 0016)."""
    plain = reply.replace("*", "").replace("`", "").replace("\u2212", "-")
    lines = [line for line in plain.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def answer(reply: str) -> float | None:
    """The number on the reply's last non-empty line when that line is only the answer line;
    only finite numbers count. None otherwise."""
    found = ANSWER_LINE.match(last_line(reply))
    value = float(found.group(1)) if found else None
    return value if value is not None and math.isfinite(value) else None


def reward(value: float | None, key: int) -> float:
    """1 for the exact count, else 0."""
    return float(value is not None and value == key)


def group(item: dict) -> str:
    """The held-out group: the season. The four station pairs share stations, so a season's
    readings at every station fall on one side of a split (decision 0017)."""
    return str(item["year"])


def split(item: dict) -> str:
    """'test' for about one group in five, picked by a hash of the group key, else 'train'."""
    return "test" if hashlib.sha256(group(item).encode()).digest()[0] % 5 == 0 else "train"


def gold(key: int) -> str:
    """The reference reply for the gold check: the exact count on the answer line (decision
    0021)."""
    return f"ANSWER: {key}"
