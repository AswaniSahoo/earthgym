"""A second computation of the heat and storm answers, from a rendered prompt alone (decision 0026).

Written by an AI agent (Claude Fable 5.1) that saw only the rendered prompts, never the keys or the
code that made them. Every parameter, row and question is read out of the prompt, and each rule is
applied as literally as its wording allows. Anything the text does not state exactly raises
ValueError rather than being guessed.
"""

import datetime
import re
from fractions import Fraction

_MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}
_YEAR = 2000  # leap year, so every month-day the prompts could show is a valid date
_ANSWER_LINE = r" The last line of your response must be 'ANSWER: <number>'\."
_TIME = r"(\d\d):(\d\d)"

_HEAT_HEAD = re.compile(
    r"A parametric heat policy pays from the daily maximum temperature at an index weather "
    r"station, ([^;]+); the insured worker is at ([^.]+)\. The cover runs from "
    r"(\d{1,2}) ([A-Z][a-z]+) to (\d{1,2}) ([A-Z][a-z]+)\. Below are both stations' daily maximum "
    r"temperatures in whole degrees F from GHCN-Daily, with the year left out; a dash means no "
    r"value\."
)
_HEAT_ROW = re.compile(r"(\d\d)-(\d\d) \| (-|\d+) \| (-|\d+)")
_TRIGGER = (
    r"Rule\. A trigger day is a day on which the index station's maximum is at or above (\d+) F\. "
    r"A missing value is never a trigger day"
)
_HEAT_TRIGGER = re.compile(
    _TRIGGER + r"\.\n\nHow many trigger days did the index station have from "
    r"(\d{1,2}) ([A-Z][a-z]+) to (\d{1,2}) ([A-Z][a-z]+)\?" + _ANSWER_LINE
)
_HEAT_EVENTS = re.compile(
    _TRIGGER + r" and ends a run\. An event is a run of at least (\d+) consecutive trigger "
    r"days; it pays once, however long it lasts\.\n\nHow many events did the policy pay for\?"
    + _ANSWER_LINE
)
_HEAT_MISSED = re.compile(
    r"Rule\. A missed day is a day on which the insured site's maximum is at or above (\d+) F "
    r"while the index station's maximum is not; a missing index value counts as not at or above "
    r"the threshold\. A missing site value is never a missed day\.\n\n"
    r"How many missed days were there\?" + _ANSWER_LINE
)

_STORM_HEAD = (
    "Below is one North Atlantic storm's track from the IBTrACS archive, with every row the "
    "archive has: the 6-hourly rows, the 3-hourly rows between them, and extra rows at other "
    "times. Times are UTC, written month-day hour:minute, with the year left out. Winds are "
    "maximum sustained winds in knots (kt); pressure is the minimum central pressure in mb, "
    "and a dash means no value."
)
_STORM_HEADER = "time | status | wind (kt) | pressure (mb)"
_STORM_ROW = re.compile(r"(\d\d)-(\d\d) (\d\d):(\d\d) \| ([A-Z]{2}) \| (-|\d+) \| (-|\d+)")
_STATUSES = re.compile(r"Statuses: ([A-Z]{2} [a-z ]+(?:, [A-Z]{2} [a-z ]+)*)\.")
_SYNOPTIC = (
    r" at exactly "
    + _TIME
    + ", "
    + _TIME
    + ", "
    + _TIME
    + " or "
    + _TIME
    + r" UTC \(a row at "
    + _TIME
    + r" does not count\) whose status is "
)
_STORM_ACE = re.compile(
    r"Rule\. ACE: take every row" + _SYNOPTIC + r"([A-Z]{2}), ([A-Z]{2}) or ([A-Z]{2}) and whose "
    r"wind is (\d+) kt or more; square each of those winds, add the squares, and divide the sum "
    r"by 10\^(\d+)\. Rows at any other time do not count\.\n\n"
    r"What is this storm's accumulated cyclone energy \(ACE\), in units of 10\^(\d+) kt\^2, "
    r"rounded to one decimal\?" + _ANSWER_LINE
)
_STORM_PEAK = re.compile(
    r"Rule\. Peak category: take the highest wind on any row with status (?P<st>[A-Z]{2}), at "
    r"any time, and place it on the Saffir-Simpson scale: (\d+) to (\d+) kt is category (\d+), "
    r"(\d+) to (\d+) kt is (\d+), (\d+) to (\d+) kt is (\d+), (\d+) to (\d+) kt is (\d+), "
    r"(\d+) kt or more is (\d+)\. A storm with no (?P<zst>[A-Z]{2}) row at (?P<zlow>\d+) kt or "
    r"more is (?P<zcat>\d+)\.\n\nWhat is this storm's peak Saffir-Simpson category\?" + _ANSWER_LINE
)
_STORM_HOURS = re.compile(
    r"Rule\. Hours at hurricane strength: count (\d+) hours for each row"
    + _SYNOPTIC
    + r"([A-Z]{2})\. Rows at any other time do not count\.\n\n"
    r"For how many hours was this storm at hurricane strength\?" + _ANSWER_LINE
)


