"""One answer contract for the IBTrACS storm questions: the prompt with its rules, the answer
line and the reward (decisions 0009 and 0011), and the read-only SQL query over a storm's rows
for tools mode (decision 0023).

The Inspect task and the verifiers taskset both import this module, so they read the same
replies, run the same queries and pay the same reward.
"""

import hashlib
import math
import re
import sqlite3
from time import monotonic

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


MAX_ROWS = 200  # rows in one query reply
MAX_CHARS = 8000  # characters in one query reply, and in any one value
MAX_SECONDS = 0.5  # for one query
READS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}


def _shown(row: list) -> tuple:
    """A row as the prompt shows it: the time as month-day hour:minute, the status, the wind
    and the pressure (None for no value)."""
    when, status, wind, pressure = row
    return when[5:16], status, wind, pressure


def prompt(item: dict, rules: bool = True) -> str:
    """The task text: the storm's rows and the rule for the question (left out for the
    rules-hidden ablation); never the key, the name, the year or the SID."""
    question, rule = QUESTIONS[item["question"]]
    lines = "\n".join(
        f"{when} | {status} | {wind} | {'-' if pressure is None else pressure}"
        for when, status, wind, pressure in map(_shown, item["rows"])
    )
    rule = f"Rule. {rule}\n\n" if rules else ""
    return PROMPT.format(rows=lines, statuses=STATUSES, rule=rule, question=question)


def database(rows: list) -> sqlite3.Connection:
    """An in-memory SQLite database with one table, track, holding the rows as the prompt shows
    them. Once filled it authorizes only SELECT, column reads and functions, so every write,
    ATTACH, VACUUM INTO and PRAGMA is refused, and no value may be longer than a reply: a
    single function call such as randomblob(10^9) runs past any deadline."""
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE track (time TEXT, status TEXT, wind INTEGER, pressure INTEGER)")
    db.executemany("INSERT INTO track VALUES (?, ?, ?, ?)", map(_shown, rows))
    db.commit()
    db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_CHARS)
    db.set_authorizer(
        lambda action, *_: sqlite3.SQLITE_OK if action in READS else sqlite3.SQLITE_DENY
    )
    return db


def query(db: sqlite3.Connection, sql: str) -> str:
    """One SQL statement's result as text: the column names, then up to MAX_ROWS rows, values
    joined by ' | ' and NULL for no value, in at most about MAX_CHARS characters, with a note
    when cut. A statement still running after MAX_SECONDS is interrupted. A refused, failed or
    interrupted statement comes back as 'error: <reason>', so the model reads every error and
    nothing is raised."""
    deadline = monotonic() + MAX_SECONDS
    db.set_progress_handler(lambda: monotonic() > deadline, 1000)  # every 1000 instructions
    note = ""
    try:
        cursor = db.execute(sql)
        lines = [" | ".join(column[0] for column in cursor.description or ())]
        size = len(lines[0])
        for row in cursor:  # read lazily, so a cut stops the statement too
            if len(lines) > MAX_ROWS:
                note = f"(only the first {MAX_ROWS} rows)"
                break
            lines.append(" | ".join("NULL" if value is None else str(value) for value in row))
            size += 1 + len(lines[-1])
            if size > MAX_CHARS:
                break
        if len(lines) == 1:
            lines.append("(no rows)")
    except sqlite3.Error as error:
        lines, note = [f"error: {error}"], ""
    text = "\n".join(lines)
    if len(text) > MAX_CHARS:
        cut = text.rfind("\n", 0, MAX_CHARS)
        text, note = text[: cut if cut > 0 else MAX_CHARS], f"(cut at {MAX_CHARS} characters)"
    return f"{text}\n{note}" if note else text


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


def group(item: dict) -> str:
    """The held-out group: the storm, so every question on one storm falls on one side of a
    split (decision 0017)."""
    return item["sid"]


def split(item: dict) -> str:
    """'test' for about one group in five, picked by a hash of the group key, else 'train'."""
    return "test" if hashlib.sha256(group(item).encode()).digest()[0] % 5 == 0 else "train"


def gold(question: str, key: float) -> str:
    """The reference reply for the gold check: the key as the question asks for it, ACE at one
    decimal (decision 0021)."""
    if question == "ace":
        return f"ANSWER: {min(_roundings(key)) / 10:.1f}"
    return f"ANSWER: {int(key)}"
