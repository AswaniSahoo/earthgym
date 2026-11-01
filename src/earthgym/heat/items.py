"""Heat policy items for heat-basis-v1 (decisions 0012 and 0013).

uv run python -m earthgym.heat.items   # writes the bundled items and the manifest
"""

import hashlib
import itertools
import json
import random
from pathlib import Path

from earthgym.heat import data, policy, stats

INDEXES = ["USW00003192", "USW00003184"]  # regional airports: the index stations
SITES = ["USW00023183", "USC00028499"]  # the urban core: the insured sites
NAMES = {
    "USW00003192": "Scottsdale Municipal Airport",
    "USW00003184": "Phoenix Deer Valley Municipal Airport",
    "USW00023183": "Phoenix Sky Harbor",
    "USC00028499": "Tempe ASU",
}
SEASONS = range(2015, 2025)
THRESHOLDS = range(100, 116)  # whole degrees F
KS = range(2, 6)  # consecutive trigger days an event needs
QUESTIONS = ("trigger_days", "events", "missed_days")
SEED = 2026
N = 100  # items per question
OUT = Path("environments/heat_basis_v1/heat_basis_v1/heat_basis_v1.jsonl")
MANIFEST = Path("reports/heat/items_v1_manifest.json")


def _spec(question: str, index: str, site: str, year: int, f: int, k: int | None) -> dict:
    return {
        "question": question,
        "index": index,
        "site": site,
        "year": year,
        "threshold": f,
        "k": k,
    }


def plan(n: int = N, seed: int = SEED) -> list[dict]:
    """n specs per question, drawn without repeats; for trigger days and events, which depend
    on the index alone, the site column shown beside it is drawn at random."""
    rng = random.Random(seed)
    grid = list(itertools.product(INDEXES, SEASONS, THRESHOLDS))
    specs = [
        _spec("trigger_days", i, rng.choice(SITES), y, f, None) for i, y, f in rng.sample(grid, n)
    ]
    grid = list(itertools.product(INDEXES, SEASONS, THRESHOLDS, KS))
    specs += [_spec("events", i, rng.choice(SITES), y, f, k) for i, y, f, k in rng.sample(grid, n)]
    grid = list(itertools.product(INDEXES, SITES, SEASONS, THRESHOLDS))
    return specs + [_spec("missed_days", i, s, y, f, None) for i, s, y, f in rng.sample(grid, n)]


def key(spec: dict, series: dict[str, dict[str, int]]) -> int:
    """The exact answer, by the rules in the prompt (`earthgym.heat.policy`)."""
    index, site, year, f = (
        series[spec["index"]],
        series[spec["site"]],
        spec["year"],
        spec["threshold"],
    )
    if spec["question"] == "trigger_days":
        return policy.trigger_days(index, year, f)
    if spec["question"] == "events":
        return policy.events(index, year, f, spec["k"])
    if spec["question"] == "missed_days":
        return policy.missed_days(index, site, year, f)
    raise ValueError(f"unknown question {spec['question']!r}")


def make_item(spec: dict, series: dict[str, dict[str, int]]) -> dict:
    """One question about one season: both stations' daily maxima in whole degrees F over the
    window (None where missing) and the exact key."""
    days = policy.window(spec["year"])
    parts = [
        spec["question"],
        spec["index"],
        spec["site"],
        str(spec["year"]),
        str(spec["threshold"]),
    ]
    parts += [] if spec["k"] is None else [str(spec["k"])]

    def whole(station: str) -> list[int | None]:
        values = series[station]
        return [stats.fahrenheit(values[d]) if d in values else None for d in days]

    return (
        {"id": "/".join(parts)}
        | spec
        | {
            "index_name": NAMES[spec["index"]],
            "site_name": NAMES[spec["site"]],
            "dates": [f"{d[4:6]}-{d[6:]}" for d in days],
            "index_f": whole(spec["index"]),
            "site_f": whole(spec["site"]),
            "key": key(spec, series),
        }
    )


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
    record |= {"questions": {q: c for q, c in counts.items() if c}}
    record |= {"stations": {s: data.STATIONS[s][0] for s in INDEXES + SITES}}
    manifest.write_text(json.dumps(record | extra, indent=1) + "\n", "utf-8")


def main() -> None:
    series = {s: data.read(data.fetch(s)) for s in INDEXES + SITES}
    days = [d for year in SEASONS for d in policy.window(year)]
    for station, values in series.items():  # whole degrees in the prompt give the keys' answers
        if any(stats.tenths(stats.fahrenheit(values[d])) != values[d] for d in days if d in values):
            raise SystemExit(f"{station}: a TMAX value is not the image of a whole degree F")
    specs = plan()
    write([make_item(spec, series) for spec in specs], seed=SEED)
    print(f"{len(specs)} items written to {OUT}")


if __name__ == "__main__":
    main()
