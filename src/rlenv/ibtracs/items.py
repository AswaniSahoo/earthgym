"""Per-storm question items for ibtracs-storm-v1 (decisions 0009 and 0011).

uv run python -m rlenv.ibtracs.items   # writes the bundled items and the manifest
"""

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

from rlenv.ibtracs import data, stats

COLUMNS = (*stats.COLUMNS, "NAME", "USA_PRES")
SEASONS = range(1980, 2026)  # 2026 is provisional; before 1980 many 3-hourly rows are blank
QUESTIONS = ("ace", "peak_category", "hurricane_hours")
SEED = 2026
N = 100  # storms per question
OUT = Path("environments/ibtracs_storm_v1/ibtracs_storm_v1/ibtracs_storm_v1.jsonl")
MANIFEST = Path("reports/ibtracs/items_v1_manifest.json")


def eligible(tracks: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Named storms of final seasons from 1980 on, every row a main-track row inside the North
    Atlantic basin with a wind and a status."""

    def keep(track: list[dict]) -> bool:
        return (
            int(track[0]["SEASON"]) in SEASONS
            and all(r["BASIN"] == "NA" and r["TRACK_TYPE"] == "main" for r in track)
            and all(r["USA_WIND"] and r["USA_STATUS"] for r in track)
            and stats.storm(track)["named"]
        )

    return {sid: track for sid, track in tracks.items() if keep(track)}


def keys(track: list[dict]) -> dict:
    """The exact answer to each question, by the rules in the prompt."""
    return {
        "ace": round(stats.storm(track)["ace"], 4),
        "peak_category": stats.category(track),
        "hurricane_hours": stats.hurricane_hours(track),
    }


def plan(tracks: dict[str, list[dict]], n: int = N, seed: int = SEED) -> list[tuple[str, str]]:
    """(question, SID) pairs, n per question, each storm used once: ACE first from all the named
    storms, so its draw is not thinned of hurricanes, then peak category and hours at hurricane
    strength from the storms left that reached it."""
    rng = random.Random(seed)
    named = sorted(tracks)
    rng.shuffle(named)
    chosen = [("ace", sid) for sid in named[:n]]
    left = {sid for sid in named[n:] if stats.storm(tracks[sid])["hurricane"]}
    hurricanes = sorted(left)
    rng.shuffle(hurricanes)
    chosen += [("peak_category", sid) for sid in hurricanes[:n]]
    chosen += [("hurricane_hours", sid) for sid in hurricanes[n : 2 * n]]
    if len(chosen) < 3 * n:
        raise ValueError(f"{len(chosen)} storms for {3 * n} items")
    return chosen


def make_item(sid: str, track: list[dict], question: str) -> dict:
    """One question about one storm: every row in archive order and the exact key. The name,
    year and SID are kept for provenance and never shown in the prompt."""
    rows = [
        [r["ISO_TIME"], r["USA_STATUS"], int(r["USA_WIND"])]
        + [int(r["USA_PRES"]) if r["USA_PRES"] else None]
        for r in track
    ]
    return {"id": f"{question}/{sid}", "sid": sid, "season": int(track[0]["SEASON"])} | {
        "name": track[0]["NAME"],
        "question": question,
        "rows": rows,
        "key": keys(track)[question],
    }


def write(items: list[dict], out: Path = OUT, manifest: Path = MANIFEST, **extra) -> None:
    text = "".join(json.dumps(item) + "\n" for item in items)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, "utf-8")
    counts = {q: sum(i["question"] == q for i in items) for q in QUESTIONS}
    record = {
        "file": out.name,
        "n": len(items),
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    record |= {"questions": {q: c for q, c in counts.items() if c}, "source_sha256": data.SHA256}
    manifest.write_text(json.dumps(record | extra, indent=1) + "\n", "utf-8")


def main() -> None:
    if hashlib.sha256(data.PATH.read_bytes()).hexdigest() != data.SHA256:
        raise SystemExit(f"{data.PATH} does not match the pinned sha256")
    tracks = defaultdict(list)
    for r in data.read(columns=COLUMNS):
        tracks[r["SID"]].append(r)
    storms = eligible(tracks)
    chosen = plan(storms)
    write([make_item(sid, storms[sid], q) for q, sid in chosen], seed=SEED, storms=len(storms))
    print(f"{len(chosen)} items from {len(storms)} eligible storms, written to {OUT}")


if __name__ == "__main__":
    main()
