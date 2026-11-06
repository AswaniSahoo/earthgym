"""The bundled heat and storm keys against a second computation (decision 0026).

`key_oracle.py` reads a rendered prompt and nothing else, so a key that passes here follows from
what the model is shown, not from the code that made the key. The fixtures' answers come from the
prompts' rules, worked out without running code.
"""

import ast
import datetime as dt
import json
import sys
from fractions import Fraction
from pathlib import Path

import key_oracle
import pytest
from heat_basis_v1 import contract as heat
from ibtracs_storm_v1 import contract as storm

ROOT = Path(__file__).parents[1]
SEASON = 153  # 1 May to 30 September
COOL = 90


def bundled(package: str) -> list[dict]:
    path = ROOT / "environments" / package / package / f"{package}.jsonl"
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def season(head=(), tail=()) -> list[int | None]:
    return [*head, *[COOL] * (SEASON - len(head) - len(tail)), *tail]


def heat_prompt(question, index, site=None, threshold=110, k=None) -> str:
    first = dt.date(2001, 5, 1)
    days = (first + dt.timedelta(days=n) for n in range(SEASON))
    return heat.prompt(
        {
            "question": question,
            "threshold": threshold,
            "k": k,
            "index_name": "Index Airport",
            "site_name": "Site Campus",
            "dates": [d.strftime("%m-%d") for d in days],
            "index_f": index,
            "site_f": season() if site is None else site,
        }
    )


def storm_prompt(question, *rows) -> str:
    return storm.prompt(
        {
            "question": question,
            "rows": [[f"2000-{when}:00", status, wind, None] for when, status, wind in rows],
        }
    )


@pytest.mark.parametrize(
    ("index", "site", "expected"),
    [
        (season((110, 109, None, 111)), None, 2),  # at the threshold counts, a dash does not
        (season(), season((120, 120)), 0),  # the site's heat is not the index's
    ],
)
def test_trigger_days(index, site, expected):
    assert key_oracle.heat_answer(heat_prompt("trigger_days", index, site)) == expected


@pytest.mark.parametrize(
    ("index", "k", "expected"),
    [
        (season((110, 110, None, 110, 110, 110, 109, 110)), 2, 2),  # a dash ends a run
        (season((110, 110, 110, 110, 110)), 2, 1),  # a long run pays once
        (season((110, 110, 110, 110, 110)), 5, 1),  # exactly k days is enough
        (season((110, 110, 110, 110)), 5, 0),
        (season(tail=(110, 110)), 2, 1),  # a run that ends with the window still pays
    ],
)
def test_events(index, k, expected):
    assert key_oracle.heat_answer(heat_prompt("events", index, k=k)) == expected


def test_missed_days():
    index = season((109, None, 109, 110, 109))
    site = season((110, 110, None, 110, 109))
    assert key_oracle.heat_answer(heat_prompt("missed_days", index, site)) == 2


def test_ace_counts_only_named_synoptic_rows_at_34_kt():
    prompt = storm_prompt(
        "ace",
        ("08-01 00:00", "HU", 100),  # 10000
        ("08-01 03:00", "HU", 100),  # not a six-hourly time
        ("08-01 06:00", "TS", 34),  # 1156
        ("08-01 12:00", "TD", 34),  # not a named status
        ("08-01 12:30", "HU", 100),  # the rule's own example
        ("08-01 18:00", "TS", 33),  # below 34 kt
        ("08-02 00:00", "SS", 50),  # 2500
        ("08-02 06:00", "EX", 60),  # not a named status
    )
    assert key_oracle.storm_answer(prompt) == Fraction(13656, 10000)


@pytest.mark.parametrize(
    ("wind", "expected"),
    [
        (63, 0),
        (64, 1),
        (82, 1),
        (83, 2),
        (95, 2),
        (96, 3),
        (112, 3),
        (113, 4),
        (136, 4),
        (137, 5),
    ],
)
def test_peak_category_at_each_edge_of_the_scale(wind, expected):
    prompt = storm_prompt("peak_category", ("08-01 00:00", "TS", 40), ("08-01 06:00", "HU", wind))
    assert key_oracle.storm_answer(prompt) == expected


