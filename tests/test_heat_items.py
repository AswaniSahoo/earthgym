import json
from collections import Counter

import pytest

from earthgym.heat import items, policy, stats

T = stats.tenths


def test_plan_draws_distinct_specs_per_question():
    specs = items.plan(n=5, seed=0)
    assert Counter(s["question"] for s in specs) == {
        "trigger_days": 5,
        "events": 5,
        "missed_days": 5,
    }
    triggers = [
        (s["index"], s["year"], s["threshold"]) for s in specs if s["question"] == "trigger_days"
    ]
    assert len(set(triggers)) == 5
    assert all(2 <= s["k"] <= 5 for s in specs if s["question"] == "events")
    assert all(s["k"] is None for s in specs if s["question"] != "events")
    assert all(s["index"] in items.INDEXES and s["site"] in items.SITES for s in specs)
    assert items.plan(n=5, seed=0) == specs


def series():
    index = {"20200501": T(110), "20200502": T(111), "20200503": T(109)}
    site = {"20200501": T(112), "20200503": T(110)}  # 05-02 missing at the site
    return {items.INDEXES[0]: index, items.SITES[0]: site}


def test_make_item_shows_whole_degrees_dashes_and_the_exact_key():
    spec = {"question": "missed_days", "index": items.INDEXES[0], "site": items.SITES[0]}
    spec |= {"year": 2020, "threshold": 110, "k": None}
    item = items.make_item(spec, series())
    assert item["id"] == f"missed_days/{items.INDEXES[0]}/{items.SITES[0]}/2020/110"
    names = (item["index_name"], item["site_name"])
    assert names == (items.NAMES[items.INDEXES[0]], items.NAMES[items.SITES[0]])
    assert (len(item["dates"]), item["dates"][0], item["dates"][-1]) == (153, "05-01", "09-30")
    assert item["index_f"][:4] == [110, 111, 109, None]
    assert item["site_f"][:4] == [112, None, 110, None]
    assert item["key"] == 1 == policy.missed_days(*series().values(), 2020, 110)  # 05-03


def test_events_items_carry_k_in_the_id_and_the_key():
    spec = {"question": "events", "index": items.INDEXES[0], "site": items.SITES[0]}
    spec |= {"year": 2020, "threshold": 110, "k": 2}
    item = items.make_item(spec, series())
    assert item["id"].endswith("/2020/110/2") and item["key"] == 1  # 05-01 and 05-02


def test_write_records_the_items_sha256_in_the_manifest(tmp_path):
    spec = {"question": "trigger_days", "index": items.INDEXES[0], "site": items.SITES[0]}
    spec |= {"year": 2020, "threshold": 110, "k": None}
    out, manifest = tmp_path / "items.jsonl", tmp_path / "manifest.json"
    items.write([items.make_item(spec, series())], out, manifest, seed=2026)
    m = json.loads(manifest.read_text())
    assert (m["n"], m["seed"], m["questions"]) == (1, 2026, {"trigger_days": 1})
    assert len(m["sha256"]) == 64 and set(m["stations"]) == set(items.INDEXES + items.SITES)
    assert json.loads(out.read_text())["key"] == 2


def test_key_refuses_an_unknown_question():
    spec = {"question": "hot_days", "index": items.INDEXES[0], "site": items.SITES[0]}
    spec |= {"year": 2020, "threshold": 110, "k": None}
    with pytest.raises(ValueError, match="unknown question 'hot_days'"):
        items.key(spec, series())
