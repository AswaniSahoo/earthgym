import pytest

from rlenv.ibtracs import stats


def row(sid, time, status, wind, basin="NA", track="main", season="2024"):
    wind = "" if wind is None else str(wind)
    return {"SID": sid, "SEASON": season, "BASIN": basin, "ISO_TIME": time} | {
        "TRACK_TYPE": track,
        "USA_STATUS": status,
        "USA_WIND": wind,
    }


A = [
    row("A", "2024-06-01 00:00:00", "TD", 30),  # below 34 kt
    row("A", "2024-06-01 06:00:00", "TS", 50),  # 2500
    row("A", "2024-06-01 09:00:00", "TS", 55),  # not a synoptic hour
    row("A", "2024-06-01 12:00:00", "HU", 70),  # 4900
    row("A", "2024-06-01 18:00:00", "SS", 40),  # 1600
    row("A", "2024-06-02 00:00:00", "EX", 45),  # extratropical
]


def test_ace_sums_squared_synoptic_winds_while_named_status_and_34_kt_or_more():
    assert stats.storm(A)["ace"] == pytest.approx(0.9)  # (2500 + 4900 + 1600) / 1e4


def test_counts_take_any_row_at_the_threshold_with_the_right_status():
    assert stats.storm(A) | {"ace": None} == {
        "named": True,
        "hurricane": True,
        "major": False,
        "ace": None,
    }
    extratropical = [
        row("B", "2024-07-01 06:00:00", "TS", 40),
        row("B", "2024-07-02 06:00:00", "EX", 100),
    ]
    assert (stats.storm(extratropical)["hurricane"], stats.storm(extratropical)["named"]) == (
        False,
        True,
    )
    special = [row("C", "2024-08-01 03:00:00", "HU", 100)]  # an off-hour peak still counts
    assert (stats.storm(special)["major"], stats.storm(special)["ace"]) == (True, 0.0)


def test_peak_category_takes_the_highest_hu_wind_at_any_time_on_the_nhc_scale():
    assert stats.category(A) == 1  # 70 kt as HU; 45 kt EX does not count
    off_hour = [
        row("G", "2024-08-01 06:00:00", "HU", 90),
        row("G", "2024-08-01 17:45:00", "HU", 96),
    ]
    assert stats.category(off_hour) == 3  # the 17:45 landfall row counts for the peak
    edges = {63: 0, 64: 1, 82: 1, 83: 2, 95: 2, 96: 3, 112: 3, 113: 4, 136: 4, 137: 5}
    for knots, category in edges.items():
        assert stats.category([row("H", "2024-08-01 06:00:00", "HU", knots)]) == category
    assert stats.category([row("I", "2024-08-01 06:00:00", "EX", 120)]) == 0


def test_hurricane_hours_count_six_for_each_synoptic_hu_row():
    track = [
        row("J", "2024-08-01 00:00:00", "TS", 60),
        row("J", "2024-08-01 06:00:00", "HU", 65),
        row("J", "2024-08-01 09:00:00", "HU", 70),  # 3-hourly: not counted
        row("J", "2024-08-01 12:00:00", "HU", 75),
        row("J", "2024-08-01 17:45:00", "HU", 80),  # off-hour: not counted
        row("J", "2024-08-01 18:00:00", "EX", 70),
    ]
    assert stats.hurricane_hours(track) == 12


def test_season_leaves_out_spur_tracks_and_rows_outside_the_basin():
    spur = [row("D", "2024-08-01 06:00:00", "HU", 80, track="spur-merge")]
    crossing = [
        row("E", "2024-09-01 06:00:00", "TS", 40),
        row("E", "2024-09-02 06:00:00", "HU", 80, basin="EP"),
    ]
    other_year = [row("F", "2023-09-01 06:00:00", "TS", 40, season="2023")]
    result = stats.season(A + spur + crossing + other_year, 2024)
    assert result | {"ace": None} == {"named": 2, "hurricanes": 1, "major": 0, "ace": None}
    assert result["ace"] == pytest.approx(0.9 + 0.16)  # A, and E's 40 kt row inside the basin
