import hashlib
import io
import urllib.error

import pytest

from rlenv.ibtracs import data

CSV = (
    "SID,SEASON,BASIN,NAME,ISO_TIME,USA_WIND\n"
    " ,Year, , , ,kts\n"
    "2024001N10300,2024,NA,ALPHA,2024-06-01 06:00:00,45\n"
    "2024001N10300,2024,NA,ALPHA,2024-06-01 09:00:00, \n"
)


class Body(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_for(payloads, calls):
    """An opener that serves each URL its payload, or raises 404 for a URL it lacks."""

    def opener(url, timeout):
        calls.append(url)
        if url not in payloads:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return Body(payloads[url])

    return opener


def test_fetch_takes_the_release_mirror_first_and_checks_its_sha256(tmp_path, monkeypatch):
    payload, calls = CSV.encode(), []
    monkeypatch.setattr(data, "SHA256", hashlib.sha256(payload).hexdigest())
    path = data.fetch(tmp_path / "na.csv", opener=opener_for({data.MIRROR: payload}, calls))
    assert path.read_bytes() == payload and calls == [data.MIRROR]
    data.fetch(path, opener=opener_for({}, calls))  # a good copy is not fetched again
    assert calls == [data.MIRROR]


def test_fetch_falls_back_to_ncei_when_the_mirror_is_out_of_reach(tmp_path, monkeypatch):
    payload, calls = CSV.encode(), []
    monkeypatch.setattr(data, "SHA256", hashlib.sha256(payload).hexdigest())
    path = data.fetch(tmp_path / "na.csv", opener=opener_for({data.URL: payload}, calls))
    assert path.read_bytes() == payload and calls == [data.MIRROR, data.URL]


def test_fetch_keeps_nothing_unless_a_source_serves_the_pinned_build(tmp_path, monkeypatch):
    payload, calls = CSV.encode(), []
    monkeypatch.setattr(data, "SHA256", "0" * 64)
    with pytest.raises(ValueError, match="no source serves the pinned build") as error:
        data.fetch(tmp_path / "na.csv", opener=opener_for({data.URL: payload}, calls))
    assert "404" in str(error.value) and hashlib.sha256(payload).hexdigest() in str(error.value)
    assert not (tmp_path / "na.csv").exists()


def test_read_skips_the_units_row_and_strips_single_space_blanks(tmp_path):
    path = tmp_path / "na.csv"
    path.write_text(CSV, encoding="utf-8")
    rows = data.read(path, columns=("SID", "ISO_TIME", "USA_WIND"))
    assert rows == [
        {"SID": "2024001N10300", "ISO_TIME": "2024-06-01 06:00:00", "USA_WIND": "45"},
        {"SID": "2024001N10300", "ISO_TIME": "2024-06-01 09:00:00", "USA_WIND": ""},
    ]
