"""Jev as a third reader of the ClimaQA miss sort (decision 0008).

uv run python -m earthgym.climaqa.third_reader run      # stops before $0.10; run again to resume
uv run python -m earthgym.climaqa.third_reader results  # the log's calls, compact, for git (0019)
uv run python -m earthgym.climaqa.third_reader report   # from the results file and the two sorts

The provider is TypeSafe direct or the Experiential Labs gateway (decision 0008, amendment
2026-11-19): the one JEV_BASE_URL names, and when it is unset TypeSafe direct if TYPESAFE_API_KEY
is set, else the gateway if JEV_API_KEY is set. Each provider reads only its own key, and the
gateway's JEV_API_KEY only from where its JEV_BASE_URL came from, the repo-root .env for the
fallback (jev.provider, jev.load_key). A run holds a lock file next to the log, so a second launch
fails while it goes, and each record holds the commit and whether the tree had uncommitted changes
when it started.
"""

import argparse
import contextlib
import csv
import hashlib
import itertools
import json
import math
import os
import statistics
import subprocess
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from earthgym import results
from earthgym.climaqa import expert_sheet, jev

RUNS = 5  # identical calls per item, for stability
AT = "%Y-%m-%dT%H:%M:%SZ"  # UTC to the second, as each record's `at` and the header's times
LOG = Path("logs/2026-10-31-jev/responses.jsonl")  # raw responses, not in git
RESULTS = Path("reports/climaqa/results/2026-10-31-jev-third-reader.jsonl")  # per call, in git
# The 2026-10-31 study's records predate the commit and dirty fields. From git reflog, HEAD stayed
# at 2ed5f18 throughout the run, and the tree held the gateway amendment, not yet committed.
STUDY_REVISION = ("2ed5f18", True)
# prompt_sha256 of INSTRUCTIONS and BUCKETS at 2ed5f18 (git show 2ed5f18:src/earthgym/climaqa/
# jev.py, read 2026-11-19), the prompt the study sent; the gateway amendment left both alone.
STUDY_PROMPT_SHA256 = "786f7d55f63e44c22435de4ee95e9359b7f073400f850e36330bf54c4982c4a4"
PROMPT_FILE = "src/earthgym/climaqa/jev.py"  # where INSTRUCTIONS and BUCKETS live
REVIEW = Path("docs/reviews/phase-2-climaqa-port.md")
REPORT = Path("reports/climaqa/runs/2026-10-31-jev-third-reader.md")
REQUIRED = ("id", "pass", "run", "provider", "retries")  # what a resumed run reads of a record
LABELS = {  # the miss notes' bucket names, as the item-level options Jev chooses from
    "mcq": {
        "model error": "key_right",
        "ambiguous": "ambiguous",
        "flawed": "flawed_item",
        "source only": "source_only",
    },
    "cloze": {
        "strictness": "same_answer",
        "other": "other_correct_word",
        "model error": "wrong_reply",
    },
}


def state(row: dict) -> dict:
    """The item and the model's answer as Jev sees them: no notes, flags or labels."""
    if row["task"] == "mcq":
        options = dict(line.split(") ", 1) for line in row["options"].splitlines())
        key, answer = row["key"][0], row["model_answer"][0]
        return {"question": row["question"], "options": options, "key": key, "model_answer": answer}
    return {"sentence": row["question"], "key": row["key"], "reply": row["model_answer"]}


def rotations(task: str) -> list[list[str]]:
    """The fixed option order and its cyclic rotations: each option is listed first once."""
    names = list(jev.BUCKETS[task])
    return [names[r:] + names[:r] for r in range(len(names))]


def schedule(rows: list[dict], runs: int = RUNS):
    """Each call in order: per item, `runs` identical calls in the fixed order, then one call per
    other rotation of the options (the first fixed call stands for rotation 0)."""
    for row in rows:
        orders = rotations(row["task"])
        yield from ((row, "fixed", k, orders[0]) for k in range(1, runs + 1))
        yield from ((row, "rotated", r, orders[r]) for r in range(1, len(orders)))


