"""The bundled items rebuild byte for byte from the pinned station files (skipped without
them)."""

import hashlib
import json

import pytest

from earthgym.heat import data, items

STATIONS = items.INDEXES + items.SITES
pytestmark = pytest.mark.skipif(
    not all((data.ROOT / f"{s}.csv.gz").exists() for s in STATIONS),
    reason="no pinned files; run uv run python -m earthgym.heat.data",
)


def test_the_bundled_items_rebuild_from_the_pinned_station_files():
    series = {s: data.read(data.fetch(s)) for s in STATIONS}  # fetch only checks the pins here
    manifest = json.loads(items.MANIFEST.read_text("utf-8"))
    text = "".join(json.dumps(items.make_item(spec, series)) + "\n" for spec in items.plan())
    assert hashlib.sha256(text.encode()).hexdigest() == manifest["sha256"]
    assert text == items.OUT.read_text("utf-8")
