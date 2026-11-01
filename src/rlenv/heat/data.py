"""Pinned GHCN-Daily station files (Phase 5, decision 0012).

uv run python -m rlenv.heat.data   # about 1.5 MB a station over anonymous HTTPS, to data/heat/

NCEI publishes no checksum and rewrites the by_station files daily, so each pin is our own
sha256 of the copy we fetched, with its size and Last-Modified, and that copy under data/ is
the one we keep; a newer build fails the pin. NOAA names no licence; cite GHCN-Daily,
doi:10.7289/V5D21VHZ (docs/radar.md).
"""

import argparse
import csv
import gzip
import hashlib
import io
import urllib.request
from pathlib import Path

URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{station}.csv.gz"
ROOT = Path("data/heat")
STATIONS = {  # station: (sha256, size, Last-Modified), each fetched 2026-11-01
    "USW00023183": (  # Phoenix Sky Harbor
        "8c0de135bbafa0d0264069ddacf8d5acfed61cd9bef3af0aa7ef27f78b077eed",
        1_479_584,
        "Sun, 01 Nov 2026 00:01:02 GMT",
    ),
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fetch(station: str = "USW00023183", root: Path = ROOT, opener=urllib.request.urlopen) -> Path:
    """The pinned file: kept if the copy on disk matches, else downloaded and checked."""
    pinned = STATIONS[station][0]
    path = root / f"{station}.csv.gz"
    if path.exists() and _sha256(path.read_bytes()) == pinned:
        return path
    with opener(URL.format(station=station), timeout=300) as response:
        raw = response.read()
    if (got := _sha256(raw)) != pinned:
        raise ValueError(f"NCEI now serves another build of {station}: sha256 {got}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def read(path: Path) -> dict[str, int]:
    """TMAX by date (YYYYMMDD) in tenths of a degree C, without quality-flagged values. Rows:
    ID, date, element, value, measurement flag, quality flag, source flag, time."""
    text = gzip.decompress(path.read_bytes()).decode("utf-8")
    return {
        row[1]: int(row[3])
        for row in csv.reader(io.StringIO(text))
        if row[2] == "TMAX" and not row[5].strip()
    }


def main() -> None:
    argparse.ArgumentParser(description="Fetch the pinned GHCN-Daily station files.").parse_args()
    for station in STATIONS:
        print(f"kept {fetch(station)}")


if __name__ == "__main__":
    main()