def compact(record: dict) -> dict:
    """One logged call as the results file keeps it (decision 0019): only what the report reads,
    so no reply text, prompt, request body, request id or anything of the key."""
    row = {name: record[name] for name in ("id", "task", "pass", "run")}
    if "error" in record:  # a failed call: what the spend line reads
        kept = ("error", "retries", "estimate", "provider", "model_requested", "at")
        return row | {name: record[name] for name in kept}
    reply = record["response"]
    bucket, usage = reply["answers"]["bucket"], reply["usage"]
    row |= {"order": record["order"], "choice": bucket["choice"]}
    row |= {"probabilities": bucket["probabilities"], "retries": record["retries"]}
    row |= {"input_tokens": jev.count(usage["input_tokens"])}  # 53.0 kept as 53
    row |= {"output_tokens": jev.count(usage.get("output_tokens", 0)), "seconds": record["seconds"]}
    row |= {"provider": record["provider"], "model_requested": record["model_requested"]}
    row |= {"reply_model": reply["model"], "reply_provider": reply.get("provider")}
    return row | {"at": record["at"]}


def sheet() -> list[dict]:
    """The expert sheet's rows: the items, each as a run reads it."""
    with expert_sheet.SHEET.open(encoding="utf-8") as rows:
        return list(csv.DictReader(rows))


def _canonical(value) -> bytes:
    """Canonical JSON: sorted keys, no spaces, UTF-8."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def items_sha256(rows: list[dict]) -> str:
    """The items' revision: the sha256 of what each request sends of them (`state`), in id order,
    as canonical JSON, so a column no request sends, such as the expert's, leaves it alone."""
    sent = [state(row) for row in sorted(rows, key=lambda row: row["id"])]
    return hashlib.sha256(_canonical(sent)).hexdigest()


def prompt_sha256() -> str:
    """The prompt's revision: the sha256 of INSTRUCTIONS and BUCKETS as canonical JSON, each task's
    buckets as [name, text] pairs, as their order is the fixed option order."""
    pairs = {task: [[name, text] for name, text in b.items()] for task, b in jev.BUCKETS.items()}
    return hashlib.sha256(
        _canonical({"instructions": jev.INSTRUCTIONS, "buckets": pairs})
    ).hexdigest()