def _date(month, day):
    try:
        return datetime.date(_YEAR, int(month), int(day))
    except ValueError as exc:
        raise ValueError(f"bad date {month}-{day}") from exc


def _value(cell):
    return None if cell == "-" else int(cell)


def _heat_table(text, index, site):
    lines = text.split("\n")
    if lines[0] != f"date | index: {index} | site: {site}":
        raise ValueError("unexpected heat table header")
    rows = {}
    for line in lines[1:]:
        m = _HEAT_ROW.fullmatch(line)
        if m is None:
            raise ValueError(f"malformed heat row: {line!r}")
        day = _date(m.group(1), m.group(2))
        if day in rows:
            raise ValueError(f"duplicate heat row for {line[:5]}")
        rows[day] = (_value(m.group(3)), _value(m.group(4)))
    if not rows:
        raise ValueError("empty heat table")
    return rows


def _window(d1, m1, d2, m2):
    if m1 not in _MONTHS or m2 not in _MONTHS:
        raise ValueError("unknown month name")
    start, end = _date(_MONTHS[m1], d1), _date(_MONTHS[m2], d2)
    if end < start:
        raise ValueError("cover window ends before it starts")
    return [start + datetime.timedelta(days=i) for i in range((end - start).days + 1)]


def heat_answer(prompt: str) -> int:
    """Answer a heat prompt: trigger days, paid events, or missed days."""
    parts = prompt.split("\n\n")
    if len(parts) != 4:
        raise ValueError("not a heat prompt")
    head = _HEAT_HEAD.fullmatch(parts[0])
    if head is None:
        raise ValueError("not a heat prompt")
    index, site = head.group(1), head.group(2)
    days = _window(*head.group(3, 4, 5, 6))
    rows = _heat_table(parts[1], index, site)
    missing = (None, None)
    index_max = [rows.get(d, missing)[0] for d in days]
    site_max = [rows.get(d, missing)[1] for d in days]
    tail = parts[2] + "\n\n" + parts[3]

    m = _HEAT_TRIGGER.fullmatch(tail)
    if m is not None:
        if _window(*m.group(2, 3, 4, 5)) != days:
            raise ValueError("question window differs from the cover")
        threshold = int(m.group(1))
        return sum(1 for v in index_max if v is not None and v >= threshold)

    m = _HEAT_EVENTS.fullmatch(tail)
    if m is not None:
        threshold, min_run = int(m.group(1)), int(m.group(2))
        if min_run < 1:
            raise ValueError("event length must be at least 1")
        events = run = 0
        for v in index_max + [None]:
            if v is not None and v >= threshold:
                run += 1
                continue
            if run >= min_run:
                events += 1
            run = 0
        return events

    m = _HEAT_MISSED.fullmatch(tail)
    if m is not None:
        threshold = int(m.group(1))
        return sum(
            1
            for s, i in zip(site_max, index_max, strict=True)
            if s is not None and s >= threshold and (i is None or i < threshold)
        )
    raise ValueError("unknown heat question")


