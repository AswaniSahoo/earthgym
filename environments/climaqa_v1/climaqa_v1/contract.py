"""One answer contract for every harness: the prompts and the exact correctness rules.

Inspect (rlenv.climaqa.tasks) and verifiers (climaqa_v1.taskset) both import this module, so they
show the same prompt and count the same replies as correct.
"""

import re

LETTERS = "ABCD"
MCQ_PROMPT = (
    "Answer the following multiple choice question. The last line of your response must be "
    "'ANSWER: X' where X is one of A, B, C, D.\n\n{question}\n\n{options}"
)
CLOZE_PROMPT = (
    "Fill in the <MASK> in this climate science statement. "
    "Reply with only the missing word or phrase.\n\n{question}"
)
ANSWER_LINE = re.compile(r"^[ \t]*ANSWER[ \t]*:[ \t]*\(?([A-D])\)?[ \t]*\.?[ \t]*$", re.IGNORECASE)
ARTICLES = {"a", "an", "the"}


def mcq_prompt(question: str, options: list[str]) -> str:
    listed = "\n".join(f"{letter}) {text}" for letter, text in zip(LETTERS, options, strict=True))
    return MCQ_PROMPT.format(question=question, options=listed)


def cloze_prompt(question: str) -> str:
    return CLOZE_PROMPT.format(question=question)


def last_line(reply: str) -> str:
    """The reply's last non-empty line, with Markdown bold and code marks and the Unicode minus
    read as plain text: the one line an answer may sit on, as the prompt asks (decision 0016)."""
    plain = reply.replace("*", "").replace("`", "").replace("\u2212", "-")
    lines = [line for line in plain.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def mcq_choice(reply: str) -> str | None:
    """The letter when the reply's last non-empty line is only 'ANSWER: X'; None otherwise."""
    found = ANSWER_LINE.match(last_line(reply))
    return found.group(1).upper() if found else None


def mcq_correct(reply: str, key: str) -> bool:
    return mcq_choice(reply) == key


OPERATORS = set("+/^=<>")  # not *, which marks Markdown bold


def _kept(text: str, i: int) -> bool:
    """Whether the punctuation at i carries meaning: an operator, a decimal point between
    digits, or a minus sign before a number (not a hyphen inside a word)."""
    c = text[i]
    prev = text[i - 1] if i else " "
    nxt = text[i + 1] if i + 1 < len(text) else " "
    if c in OPERATORS:
        return True
    if c == "." and prev.isdigit() and nxt.isdigit():
        return True
    return c == "-" and nxt.isdigit() and not (prev.isalnum() or prev in "._")


def normalize(text: str) -> str:
    """SQuAD-style: casefold, drop a/an/the, and turn punctuation into spaces (so hyphenated
    words split), except what carries meaning in a science answer: an operator, a decimal point
    between digits, and a minus sign before a number (decision 0016)."""
    text = text.casefold().replace("\u2212", "-")
    chars = (
        c if c.isalnum() or c.isspace() or c == "_" or _kept(text, i) else " "
        for i, c in enumerate(text)
    )
    return " ".join(w for w in "".join(chars).split() if w not in ARTICLES)


def cloze_correct(reply: str, key: str) -> bool:
    return normalize(key) != "" and normalize(reply) == normalize(key)
