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
