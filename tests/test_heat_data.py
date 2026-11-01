import gzip
import hashlib
import io

import pytest

from rlenv.heat import data

ROWS = (
    "USW00023183,20230719,TMAX,483,,,W,\n"  # 119 F
    "USW00023183,20230719,TMIN,294,,,W,\n"
    "USW00023183,20230720,TMAX,433,,,W,\n"  # 110 F
    "USW00023183,20230721,TMAX,450,,X,W,\n"  # a quality flag: dropped
)


class Body(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_for(payload, calls):
    def opener(url, timeout):
        calls.append(url)
        return Body(payload)

    return opener


def test_fetch_keeps_a_download_only_if_it_matches_the_pinned_sha256(tmp_path, monkeypatch):
    payload, calls = gzip.compress(ROWS.encode()), []
    monkeypatch.setitem(data.STATIONS, "X", ("0" * 64, len(payload), "today"))
    with pytest.raises(ValueError, match="sha256"):
        data.fetch("X", root=tmp_path, opener=opener_for(payload, calls))
    assert not (tmp_path / "X.csv.gz").exists()
    monkeypatch.setitem(data.STATIONS, "X", (hashlib.sha256(payload).hexdigest(), 0, "today"))
    path = data.fetch("X", root=tmp_path, opener=opener_for(payload, calls))
    assert path.read_bytes() == payload and calls[-1].endswith("/X.csv.gz")
    data.fetch("X", root=tmp_path, opener=opener_for(payload, calls))  # a good copy stays
    assert len(calls) == 2


def test_read_keeps_tmax_by_date_and_drops_quality_flagged_values(tmp_path):
    path = tmp_path / "s.csv.gz"
    path.write_bytes(gzip.compress(ROWS.encode()))
    assert data.read(path) == {"20230719": 483, "20230720": 433}
