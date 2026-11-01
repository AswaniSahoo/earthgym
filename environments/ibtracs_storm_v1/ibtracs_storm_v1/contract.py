"""One answer contract for the IBTrACS storm questions: the prompt with its rules, the answer
line and the reward (decisions 0009 and 0011).

The Inspect task and the verifiers taskset both import this module, so they read the same
replies and pay the same reward.
"""

import math
import re

QUESTIONS = {  # question: (what is asked, the rule that answers it)
    "ace": (
        "What is this storm's accumulated cyclone energy (ACE), in units of 10^4 kt^2, rounded "
        "to one decimal?",
        "ACE: take every row at exactly 00:00, 06:00, 12:00 or 18:00 UTC (a row at 12:30 does "
        "not count) whose status is TS, HU or SS and whose wind is 34 kt or more; square each "
        "of those winds, add the squares, and divide the sum by 10^4. Rows at any other time do "
        "not count.",
    ),
    "peak_category": (
        "What is this storm's peak Saffir-Simpson category?",
        "Peak category: take the highest wind on any row with status HU, at any time, and place "
        "it on the Saffir-Simpson scale: 64 to 82 kt is category 1, 83 to 95 kt is 2, 96 to "
        "112 kt is 3, 113 to 136 kt is 4, 137 kt or more is 5. A storm with no HU row at 64 kt "
        "or more is 0.",
    ),
    "hurricane_hours": (
        "For how many hours was this storm at hurricane strength?",
        "Hours at hurricane strength: count 6 hours for each row at exactly 00:00, 06:00, 12:00 "
        "or 18:00 UTC (a row at 12:30 does not count) whose status is HU. Rows at any other "
        "time do not count.",
    ),
}
STATUSES = (
    "Statuses: TD tropical depression, TS tropical storm, HU hurricane, EX extratropical "
    "cyclone, SD subtropical depression, SS subtropical storm, LO low, WV tropical wave, DB "
    "disturbance."
)
PROMPT = (
    "Below is one North Atlantic storm's track from the IBTrACS archive, with every row the "
    "archive has: the 6-hourly rows, the 3-hourly rows between them, and extra rows at other "
    "times. Times are UTC, written month-day hour:minute, with the year left out. Winds are "
    "maximum sustained winds in knots (kt); pressure is the minimum central pressure in mb, and "
    "a dash means no value.\n\n"
    "time | status | wind (kt) | pressure (mb)\n{rows}\n\n"
    "{statuses}\n\n{rule}"
    "{question} The last line of your response must be 'ANSWER: <number>'."
)
NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
ANSWER_LINE = re.compile(  # horizontal space only, so the number sits on the answer line
    rf"^[ \t]*ANSWER[ \t]*:[ \t]*({NUMBER})[ \t]*\.?[ \t]*$", re.MULTILINE | re.IGNORECASE
)


def prompt(item: dict, rules: bool = True) -> str:
    """The task text: the storm's rows and the rule for the question (left out for the
    rules-hidden ablation); never the key, the name, the year or the SID."""
    question, rule = QUESTIONS[item["question"]]
    lines = "\n".join(
        f"{time[5:16]} | {status} | {wind} | {'-' if pressure is None else pressure}"
        for time, status, wind, pressure in item["rows"]
    )
    rule = f"Rule. {rule}\n\n" if rules else ""
    return PROMPT.format(rows=lines, statuses=STATUSES, rule=rule, question=question)


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


def _tenths(value: float) -> int | None:
    """value times 10 as an integer, when value has at most one decimal; else None."""
    tenths = round(value * 10)
    return tenths if abs(value * 10 - tenths) < 1e-6 else None


def _roundings(key: float) -> set[int]:
    """The one-decimal roundings of an exact ACE key (kept to four decimals), in tenths: one,
    or both neighbours of a tie."""
    whole, rest = divmod(round(key * 1e4), 1000)
    return {whole} if rest < 500 else {whole + 1} if rest > 500 else {whole, whole + 1}


def reward(question: str, value: float | None, key: float) -> float:
    """1 for a right answer, else 0. ACE must be the exact value rounded to one decimal, or
    either neighbour when the exact value ends in 5 at the second decimal and 0 after it
    (decision 0016); the other questions must match exactly."""
    if value is None:
        return 0.0
    if question == "ace":
        return float(_tenths(value) in _roundings(key))
    return float(value == key)
