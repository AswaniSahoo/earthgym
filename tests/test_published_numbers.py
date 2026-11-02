"""Every published report and its JSON, re-rendered from the committed per-item results
alone, byte for byte (decision 0019)."""

import json
from pathlib import Path

import pytest
from climaqa_v1.taskset import near_matches
from era5_forecast_v1.taskset import records as era5_items
from heat_basis_v1.taskset import records as heat_items
from ibtracs_storm_v1.taskset import records as ibtracs_items

from earthgym import results, spend
from earthgym.climaqa import compare
from earthgym.climaqa import report as climaqa_report
from earthgym.era5 import report as era5_report
from earthgym.heat import report as heat_report
from earthgym.ibtracs import report as ibtracs_report

R = Path("reports")


def load(env, name):
    head, rows = results.read(R / env / "results" / f"{name}.jsonl")
    assert head["items_sha256"] in results.scored_on(env)  # the bundled items, or their draw
    return head, rows


SINGLE = [
    ("era5", "2026-11-01-claude-sonnet-5-5", era5_report, era5_items),
    ("ibtracs", "2026-11-01-claude-sonnet-5-5", ibtracs_report, ibtracs_items),
    ("ibtracs", "2026-11-01-claude-sonnet-5-5-rules-hidden", ibtracs_report, ibtracs_items),
    ("heat", "2026-11-01-claude-sonnet-5-5", heat_report, heat_items),
    ("heat", "2026-11-01-claude-sonnet-5-5-terms-only", heat_report, heat_items),
]
PAIRS = [
    ("ibtracs", SINGLE[1][1], SINGLE[2][1], "2026-11-01-rules-shown-vs-hidden", ibtracs_report),
    ("heat", SINGLE[3][1], SINGLE[4][1], "2026-11-01-rules-shown-vs-terms-only", heat_report),
]
ITEMS_OF = {"ibtracs": ibtracs_items, "heat": heat_items}
CLIMAQA = ["2026-10-30-gemini-3.8-flash", "2026-11-01-claude-sonnet-5-5"]


@pytest.mark.parametrize(("env", "name", "module", "items"), SINGLE)
def test_each_run_report_and_its_json_re_render_from_the_results(env, name, module, items):
    s = module.from_results(*load(env, name), items())
    assert module.render(s) == (R / env / f"{name}.md").read_text("utf-8")
    assert json.dumps(s, indent=1, default=str) == (R / env / f"{name}.json").read_text("utf-8")


@pytest.mark.parametrize(("env", "shown", "hidden", "pair", "module"), PAIRS)
def test_each_pair_report_re_renders_from_the_results(env, shown, hidden, pair, module):
    a, b = (module.from_results(*load(env, n), ITEMS_OF[env]()) for n in (shown, hidden))
    assert module.render_pair(a, b) == (R / env / f"{pair}.md").read_text("utf-8")


@pytest.mark.parametrize("name", CLIMAQA)
def test_each_climaqa_run_report_re_renders_from_the_results(name):
    runs = [load("climaqa", f"{name}-{kind}") for kind in ("cloze", "mcq")]
    summaries = [climaqa_report.from_results(*run) for run in runs]
    sha256 = json.loads((R / "climaqa/clean_v1_manifest.json").read_text("utf-8"))["sha256"]
    notes = sorted(p.name for p in (R / "climaqa/runs").glob(f"{name}-*misses.md"))
    text = climaqa_report.render(summaries, sha256, notes, runs[0][0]["log_dir"])
    assert text == (R / "climaqa/runs" / f"{name}.md").read_text("utf-8")
    dumped = json.dumps(summaries, indent=1, default=str)
    assert dumped == (R / "climaqa/runs" / f"{name}.json").read_text("utf-8")


def test_the_climaqa_comparison_re_renders_from_the_results():
    a, b = ({k: load("climaqa", f"{n}-{k}") for k in ("cloze", "mcq")} for n in CLIMAQA)
    rows = [compare.compare(a[k], b[k]) for k in ("cloze", "mcq")]
    strict = [compare.compare(a[k], b[k], exclude=near_matches()) for k in ("cloze", "mcq")]
    levels = {a[k][0]["task"]: compare.by_level(a[k], b[k]) for k in ("cloze", "mcq")}
    dirs = (a["mcq"][0]["log_dir"], b["mcq"][0]["log_dir"])
    out = R / "climaqa/2026-11-01-sonnet-vs-gemini"
    assert compare.render(rows, levels, dirs, strict) == out.with_suffix(".md").read_text("utf-8")
    record = json.dumps({"rows": rows, "strict": strict, "levels": levels}, indent=1, default=str)
    assert record == out.with_suffix(".json").read_text("utf-8")


def test_every_ledger_row_has_the_tokens_of_its_committed_results():
    heads = [results.read(p)[0] for p in sorted(R.glob("*/results/*.jsonl"))]
    rows = 0
    for line in spend.LEDGER.read_text("utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| run "):
            continue
        cells = [c.strip() for c in line.strip("| ").split(" | ")]
        found = [h for h in heads if h["log_dir"] == cells[2]]  # ClimaQA: one file per task
        assert found, cells[0]
        assert [sum(h["tokens"][k] for h in found) for k in spend.KINDS] == [
            int(c) for c in cells[4:9]
        ], cells[0]
        rows += 1
    assert rows == 13


def test_the_gemini_era5_probe_projects_the_tokens_decision_0010_gives():
    head, rows = load("era5", "2026-11-01-era5-probe")
    tokens = head["tokens"]["input"] + head["tokens"]["output"]
    assert (len(rows), tokens * 720 // len(rows)) == (10, 1_731_960)
