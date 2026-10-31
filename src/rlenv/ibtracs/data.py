"""Pinned IBTrACS v04r01 North Atlantic CSV (Phase 4).

uv run python -m rlenv.ibtracs.data   # about 58 MB over anonymous HTTPS, writes data/ibtracs/

NCEI publishes no checksum and overwrites its files in place (docs/radar.md), so the pin is
our own sha256 of the build we fetched, and the copy under data/ is the one we keep. IBTrACS
terms: "full and open access", WMO Resolution 40 for commercial use. Cite Knapp, Kruk,
Levinson, Diamond and Neumann (2010), BAMS 91, doi:10.1175/2009BAMS2755.1, and Gahtan et al.
(2024), IBTrACS Version 4r01, NOAA NCEI, doi:10.25921/82ty-9e16 (docs/radar.md).
"""

import argparse
import csv
import hashlib
import urllib.request
from pathlib import Path

URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-"
    "ibtracs/v04r01/access/csv/ibtracs.NA.list.v04r01.csv"
)
PATH = Path("data/ibtracs/ibtracs.NA.list.v04r01.csv")
SHA256 = ""
SIZE, LAST_MODIFIED = 57_593_323, "Fri, 30 Oct 2026 04:27:28 GMT"  # HEAD, 2026-11-01


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fetch(path: Path = PATH, opener=urllib.request.urlopen) -> Path:
    """The pinned file: kept if the copy on disk matches, else downloaded and checked."""
    if path.exists() and _sha256(path.read_bytes()) == SHA256:
        return path
    with opener(URL, timeout=300) as response:
        raw = response.read()
    if (got := _sha256(raw)) != SHA256:
        raise ValueError(f"NCEI now serves another build: sha256 {got}, pinned {SHA256}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def read(path: Path = PATH, columns: tuple[str, ...] = ()) -> list[dict]:
    """Data rows as dicts of the named columns, with the units row skipped and every cell
    stripped, so a blank (a single space in IBTrACS) reads as ''."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        names = next(reader)
        next(reader)  # the units row
        index = [names.index(c) for c in columns]
        return [{c: row[i].strip() for c, i in zip(columns, index, strict=True)} for row in reader]


def main() -> None:
    argparse.ArgumentParser(description="Fetch the pinned IBTrACS NA CSV.").parse_args()
    print(f"kept {fetch()}")


if __name__ == "__main__":
    main()