def _storm_rows(text, statuses):
    lines = text.split("\n")
    if lines[0] != _STORM_HEADER:
        raise ValueError("unexpected storm table header")
    rows, seen = [], set()
    for line in lines[1:]:
        m = _STORM_ROW.fullmatch(line)
        if m is None:
            raise ValueError(f"malformed storm row: {line!r}")
        month, day, hour, minute, status, wind, _pressure = m.groups()
        _date(month, day)
        if not (int(hour) < 24 and int(minute) < 60):
            raise ValueError(f"bad time in row: {line!r}")
        if status not in statuses:
            raise ValueError(f"unknown status {status}")
        if line[:11] in seen:
            raise ValueError(f"duplicate time {line[:11]}")
        seen.add(line[:11])
        rows.append((f"{hour}:{minute}", status, _value(wind)))
    if not rows:
        raise ValueError("empty storm table")
    return rows


def _synoptic_times(groups):
    times = {f"{h}:{m}" for h, m in zip(groups[0::2], groups[1::2], strict=True)}
    if len(times) != 4:
        raise ValueError("synoptic times are not four distinct times")
    return times


def storm_answer(prompt: str) -> "Fraction | int":
    """Answer a storm prompt: ACE (exact Fraction), peak category, or hurricane hours."""
    parts = prompt.split("\n\n")
    if len(parts) != 5 or parts[0] != _STORM_HEAD:
        raise ValueError("not a storm prompt")
    m = _STATUSES.fullmatch(parts[2])
    if m is None:
        raise ValueError("unreadable status list")
    statuses = {item.split(" ", 1)[0] for item in m.group(1).split(", ")}
    rows = _storm_rows(parts[1], statuses)
    tail = parts[3] + "\n\n" + parts[4]

    m = _STORM_ACE.fullmatch(tail)
    if m is not None:
        times = _synoptic_times(m.groups()[0:8])
        counted = set(m.group(11, 12, 13))
        min_wind, power, unit = int(m.group(14)), int(m.group(15)), int(m.group(16))
        if power != unit or not counted <= statuses:
            raise ValueError("ACE rule and question disagree")
        total = sum(
            w * w
            for t, s, w in rows
            if t in times and s in counted and w is not None and w >= min_wind
        )
        return Fraction(total, 10**power)

    m = _STORM_PEAK.fullmatch(tail)
    if m is not None:
        status = m.group("st")
        zero_low, zero_cat = int(m.group("zlow")), int(m.group("zcat"))
        nums = [int(x) for x in m.group(*range(2, 16))]
        bands = [tuple(nums[i : i + 3]) for i in range(0, 12, 3)]  # (low, high, category)
        top_low, top_cat = nums[12], nums[13]
        contiguous = all(bands[i][1] + 1 == bands[i + 1][0] for i in range(3))
        if (
            status != m.group("zst")
            or status not in statuses
            or zero_low != bands[0][0]
            or not contiguous
            or bands[3][1] + 1 != top_low
        ):
            raise ValueError("Saffir-Simpson bands do not join up")
        winds = [w for _t, s, w in rows if s == status and w is not None]
        if not winds or max(winds) < zero_low:
            return zero_cat
        peak = max(winds)
        for low, high, cat in bands:
            if low <= peak <= high:
                return cat
        return top_cat

    m = _STORM_HOURS.fullmatch(tail)
    if m is not None:
        hours, times, status = int(m.group(1)), _synoptic_times(m.groups()[1:9]), m.group(12)
        if status not in statuses:
            raise ValueError("unknown status in hours rule")
        return hours * sum(1 for t, s, _w in rows if t in times and s == status)
    raise ValueError("unknown storm question")
