from datetime import datetime

import numpy as np
import pytest

from earthgym.era5 import data


def test_positions_finds_each_wanted_time_and_refuses_a_missing_one():
    times = np.array([0, 6, 12, 18])
    assert data.positions(times, [6, 18]).tolist() == [1, 3]
    with pytest.raises(ValueError, match="1 times"):
        data.positions(times, [6, 7])


def test_epoch_reads_cf_hours_since_units():
    assert data.epoch("hours since 1959-01-01") == datetime(1959, 1, 1)


def test_align_picks_the_climatology_of_each_valid_day_of_year_and_hour():
    hours, days = np.array([0, 6, 12, 18]), np.arange(1, 367)
    clim = (100 * np.arange(4)[:, None] + days[None, :])[:, :, None, None]  # hour, day, lat, lon
    valid = [datetime(2020, 12, 31, 18), datetime(2021, 1, 1, 6)]  # day 366 of a leap year
    assert data.align(clim, hours, days, valid)[:, 0, 0].tolist() == [666, 101]


def test_load_accepts_only_the_pinned_subset(tmp_path, monkeypatch):
    path = tmp_path / "subset.npz"
    arrays = {"forecast": np.arange(4, dtype="f4"), "latitude": np.array([-45.0, 45.0])}
    np.savez(path, **arrays)
    with pytest.raises(ValueError, match="does not match"):
        data.load(path)
    monkeypatch.setattr(data, "SUBSET_SHA256", data.content_sha256(arrays))
    assert data.load(path)["forecast"].tolist() == [0.0, 1.0, 2.0, 3.0]


def test_content_hash_changes_with_any_value():
    arrays = {"forecast": np.zeros(3, dtype="f4")}
    changed = {"forecast": np.array([0, 0, 1e-3], dtype="f4")}
    assert data.content_sha256(arrays) != data.content_sha256(changed)


def test_load_checks_the_pin_it_is_given(tmp_path):
    path = tmp_path / "subset.npz"
    arrays = {"forecast": np.arange(4, dtype="f4")}
    np.savez(path, **arrays)
    with pytest.raises(ValueError, match="does not match"):
        data.load(path, data.SUBSET_SHA256)
    assert data.load(path, data.content_sha256(arrays))["forecast"].tolist() == [0.0, 1.0, 2.0, 3.0]


def test_fetch_writes_a_subset_only_on_its_pin_and_main_writes_each_one(tmp_path, monkeypatch):
    arrays = {"forecast": np.arange(4, dtype="f4")}
    monkeypatch.setattr(data, "build", lambda variable, lead_hours: arrays)
    path = tmp_path / "pinned.npz"
    monkeypatch.setattr(data, "SUBSETS", {("v", 24): (path, "0" * 64)})
    with pytest.raises(ValueError, match="no longer give the pinned pinned.npz"):
        data.fetch("v", 24)
    assert not path.exists()
    monkeypatch.setattr(data, "SUBSETS", {("v", 24): (path, data.content_sha256(arrays))})
    elsewhere = tmp_path / "elsewhere" / "x.npz"
    assert data.fetch("v", 24, elsewhere) == elsewhere and elsewhere.exists()
    assert not path.exists()
    monkeypatch.setattr("sys.argv", ["data", "--dir", str(tmp_path / "dir")])
    data.main()
    assert data.load(tmp_path / "dir" / "pinned.npz", data.content_sha256(arrays))
