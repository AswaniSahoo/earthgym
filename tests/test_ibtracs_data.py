import hashlib
import io

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


def opener_for(payload, calls):
    def opener(url, timeout):
        calls.append(url)
        return Body(payload)

    return opener


def test_fetch_keeps_a_download_only_if_it_matches_the_pinned_sha256(tmp_path, monkeypatch):
    payload, calls = CSV.encode(), []
    path = tmp_path / "na.csv"
    monkeypatch.setattr(data, "SHA256", "0" * 64)
    with pytest.raises(ValueError, match="sha256"):
        data.fetch(path, opener=opener_for(payload, calls))
    assert not path.exists()
    monkeypatch.setattr(data, "SHA256", hashlib.sha256(payload).hexdigest())
    assert data.fetch(path, opener=opener_for(payload, calls)).read_bytes() == payload
    data.fetch(path, opener=opener_for(payload, calls))  # a good copy is not fetched again
    assert len(calls) == 2


def test_read_skips_the_units_row_and_strips_single_space_blanks(tmp_path):
    path = tmp_path / "na.csv"
    path.write_text(CSV, encoding="utf-8")
    rows = data.read(path, columns=("SID", "ISO_TIME", "USA_WIND"))
    assert rows == [
        {"SID": "2024001N10300", "ISO_TIME": "2024-06-01 06:00:00", "USA_WIND": "45"},
        {"SID": "2024001N10300", "ISO_TIME": "2024-06-01 09:00:00", "USA_WIND": ""},
    ]