def git_revision(runner=subprocess.run) -> tuple[str, bool | str]:
    """The checkout's short HEAD, and whether `git status --porcelain` lists anything, as a run
    starts; "unknown" for both when git cannot say."""
    root = jev.repo_root(Path(__file__).resolve())
    commands = (["rev-parse", "--short", "HEAD"], ["status", "--porcelain"])
    try:
        head, status = (
            runner(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout
            for args in commands
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown", "unknown"
    return head.strip(), bool(status.strip())


def progress(records: list[dict], rows: list[dict]) -> tuple[int, int]:
    """How many of the calls `schedule` plans for `rows` have an answered record, and how many it
    plans."""
    planned = {(row["id"], kind, k) for row, kind, k, _ in schedule(rows)}
    answered = {(r["id"], r["pass"], r["run"]) for r in records if "error" not in r}
    return len(planned & answered), len(planned)


def outcome(records: list[dict], rows: list[dict]) -> str:
    """What a run left in the log: every planned call answered, or how far it got."""
    answered, planned = progress(records, rows)
    if answered == planned:
        return f"all {planned} planned calls answered, logged to {LOG}"
    return (
        f"the run stopped early: {answered} of {planned} planned calls answered, logged to {LOG};"
        " run it again to resume"
    )


def header(records: list[dict]) -> dict:
    """The run, as the first line of its results file (decision 0019). started is when the first
    call started and completed when the last one ended, its `at` plus its `seconds`, both to the
    second (null for an empty log); the commit is what the records hold (the study's from
    STUDY_REVISION); a Jev request takes no generate settings; items_sha256 is `items_sha256` of
    the sheet's rows for the items called; the token totals are the sums of the rows'; planned,
    answered and complete say whether every call `schedule` plans for the sheet was answered."""
    ids, rows = {r["id"] for r in records}, sheet()
    items = [row for row in rows if row["id"] in ids]
    answered, planned = progress(records, rows)
    if missing := ids - {row["id"] for row in items}:
        raise ValueError(f"the expert sheet has no row for {sorted(missing)}")
    revisions = {(r["commit"], r["dirty"]) if "commit" in r else STUDY_REVISION for r in records}
    calls = [compact(r) for r in records if "error" not in r]
    started = completed = None
    if records:  # a failed call logs no seconds: its end is taken as its start
        last = max(records, key=lambda r: (r["at"], r.get("seconds", 0)))
        ended = datetime.strptime(last["at"], AT) + timedelta(seconds=last.get("seconds", 0))
        started, completed = min(r["at"] for r in records), ended.strftime(AT)
    models = sorted({f"{r['provider']}/{r['model_requested']}" for r in records})
    commits = sorted(f"{c} (dirty)" if d is True else c for c, d in revisions)
    return {
        "task": "climaqa_third_reader",
        "task_args": {"runs": RUNS},
        "model": ", ".join(models) or None,
        "items_sha256": items_sha256(items),
        "started": started,
        "completed": completed,
        "commit": ", ".join(commits) or None,
        "settings": {},
        "tokens": {k: sum(r[f"{k}_tokens"] for r in calls) for k in ("input", "output")},
        "planned": planned,
        "answered": answered,
        "complete": answered == planned,
        "log": LOG.name,
        "log_dir": str(LOG.parent),
    }


def charged(row: dict) -> float:
    """The input tokens a call counts against the cap, every try of it: at the usage its reply
    reports when it was answered, at its estimate when it failed. It reads a results row; a log
    record goes through `compact` first, so the budget and the report count alike."""
    tokens = row["estimate"] if "error" in row else row["input_tokens"]
    return tokens * (1 + row["retries"])


def load(path: Path) -> list[dict]:
    """The records of a log. A blank or torn line, or a record without what resuming and
    charging read, stops with the file and the line number."""
    records = []
    for number, line in enumerate(path.read_text("utf-8").splitlines(), start=1):
        where = f"{path}:{number}"
        if not line.strip():
            raise ValueError(f"{where}: a blank line")
        try:
            record = json.loads(line)
        except ValueError:
            raise ValueError(f"{where}: a torn line, not one JSON record") from None
        if not isinstance(record, dict):
            raise ValueError(f"{where}: not a JSON object")
        if missing := [name for name in REQUIRED if name not in record]:
            raise ValueError(f"{where}: the record has no {', '.join(missing)}")
        try:
            countable = record["retries"] >= 0 and charged(compact(record)) >= 0
        except KeyError as missing:
            raise ValueError(f"{where}: the record has no {missing.args[0]}") from None
        except TypeError:
            countable = False
        if not countable:
            raise ValueError(f"{where}: the record has no count of retries and tokens to charge")
        records.append(record)
    return records


@contextlib.contextmanager
def locked(out: Path):
    """An exclusive lock file next to the log, `<out>.lock`, made with O_EXCL so that a second
    launch fails while a run goes, and removed when the run ends, however it ends."""
    lock = out.with_name(out.name + ".lock")
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        raise RuntimeError(
            f"{lock} exists, so another run may be writing {out}; delete it only if no run is "
            "active"
        ) from None
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def run(
    rows: list[dict],
    key: str,
    out: Path = LOG,
    opener=jev.OPEN,
    budget: jev.Budget | None = None,
    runs: int = RUNS,
    provider: dict | None = None,
    sleep=time.sleep,
    clock=time.monotonic,
    wall=time.time,
) -> list[dict]:
    """The calls of `schedule`, through `provider` (default TypeSafe direct), each starting at
    least its min_interval_s after the one before on the monotonic `clock`; its record holds the
    UTC `wall` time it started. Each call is appended to `out` as it ends: an answered one with
    its raw response, a failed one with its error, which is then raised. `<out>.lock` refuses a
    second launch while a run goes.

    A new launch skips the calls `out` holds as answered and sends the failed ones again, so a
    failed call can be paid for more than once. The budget charges every try in `out` and every
    new one (see `charged`), and a call starts only if all its provider's tries at its own estimate
    fit what is left of it: four on TypeSafe direct, one through the gateway, which is never tried
    again. A log made through another provider is refused."""
    budget = budget or jev.Budget()
    chosen = provider or jev.PROVIDERS[jev.TYPESAFE]
    out.parent.mkdir(parents=True, exist_ok=True)
    with locked(out):
        records = load(out) if out.exists() else []
        others = sorted({r["provider"] for r in records} - {chosen["name"]})
        if others:
            raise ValueError(f"{out} holds calls through {others}; resume through that provider")
        for r in records:
            budget.charge(charged(compact(r)))
        done = {(r["id"], r["pass"], r["run"]) for r in records if "error" not in r}
        next_start, (commit, dirty) = -math.inf, git_revision()
        with out.open("a", encoding="utf-8") as log:
            for row, kind, k, order in schedule(rows, runs):
                if (row["id"], kind, k) in done:
                    continue
                body = jev.request(row["task"], state(row), order, chosen["model"])
                estimate = jev.estimate(body)
                if not budget.allows(estimate * chosen["tries"]):
                    return records
                wait = next_start - clock()
                if wait > 0:
                    sleep(wait)
                next_start = clock() + chosen["min_interval_s"]
                record = {"id": row["id"], "task": row["task"], "pass": kind, "run": k}
                record |= {"provider": chosen["name"], "model_requested": chosen["model"]}
                record |= {"at": time.strftime(AT, time.gmtime(wall()))}
                record |= {"commit": commit, "dirty": dirty, "order": order}
                failure = None
                try:
                    payload, seconds, retries, request_id = jev.call(
                        body,
                        key,
                        chosen["url"],
                        opener=opener,
                        sleep=sleep,
                        id_header=chosen["request_id_header"],
                        tries=chosen["tries"],
                    )
                    record |= {"seconds": seconds, "retries": retries, "request_id": request_id}
                    record |= {"response": payload}
                except jev.CallError as failed:
                    failure = failed
                    record |= {"retries": failed.retries, "request_id": failed.request_id}
                    record |= {"error": failed.error, "status": failed.status}
                    record |= {"estimate": estimate, "body": failed.body}
                budget.charge(charged(compact(record)))
                records.append(record)
                log.write(json.dumps(record) + "\n")
                log.flush()
                if failure is not None:
                    raise failure
    return records


def _primary(bucket: str) -> str:
    return bucket.split(":")[0].split(",")[0].strip()


def mine() -> dict[str, str]:
    """The first sort's bucket for each miss, from the two miss notes."""
    out = {}
    for task, path in expert_sheet.NOTES.items():
        for item, _, bucket, _ in expert_sheet.note_rows(path.read_text("utf-8"), task):
            out[item] = LABELS[task][_primary(bucket)]
    return out


def blind_sort(review: Path = REVIEW) -> dict[str, str]:
    """The reviewer's blind sort of the 33 cloze misses, from the baseline review, section 3."""
    section = review.read_text("utf-8").split("### 3. Blind sort against the author's sort")[1]
    out = {}
    for line in section.split("\n### ")[0].splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split(" | ")]
        if len(cells) == 6 and cells[0].isdigit():
            out[f"gold/cloze/{cells[0]}"] = LABELS["cloze"][_primary(cells[4])]
    return out


def kappa(a: list[str], b: list[str]) -> float:
    """Cohen's kappa between two raters' labels for the same items."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    count_a, count_b = Counter(a), Counter(b)
    chance = sum(count_a[label] * count_b[label] for label in set(a) | set(b)) / n**2
    return 1.0 if chance == 1 else (observed - chance) / (1 - chance)


def brier(probabilities: dict[str, float], label: str) -> float:
    """Multi-class Brier score of one probability spread against the reference label."""
    return float(sum((p - (option == label)) ** 2 for option, p in probabilities.items()))


def stability(choices: list[str]) -> dict:
    """The modal choice over repeated calls, whether all agree, and pairwise agreement (1 when
    there is a single call)."""
    pairs = list(itertools.combinations(choices, 2))
    return {
        "modal": Counter(choices).most_common(1)[0][0],
        "all_same": len(set(choices)) == 1,
        "agreement": sum(x == y for x, y in pairs) / len(pairs) if pairs else 1.0,
    }


def _modal(choices: list[str], spreads: list[dict]) -> str:
    """The most frequent choice; a tie goes to the higher mean probability."""
    counts = Counter(choices)
    return max(counts, key=lambda o: (counts[o], sum(s.get(o, 0.0) for s in spreads)))


def _covers(recs: list[dict]) -> bool:
    """Whether an item's rotation set lists each option first once: the fixed order's first call
    and one call per other rotation, all answered."""
    return sorted(r["order"][0] for r in recs) == sorted(recs[0]["order"])


def _first_position(sets: dict[str, list[dict]]) -> dict:
    """How often Jev picks whichever option is listed first, and how much probability an
    option gains from being listed first, over each item's rotation set."""
    hits = calls = 0
    expected, gains = 0.0, []
    for recs in sets.values():
        led = [(r["order"][0], r) for r in recs]
        hits += sum(answer["choice"] == lead for lead, answer in led)
        calls += len(recs)
        expected += len(recs) / len(recs[0]["order"])
        for option in recs[0]["order"]:
            first = [a["probabilities"][option] for lead, a in led if lead == option]
            rest = [a["probabilities"][option] for lead, a in led if lead != option]
            gains.append(statistics.mean(first) - statistics.mean(rest))
    if not calls:
        return {"first_hits": 0, "rotation_calls": 0, "first_expected": None, "first_gain": None}
    return {
        "first_hits": hits,
        "rotation_calls": calls,
        "first_expected": expected / calls,
        "first_gain": statistics.mean(gains),
    }


def analyse(
    records: list[dict],
    mine_labels: dict,
    blind_labels: dict,
    usd_per_input_token: float = jev.USD_PER_INPUT_TOKEN,
) -> dict:
    """Agreement, calibration and stability from the answered fixed-order calls; first-position
    bias and rotation-averaged agreement from the rotated orders; latency from every answered
    call. Failed calls are left out of all of that; the spend counts every try of every logged
    call, answered or failed (see `charged`). It reads results rows (see `compact`), whether they
    come from a log or from the committed results file, so one code path serves both (0019)."""
    logged, records = records, [r for r in records if "error" not in r]
    fixed = [r for r in records if r.get("pass", "fixed") == "fixed"]
    by_item: dict[str, list[dict]] = {}
    for r in fixed:
        by_item.setdefault(r["id"], []).append(r)
    modal = {
        i: _modal([a["choice"] for a in answers], [a["probabilities"] for a in answers])
        for i, answers in by_item.items()
    }
    rotated_ids = {r["id"] for r in records if r.get("pass") == "rotated"}
    sets = {
        i: [r for r in records if r["id"] == i and (r.get("pass") == "rotated" or r["run"] == 1)]
        for i in rotated_ids
    }
    # a set a partial run left without each option listed first once measures no order effect
    whole = {i: recs for i, recs in sets.items() if _covers(recs)}
    incomplete, sets = len(sets) - len(whole), whole
    rotated_modal = {}
    for i, recs in sets.items():
        spreads = [r["probabilities"] for r in recs]
        options = recs[0]["order"]
        rotated_modal[i] = max(
            sorted(options, key=list(jev.BUCKETS[recs[0]["task"]]).index),
            key=lambda o: statistics.mean(s[o] for s in spreads),
        )

    def against(reference: dict, labels: dict) -> tuple[float | None, int]:
        shared = [i for i in reference if i in labels]
        if not shared:
            return None, 0
        return kappa([labels[i] for i in shared], [reference[i] for i in shared]), len(shared)

    both = [i for i in blind_labels if mine_labels.get(i) == blind_labels[i] and i in by_item]
    briers = [
        sum(brier(a["probabilities"], blind_labels[i]) for a in by_item[i]) / len(by_item[i])
        for i in both
    ]
    stable = [stability([a["choice"] for a in answers]) for answers in by_item.values()]
    seconds = [r["seconds"] for r in records]
    tokens = sum(charged(r) for r in logged)
    out = {
        "modal": modal,
        "items": len(by_item),
        "runs": max(map(len, by_item.values()), default=0),
    }
    out |= {"called_items": len({r["id"] for r in logged})}
    for name, reference, labels in [
        ("mine", mine_labels, modal),
        ("blind", blind_labels, modal),
        ("mine_blind", blind_labels, mine_labels),
        ("mine_rotated", mine_labels, rotated_modal),
        ("blind_rotated", blind_labels, rotated_modal),
    ]:
        out |= dict(zip((f"kappa_{name}", f"n_{name}"), against(reference, labels), strict=True))
    out |= {"rotated_modal": rotated_modal, "incomplete_sets": incomplete} | _first_position(sets)
    out |= {"brier": sum(briers) / len(briers) if briers else None, "brier_items": len(briers)}
    out |= {"all_same": sum(s["all_same"] for s in stable)}
    out |= {"agreement": sum(s["agreement"] for s in stable) / len(stable) if stable else None}
    out |= {"calls": len(records), "failed": len(logged) - len(records)}
    out |= {"tries": sum(1 + r["retries"] for r in logged)}
    out |= {"retries": sum(r["retries"] for r in logged)}
    out |= {"input_tokens": tokens, "usd": tokens * usd_per_input_token}
    out |= {"median_seconds": statistics.median(seconds) if seconds else None}
    p90 = statistics.quantiles(seconds, n=10, method="inclusive")[-1] if len(seconds) > 1 else None
    out |= {"p90_seconds": p90}  # quantiles need two calls or more
    out |= {"models": sorted({r["reply_model"] for r in records})}
    out |= {"providers": sorted({r["provider"] for r in logged})}
    out |= {"requested": sorted({r["model_requested"] for r in logged})}
    relayed = {r["reply_provider"] for r in records if r["reply_provider"] is not None}
    out |= {"reply_providers": sorted(relayed), "dates": sorted({r["at"][:10] for r in logged})}
    out |= {"others": dict(Counter(modal[i] for i in modal if i not in mine_labels))}
    return out


def _f(value: float | None, places: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{places}f}"


def render(a: dict, head: dict, source: Path) -> str:
    """The report from the analysis, the results file's first line and that file's path, ending
    with the config and the source of each part."""
    brier_line = (
        f"Brier score where both sorts agree: {a['brier']:.3f} over {a['brier_items']} items "
        "(0 is perfect; 2 is a sure wrong answer)."
        if a["brier"] is not None
        else "Brier score: no item where both sorts agree."
    )
    if a["rotation_calls"]:
        share = a["first_hits"] / a["rotation_calls"]
        bias_line = (
            f"First-position bias: Jev chose the first-listed option in {a['first_hits']} of "
            f"{a['rotation_calls']} rotated-order calls ({share:.3f}; {a['first_expected']:.3f} "
            "if order did not matter); being listed first adds "
            f"{a['first_gain']:+.3f} to an option's probability on average."
        )
    else:
        bias_line = "First-position bias: no rotated-order calls."
    rows = [
        ("Jev against the first sort", "mine"),
        ("Jev against the reviewer's blind sort", "blind"),
        ("Jev, rotation-averaged, against the first sort", "mine_rotated"),
        ("Jev, rotation-averaged, against the reviewer's blind sort", "blind_rotated"),
        ("first sort against the reviewer's blind sort", "mine_blind"),
    ]
    relayed = f" and provider {', '.join(a['reply_providers'])}" if a["reply_providers"] else ""
    prompt = "unchanged" if prompt_sha256() == STUDY_PROMPT_SHA256 else "changed"
    partial = (
        []
        if head["complete"]
        else [
            f"This run is partial: {head['answered']} of {head['planned']} planned calls "
            "answered, so the numbers below cover only those calls; "
            f"{a['incomplete_sets']} incomplete rotation sets are left out of the rotation "
            "measures.",
            "",
        ]
    )
    spend = (
        f"Spend against the cap: answered calls {a['calls']}, failed calls {a['failed']}, tries "
        f"{a['tries']} (retries {a['retries']}), input tokens {a['input_tokens']}, "
        f"${a['usd']:.4f} at TypeSafe's list price (output tokens are free). Each try is charged: "
        "at the input tokens its call reports when the call was answered, and at one token per "
        f"{float(jev.CHARS_PER_TOKEN):g} characters of the request when it failed."
    )
    sources = [
        "Config and sources:",
        "",
        f"- Items: the fields each request sends of the {a['called_items']} items in "
        f"{expert_sheet.SHEET}, sha256 {head['items_sha256']} of their canonical JSON in id order.",
        f"- Prompt: INSTRUCTIONS and BUCKETS in {PROMPT_FILE}, {prompt} since {STUDY_REVISION[0]}"
        f" (sha256 {prompt_sha256()} of their canonical JSON). The requests set no seed and no "
        "sampling setting.",
        f"- Calls: {source}, which this report is rendered from.",
        f"- First sort: {' and '.join(str(path) for path in expert_sheet.NOTES.values())}.",
        f"- Reviewer's blind sort: {REVIEW}, section 3.",
    ]
    if not a["calls"]:
        nothing = (
            f"No call was answered: {head['answered']} of {head['planned']} planned calls, so "
            "there is nothing to compare."
        )
        lines = ["# Jev as a third reader of the ClimaQA misses", "", nothing, "", spend, ""]
        return "\n".join([*lines, *sources, ""])
    median = f"Latency per call: median {a['median_seconds']:.3f} s"
    latency = (
        f"{median}, p90 {a['p90_seconds']:.3f} s."
        if a["p90_seconds"] is not None
        else f"{median}; the p90 needs two answered calls or more."
    )
    lines = [
        "# Jev as a third reader of the ClimaQA misses",
        "",
        f"Provider {', '.join(a['providers'])}, model requested {', '.join(a['requested'])}; the",
        f"replies name model {', '.join(a['models'])}{relayed}. Calls made on",
        f"{', '.join(a['dates'])} (UTC). One item per request, {a['runs']} identical calls per",
        "item in a fixed option order and one call per other rotation of the options,",
        f"{a['items']} items (decision 0008).",
        "",
        *partial,
        "| comparison | items | kappa |",
        "|---|---|---|",
        *(f"| {label} | {a[f'n_{key}']} | {_f(a[f'kappa_{key}'])} |" for label, key in rows),
        "",
        bias_line,
        "",
        brier_line,
        "",
        f"Stability: all {a['runs']} fixed-order calls chose the same bucket on {a['all_same']}"
        f" of {a['items']} items; mean pairwise agreement {_f(a['agreement'])}.",
        "",
        spend,
        "",
        latency,
        "",
        "Items outside the miss sort, by Jev's bucket: "
        + (", ".join(f"{k} {v}" for k, v in sorted(a["others"].items())) or "none")
        + ".",
        "",
        *sources,
    ]
    return "\n".join([*lines, ""])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jev third reader: run the calls, keep their results, then report."
    )
    parser.add_argument("step", choices=["run", "results", "report"])
    step = parser.parse_args().step
    if step == "run":
        chosen = jev.provider()  # an unvetted JEV_BASE_URL stops here, before any key is read
        key = jev.load_key(chosen)  # the chosen provider's key, and no other
        rows = sheet()
        print(jev.summary(chosen))  # before the first call, and never the key
        try:
            records = run(rows, key, provider=chosen)
        except jev.CallError:
            print(outcome(load(LOG), rows))
            raise
        print(outcome(records, rows))
        return
    if step == "results":
        records = load(LOG)
        results.write(RESULTS, header(records), [compact(r) for r in records])
        print(f"{len(records)} calls written to {RESULTS}")
        return
    head, rows = results.read(RESULTS)  # the report needs no log
    REPORT.write_text(render(analyse(rows, mine(), blind_sort()), head, RESULTS), "utf-8")
    print(f"report written to {REPORT}")


if __name__ == "__main__":
    main()
