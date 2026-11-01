import json

import pytest

from rlenv.ibtracs import items


def row(sid, time, status, wind, season="2021", basin="NA", track="main", pres="1000"):
    wind = "" if wind is None else str(wind)
    return {"SID": sid, "SEASON": season, "BASIN": basin, "ISO_TIME": time} | {
        "TRACK_TYPE": track,
        "USA_STATUS": status,
        "USA_WIND": wind,
        "USA_PRES": pres,
        "NAME": "TEST",
    }


def named(sid, season="2021"):
    return [row(sid, f"{season}-08-26 12:00:00", "TS", 40, season=season)]


def hurricane(sid):
    return [row(sid, "2021-08-26 12:00:00", "TS", 50), row(sid, "2021-08-26 18:00:00", "HU", 70)]


def test_eligible_keeps_named_storms_of_final_seasons_from_1980_inside_the_basin():
    tracks = {
        "ok": named("ok"),
        "never named": [row("never named", "2021-08-26 12:00:00", "TD", 30)],
        "1979": named("1979", season="1979"),
        "2026": [row("2026", "2026-08-26 12:00:00", "TS", 40, "2026", track="PROVISIONAL")],
        "crosses": named("crosses") + [row("crosses", "2021-08-27 00:00:00", "TS", 40, basin="EP")],
        "spur": [row("spur", "2021-08-26 12:00:00", "TS", 40, track="spur-merge")],
        "blank": named("blank") + [row("blank", "2021-08-27 00:00:00", "", None)],
    }
    assert sorted(items.eligible(tracks)) == ["ok"]


def test_keys_follow_the_reference_rules():
    track = [
        row("A", "2021-08-26 12:00:00", "TS", 50),  # 2500
        row("A", "2021-08-26 12:30:00", "HU", 80),  # a synoptic hour with minutes: not counted
        row("A", "2021-08-26 15:00:00", "TS", 60),  # 3-hourly
        row("A", "2021-08-26 18:00:00", "HU", 70),  # 4900, 6 h
        row("A", "2021-08-26 23:25:00", "HU", 100),  # landfall row: peak only
        row("A", "2021-08-27 00:00:00", "HU", 90),  # 8100, 6 h
        row("A", "2021-08-27 06:00:00", "EX", 60),  # extratropical
    ]
    assert items.keys(track) == {"ace": 1.55, "peak_category": 3, "hurricane_hours": 12}


def test_plan_draws_ace_from_all_named_storms_then_hurricanes_for_the_rest():
    tracks = {f"n{k}": named(f"n{k}") for k in range(4)} | {
        f"h{k}": hurricane(f"h{k}") for k in range(8)
    }
    chosen = items.plan(tracks, n=2, seed=0)
    questions = [q for q, _ in chosen]
    assert sorted(questions) == sorted(["ace", "peak_category", "hurricane_hours"] * 2)
    assert len({sid for _, sid in chosen}) == 6
    assert all(sid.startswith("h") for q, sid in chosen if q != "ace")
    assert items.plan(tracks, n=2, seed=0) == chosen
    # over many seeds the ACE draw takes hurricanes too, as often as the population holds them
    drawn = [sid for s in range(200) for q, sid in items.plan(tracks, n=2, seed=s) if q == "ace"]
    assert 0.55 < sum(sid.startswith("h") for sid in drawn) / len(drawn) < 0.78  # 8 of 12


def test_plan_refuses_too_few_storms():
    with pytest.raises(ValueError, match="storms"):
        items.plan({"n0": named("n0"), "h0": hurricane("h0")}, n=1)


def test_make_item_keeps_every_row_in_order_with_the_key():
    track = hurricane("h0")
    item = items.make_item("h0", track, "hurricane_hours")
    assert item["id"] == "hurricane_hours/h0" and item["key"] == 6
    assert item["rows"] == [
        ["2021-08-26 12:00:00", "TS", 50, 1000],
        ["2021-08-26 18:00:00", "HU", 70, 1000],
    ]
    assert (item["season"], item["name"]) == (2021, "TEST")


def test_write_records_the_items_sha256_in_the_manifest(tmp_path):
    rows = [items.make_item("h0", hurricane("h0"), "ace")]
    out, manifest = tmp_path / "items.jsonl", tmp_path / "manifest.json"
    items.write(rows, out, manifest, seed=2026)
    m = json.loads(manifest.read_text())
    assert m["n"] == 1 and m["seed"] == 2026 and m["questions"] == {"ace": 1}
    assert len(m["sha256"]) == 64
    assert json.loads(out.read_text().splitlines()[0])["key"] == pytest.approx(
        0.74
    )  # TS 50 and HU 70
