"""Every published report and its JSON, re-rendered from the committed per-item results
alone, byte for byte (decision 0019)."""

import json
from pathlib import Path

import pytest
from climaqa_v1.taskset import near_matches
from era5_forecast_v1.taskset import records as era5_items
from heat_basis_v1.taskset import records as heat_items
from ibtracs_storm_v1.taskset import records as ibtracs_items

from earthgym import results, samples, spend
from earthgym.climaqa import compare
from earthgym.climaqa import report as climaqa_report
from earthgym.era5 import report as era5_report
from earthgym.grpo import pick
from earthgym.grpo import report as grpo_report
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
    ("ibtracs", "2026-11-02-claude-sonnet-5-5-tools-react", ibtracs_report, ibtracs_items),
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


def test_the_three_ibtracs_runs_re_render_from_the_results():
    names = [SINGLE[1][1], SINGLE[2][1], SINGLE[5][1]]  # rules shown, rules hidden, tools
    loaded = [load("ibtracs", n) for n in names]
    shown, hidden, tools = (ibtracs_report.from_results(*x, ibtracs_items()) for x in loaded)
    pairs = ibtracs_report.flips(loaded[1][1], loaded[2][1], ibtracs_items())
    also = (
        "react's system prompt and submit tool, which the prompt run did not have (decision 0023)"
    )
    text = ibtracs_report.render_tools(shown, hidden, tools, pairs, also)
    assert text == (R / "ibtracs/2026-11-02-rows-in-prompt-vs-tool-react.md").read_text("utf-8")


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
    assert rows == 16


def test_the_gemini_era5_probe_projects_the_tokens_decision_0010_gives():
    head, rows = load("era5", "2026-11-01-era5-probe")
    tokens = head["tokens"]["input"] + head["tokens"]["output"]
    assert (len(rows), tokens * 720 // len(rows)) == (10, 1_731_960)


GRPO = [  # name, title, window
    ("2026-11-02-smoke", "smoke run, 10 steps", 5),
    ("2026-11-02-run", "250 steps", 25),
]


@pytest.mark.parametrize(("name", "title", "window"), GRPO)
def test_each_grpo_report_re_renders_from_its_committed_metrics(name, title, window):
    metrics = json.loads((R / "grpo/results" / f"{name}-metrics.json").read_text("utf-8"))
    text = grpo_report.render(metrics, title, name[:10], window)
    assert text == (R / "grpo" / f"{name}.md").read_text("utf-8")


MODELS = ("qwen3.5-2b-q8_0", "granite-4.0-h-1b-q8_0")
SMALL = [  # each environment's small-model report and the results files it merges
    (
        "climaqa",
        [f"2026-11-02-{m}-8-samples-{kind}" for m in MODELS for kind in ("mcq", "cloze")],
    ),
    ("ibtracs", [f"2026-11-02-{m}-8-samples" for m in MODELS]),
    ("heat", [f"2026-11-02-{m}-8-samples" for m in MODELS]),
    (
        "era5",
        [
            "2026-11-02-qwen3.5-2b-q8_0-8-samples-a",
            "2026-11-02-qwen3.5-2b-q8_0-8-samples-b",  # stopped by a session's deadline
            "2026-11-02-granite-4.0-h-1b-q8_0-8-samples",
        ],
    ),
]


@pytest.mark.parametrize(("env", "names"), SMALL)
def test_each_small_model_report_re_renders_from_the_results(env, names, tmp_path, monkeypatch):
    for name in names:
        load(env, name)  # the bundled items, or their draw
    out = tmp_path / "report.md"
    files = [str(R / env / "results" / f"{name}.jsonl") for name in names]
    monkeypatch.setattr("sys.argv", ["samples", env, *files, "--out", str(out)])
    samples.main()
    assert out.read_text("utf-8") == (R / env / "2026-11-02-small-models.md").read_text("utf-8")


def test_the_grpo_pick_is_climaqa_mcq_on_all_five_tasks_of_the_committed_results():
    tasks = pick.finished()
    assert set(tasks) == {"climaqa mcq", "climaqa cloze", "ibtracs", "heat", "era5"}
    assert pick.pick(tasks) == "climaqa mcq"
    assert max(tasks, key=lambda t: tasks[t]["mean_variance"]) == "climaqa mcq"  # even uncapped
    over = {t for t, s in tasks.items() if s["median_tokens"] > pick.CAP}
    assert over == {"ibtracs", "heat", "era5"}


def test_the_heat_missing_value_counts_the_write_up_gives():
    items = {i["id"]: i for i in heat_items()}
    _, rows = load("heat", "2026-11-01-claude-sonnet-5-5-terms-only")
    name = "missing index days left out"
    decided = [
        r
        for r in rows
        if items[r["id"]]["question"] == "missed_days"
        and heat_report.careless(items[r["id"]])[name] != items[r["id"]]["key"]
    ]
    assert {(items[r["id"]]["index_name"], items[r["id"]]["year"]) for r in decided} == {
        ("Phoenix Deer Valley Municipal Airport", 2019)
    }
    missed = [r for r in decided if r["reward"] != 1.0]
    other = [r for r in missed if float(r["answer"]) == heat_report.careless(items[r["id"]])[name]]
    assert (len(decided), len(missed), len(other)) == (8, 7, 6)