def test_peak_category_reads_hu_rows_at_any_time_and_no_others():
    prompt = storm_prompt(
        "peak_category",
        ("08-01 00:00", "HU", 70),
        ("08-01 03:00", "HU", 137),  # any time counts
        ("08-01 06:00", "TS", 150),  # not an HU row
    )
    assert key_oracle.storm_answer(prompt) == 5
    assert key_oracle.storm_answer(storm_prompt("peak_category", ("08-01 00:00", "TS", 90))) == 0


def test_hurricane_hours_counts_six_hours_a_synoptic_hu_row():
    prompt = storm_prompt(
        "hurricane_hours",
        ("08-01 00:00", "HU", 70),
        ("08-01 03:00", "HU", 70),
        ("08-01 06:00", "HU", 70),
        ("08-01 12:00", "TS", 70),
        ("08-01 12:30", "HU", 70),
    )
    assert key_oracle.storm_answer(prompt) == 12


def test_it_refuses_a_prompt_it_cannot_read():
    with pytest.raises(ValueError):
        key_oracle.heat_answer("How many days?")
    with pytest.raises(ValueError):
        key_oracle.storm_answer("How many hours?")
    with pytest.raises(ValueError):
        key_oracle.heat_answer(storm_prompt("ace", ("08-01 00:00", "HU", 100)))
    with pytest.raises(ValueError):
        key_oracle.storm_answer(heat_prompt("trigger_days", season()))


def test_it_imports_only_the_standard_library():
    names = set()
    for node in ast.walk(ast.parse(Path(key_oracle.__file__).read_text("utf-8"))):
        if isinstance(node, ast.Import):
            names |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            names.add(node.module.split(".")[0])
    assert names <= sys.stdlib_module_names


def test_every_bundled_heat_key_follows_from_its_prompt():
    items = bundled("heat_basis_v1")
    assert len(items) == 300
    assert [i["id"] for i in items if key_oracle.heat_answer(heat.prompt(i)) != i["key"]] == []


def test_every_bundled_storm_key_follows_from_its_prompt():
    def right(item: dict) -> bool:
        value = key_oracle.storm_answer(storm.prompt(item))
        if item["question"] == "ace":  # four decimals hold ACE exactly, so compare it exactly
            return value * 10**4 == round(item["key"] * 10**4)
        return value == item["key"]

    items = bundled("ibtracs_storm_v1")
    assert len(items) == 300
    assert [i["id"] for i in items if not right(i)] == []


def test_its_answers_earn_the_environments_full_reward():
    for item in bundled("heat_basis_v1"):
        assert heat.reward(float(key_oracle.heat_answer(heat.prompt(item))), item["key"]) == 1.0
    for item in bundled("ibtracs_storm_v1"):
        value = key_oracle.storm_answer(storm.prompt(item))
        shown = float(round(value, 1)) if item["question"] == "ace" else float(value)
        assert storm.reward(item["question"], shown, item["key"]) == 1.0


SIX_HOURLY = {"00:00", "06:00", "12:00", "18:00"}
NAMED = {"TS", "HU", "SS"}
SCALE = ((137, 5), (113, 4), (96, 3), (83, 2), (64, 1))


def at_or_above(values: list, threshold: int) -> int:
    return sum(v is not None and v >= threshold for v in values)


def run_lengths(values: list, threshold: int, dash_ends: bool = True) -> list[int]:
    runs, run = [], 0
    for value in values:
        if value is None and not dash_ends:
            continue
        if value is not None and value >= threshold:
            run += 1
        else:
            runs.append(run)
            run = 0
    return [*runs, run]


