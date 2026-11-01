"""One answer contract for the IBTrACS storm questions: the prompt with its rules, the answer
line and the reward (decisions 0009 and 0011).

The Inspect task and the verifiers taskset both import this module, so they read the same
replies and pay the same reward.
"""

import re

QUESTIONS = {  # question: (what is asked, the rule that answers it)
    "ace": (
        "What is this storm's accumulated cyclone energy (ACE), in units of 10^4 kt^2, rounded "
        "to one decimal?",
        "ACE: take every row at 00, 06, 12 or 18 UTC whose status is TS, HU or SS and whose "
        "wind is 34 kt or more; square each of those winds, add the squares, and divide the sum "
        "by 10^4. Rows at any other time do not count.",
    ),
    "peak_category": (
        "What is this storm's peak Saffir-Simpson category?",
        "Peak category: take the highest wind on any row with status HU, at any time, and place "
        "it on the Saffir-Simpson scale: 64 to 82 kt is category 1, 83 to 95 kt is 2, 96 to "
        "112 kt is 3, 113 to 136 kt is 4, 137 kt or more is 5. A storm with no HU row is 0.",
    ),
    "hurricane_hours": (
        "For how many hours was this storm at hurricane strength?",
        "Hours at hurricane strength: count 6 hours for each row at 00, 06, 12 or 18 UTC whose "
        "status is HU. Rows at any other time do not count.",
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
TOLERANCE = 0.05  # ACE: half a step of one decimal around the exact value (decision 0011)


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


def answer(reply: str) -> float | None:
    """The number on the last 'ANSWER: <number>' line, or None. A Unicode minus counts."""
    found = ANSWER_LINE.findall(reply.replace("\u2212", "-"))
    return float(found[-1]) if found else None


def reward(question: str, value: float | None, key: float) -> float:
    """1 for a right answer, else 0: ACE within TOLERANCE of the exact value (with room for
    float rounding), the other questions exactly."""
    if value is None:
        return 0.0
    if question == "ace":
        return float(abs(value - key) <= TOLERANCE + 1e-9)
    return float(value == key)
