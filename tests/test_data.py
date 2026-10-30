import hashlib
import io

import pytest

from rlenv.climaqa import data


def test_load_names_the_unnamed_index_column_id(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text(",Question,Answer\n0,Q?,A\n", encoding="utf-8")
    assert data.load(path) == [{"id": "0", "Question": "Q?", "Answer": "A"}]


def test_fetch_downloads_a_missing_file_and_keeps_it(tmp_path, monkeypatch):
    body = b",Question,Answer\n0,Q?,A\n"
    monkeypatch.setattr(
        data, "FILES", {("gold", "cloze"): ("g/c.csv", hashlib.sha256(body).hexdigest())}
    )
    monkeypatch.setattr(data.urllib.request, "urlopen", lambda url, timeout: io.BytesIO(body))
    paths = data.fetch(tmp_path)
    assert paths["gold", "cloze"].read_bytes() == body


def test_fetch_deletes_a_file_that_fails_its_pinned_hash(tmp_path):
    rel = data.FILES["gold", "mcq"][0]
    (tmp_path / rel).parent.mkdir(parents=True)
    (tmp_path / rel).write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="does not match pinned"):
        data.fetch(tmp_path)
    assert not (tmp_path / rel).exists()