def ace(item: dict, times=SIX_HOURLY, statuses=NAMED, floor: int = 34) -> float:
    rows = item["rows"]
    return (
        sum(
            r[2] ** 2
            for r in rows
            if (times is None or r[0][11:16] in times) and r[1] in statuses and r[2] >= floor
        )
        / 1e4
    )


def peak(item: dict, times=None, statuses=("HU",), scale=SCALE) -> int:
    winds = [
        r[2] for r in item["rows"] if (times is None or r[0][11:16] in times) and r[1] in statuses
    ]
    return next((c for floor, c in scale if max(winds, default=0) >= floor), 0)


def hours(item: dict, times=SIX_HOURLY, statuses=("HU",)) -> int:
    return 6 * sum(
        (times is None or r[0][11:16] in times) and r[1] in statuses for r in item["rows"]
    )


WRONG_RULES = [  # question, the wrong rule, how many of its 100 keys that rule would change
    (
        "trigger_days",
        "above the threshold, not at it",
        lambda i: at_or_above(i["index_f"], i["threshold"] + 1),
        93,
    ),
    ("trigger_days", "the site's column", lambda i: at_or_above(i["site_f"], i["threshold"]), 97),
    (
        "trigger_days",
        "a window a day short",
        lambda i: at_or_above(i["index_f"][:-1], i["threshold"]),
        11,
    ),
    (
        "events",
        "a dash does not end a run",
        lambda i: sum(r >= i["k"] for r in run_lengths(i["index_f"], i["threshold"], False)),
        1,
    ),
    (
        "events",
        "more than k days, not at least k",
        lambda i: sum(r > i["k"] for r in run_lengths(i["index_f"], i["threshold"])),
        50,
    ),
    (
        "events",
        "a long run pays again every k days",
        lambda i: sum(r // i["k"] for r in run_lengths(i["index_f"], i["threshold"])),
        62,
    ),
    (
        "missed_days",
        "above the threshold, not at it",
        lambda i: sum(
            s is not None and s > i["threshold"] and (x is None or x <= i["threshold"])
            for s, x in zip(i["site_f"], i["index_f"], strict=True)
        ),
        79,
    ),
    (
        "missed_days",
        "a missing index value is not a miss",
        lambda i: sum(
            s is not None and s >= i["threshold"] and x is not None and x < i["threshold"]
            for s, x in zip(i["site_f"], i["index_f"], strict=True)
        ),
        8,
    ),
    ("ace", "every row, not the six-hourly ones", lambda i: ace(i, times=None), 100),
    ("ace", "any status", lambda i: ace(i, statuses={r[1] for r in i["rows"]}), 44),
    ("ace", "no 34 kt floor", lambda i: ace(i, floor=0), 0),  # no named row in these is below it
    ("peak_category", "six-hourly rows only", lambda i: peak(i, times=SIX_HOURLY), 4),
    ("peak_category", "any status", lambda i: peak(i, statuses={r[1] for r in i["rows"]}), 0),
    (
        "peak_category",
        "category 3 from 95 kt",
        lambda i: peak(i, scale=((137, 5), (113, 4), (95, 3), (83, 2), (64, 1))),
        3,
    ),
    ("hurricane_hours", "every HU row", lambda i: hours(i, times=None), 99),
    ("hurricane_hours", "any named status", lambda i: hours(i, statuses=NAMED), 100),
]


@pytest.mark.parametrize(
    ("question", "rule", "changed"),
    [(q, f, n) for q, _, f, n in WRONG_RULES],
    ids=[f"{q}: {label}" for q, label, _, _ in WRONG_RULES],
)
def test_a_wrong_rule_would_change_this_many_keys(question, rule, changed):
    """What a clean comparison is worth: a key made by a wrong rule would differ from the oracle
    on this many items. A count of 0 or 1 is a clause the bundled keys barely test."""
    items = bundled("heat_basis_v1") + bundled("ibtracs_storm_v1")
    asked = [i for i in items if i["question"] == question]
    assert len(asked) == 100
    assert sum(abs(rule(i) - i["key"]) > 1e-9 for i in asked) == changed
