"""The bundled items rebuild byte for byte from the pinned CSV (skipped without it)."""

import hashlib
import json
from collections import defaultdict

import pytest

from earthgym.ibtracs import data, items

pytestmark = pytest.mark.skipif(
    not data.PATH.exists(), reason="no pinned file; run uv run python -m earthgym.ibtracs.data"
)


def test_the_bundled_items_rebuild_from_the_pinned_csv():
    assert hashlib.sha256(data.PATH.read_bytes()).hexdigest() == data.SHA256
    manifest = json.loads(items.MANIFEST.read_text("utf-8"))
    tracks = defaultdict(list)
    for r in data.read(columns=items.COLUMNS):
        tracks[r["SID"]].append(r)
    storms = items.eligible(tracks)
    chosen = items.plan(storms)
    text = "".join(json.dumps(items.make_item(sid, storms[sid], q)) + "\n" for q, sid in chosen)
    assert len(storms) == manifest["storms"]
    assert hashlib.sha256(text.encode()).hexdigest() == manifest["sha256"]
    assert text == items.OUT.read_text("utf-8")
