"""Every headline number in README.md comes from a committed report."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = " ".join((ROOT / "README.md").read_text("utf-8").split())
R = "reports"
ERA5, IBTRACS, HEAT = f"{R}/era5", f"{R}/ibtracs", f"{R}/heat"
SONNET = "2026-11-01-claude-sonnet-5-5.md"
HEADLINES = [  # as the README says it, the report, as the report says it
    ("0.118, the midpoint", f"{ERA5}/items_v1_baselines.md", "| midpoint | 648 | 0.1175 |"),
    ("| 0.128 |", f"{ERA5}/{SONNET}", "0.128"),
    ("| 0.029 |", f"{ERA5}/2026-11-02-small-models.md", "| 648 | 8 | 0.029 |"),
    ("| 0.042 |", f"{ERA5}/2026-11-02-small-models.md", "| 648 | 8 | 0.042 |"),
    (
        "all 18 of its published global RMSE, ACC and bias values",
        f"{ERA5}/2026-11-13-wb2-reproduction-leads-and-t2m.md",
        "All 18 published scores reproduce",
    ),
    (
        "0.05 to 0.35 per question",
        f"{IBTRACS}/{SONNET}",
        "| ace | best constant (0.5) | 100 | 0.050 |",
    ),
    ("0.05 to 0.35 per question", f"{IBTRACS}/{SONNET}", "best constant (1) | 100 | 0.350 |"),
    ("0.997", f"{IBTRACS}/2026-11-01-rules-shown-vs-hidden.md", "| all | 300 | 0.997 | 0.703 |"),
    ("0.703", f"{IBTRACS}/2026-11-01-rules-shown-vs-hidden.md", "| all | 300 | 0.997 | 0.703 |"),
    ("| 0.370 |", f"{IBTRACS}/2026-11-02-small-models.md", "| 300 | 8 | 0.370 |"),
    ("| 0.032 |", f"{IBTRACS}/2026-11-02-small-models.md", "| 300 | 8 | 0.032 |"),
    ("0.05 to 0.27 per question", f"{HEAT}/{SONNET}", "best constant (5) | 100 | 0.050 |"),
    ("0.05 to 0.27 per question", f"{HEAT}/{SONNET}", "best constant (0) | 100 | 0.270 |"),
    ("0.987", f"{HEAT}/2026-11-01-rules-shown-vs-terms-only.md", "0.987 | 0.960 |"),
    ("0.960", f"{HEAT}/2026-11-01-rules-shown-vs-terms-only.md", "0.987 | 0.960 |"),
    ("| 0.217 |", f"{HEAT}/2026-11-02-small-models.md", "| 300 | 8 | 0.217 |"),
    ("| 0.028 |", f"{HEAT}/2026-11-02-small-models.md", "| 300 | 8 | 0.028 |"),
    ("0.874 multiple choice", f"{R}/climaqa/runs/{SONNET}", "| 222 | 0.874 |"),
    ("0.508 cloze", f"{R}/climaqa/runs/{SONNET}", "| 128 | 0.508 |"),
    (
        "0.710 multiple choice",
        f"{R}/climaqa/2026-11-02-small-models.md",
        "| mcq | 222 | 8 | 0.710 |",
    ),
    ("0.145 cloze", f"{R}/climaqa/2026-11-02-small-models.md", "| cloze | 128 | 8 | 0.145 |"),
    (
        "0.584 multiple choice",
        f"{R}/climaqa/2026-11-02-small-models.md",
        "| mcq | 222 | 8 | 0.584 |",
    ),
    ("0.020 cloze", f"{R}/climaqa/2026-11-02-small-models.md", "| cloze | 128 | 8 | 0.020 |"),
    ("0.1277", f"{ERA5}/2026-11-01-claude-sonnet-5-5.json", '"reward": 0.1277'),
    ("0.1175", f"{ERA5}/items_v1_baselines.md", "| midpoint | 648 | 0.1175 |"),
    ("+0.0102 (SE 0.0085)", f"{ERA5}/{SONNET}", "+0.0102 (SE 0.0085)"),
    ("0.5555", f"{ERA5}/items_v1_baselines.md", "| IFS HRES | 648 | 0.5555 |"),
    ("133.890547 Pa", f"{ERA5}/2026-10-30-wb2-reproduction.md", "133.890547 Pa"),
    ("3.2e-8", f"{ERA5}/2026-10-30-wb2-reproduction.md", "3.2e-8"),
    ("258.6", f"{IBTRACS}/2026-11-01-ncei-reproduction.md", "258.6"),
    ("161.6", f"{IBTRACS}/2026-11-01-ncei-reproduction.md", "161.6"),
    ("55 days", f"{HEAT}/2026-11-01-nws-phoenix-reproduction.md", "| 55 | 55 |"),
    ("31-day", f"{HEAT}/2026-11-01-nws-phoenix-reproduction.md", "| 31, 30 Jun to 30 Jul |"),
    ("0.712 to 0.844", f"{R}/grpo/2026-11-13-resample.md", "| train | 52 | before | 0.712 |"),
    ("0.712 to 0.844", f"{R}/grpo/2026-11-13-resample.md", "| train | 52 | after | 0.844 |"),
    ("0.750 to 0.774", f"{R}/grpo/2026-11-13-resample.md", "| test | 52 | before | 0.750 |"),
    ("0.750 to 0.774", f"{R}/grpo/2026-11-13-resample.md", "| test | 52 | after | 0.774 |"),
    ("225 of 300", f"{R}/spend.md", "225 of 300"),
]


@pytest.mark.parametrize(("said", "report", "source"), HEADLINES)
def test_a_readme_number_is_in_its_report(said, report, source):
    assert said in README
    assert source in (ROOT / report).read_text("utf-8")


def test_the_readme_gives_the_climaqa_leak_as_the_findings_count_it():
    found = json.loads((ROOT / "reports/climaqa/findings.json").read_text("utf-8"))["findings"]
    same = [f for f in found if f["check"] == "leak.gold_in_silver"]
    assert (len(same), sum(f["detail"] == "answer text same" for f in same)) == (43, 29)
    assert sum(f["check"] == "leak.gold_in_other_silver_task" for f in found) == 6
    for said in (
        "43 validated Gold",
        "29 with the same answer",
        "14 with a different one",
        "6 more",
    ):
        assert said in README
