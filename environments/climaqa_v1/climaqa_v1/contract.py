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
ANSWER_LINE = re.compile(r"^\s*ANSWER\s*:\s*\(?([A-D])\)?\s*\.?\s*$", re.MULTILINE | re.IGNORECASE)
ARTICLES = re.compile(r"\b(a|an|the)\b")


def mcq_prompt(question: str, options: list[str]) -> str:
    listed = "\n".join(f"{letter}) {text}" for letter, text in zip(LETTERS, options, strict=True))
    return MCQ_PROMPT.format(question=question, options=listed)


def cloze_prompt(question: str) -> str:
    return CLOZE_PROMPT.format(question=question)


def mcq_choice(reply: str) -> str | None:
    """The letter on the last line that is only 'ANSWER: X'; markdown bold and code marks are
    ignored. None when no line follows the format."""
    found = ANSWER_LINE.findall(reply.replace("*", "").replace("`", ""))
    return found[-1].upper() if found else None


def mcq_correct(reply: str, key: str) -> bool:
    return mcq_choice(reply) == key


def normalize(text: str) -> str:
    """SQuAD-style: casefold, punctuation to spaces (so hyphens split), drop a/an/the."""
    text = re.sub(r"[^\w\s]", " ", text.casefold())
    return " ".join(ARTICLES.sub(" ", text).split())


def cloze_correct(reply: str, key: str) -> bool:
    return normalize(key) != "" and normalize(reply) == normalize(key)
