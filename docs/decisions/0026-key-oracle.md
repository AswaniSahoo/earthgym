# 0026: a second computation of the bundled heat and storm keys

Date: 2026-11-06. Status: accepted for heat and storm, 2026-11-06. ERA5's archived references stay
on the roadmap.

Context: the Codex review's finding 8, as `docs/roadmap.md` recorded it: the heat and storm item
tests rebuild the items with the same code that made them, "which proves consistency, not
correctness". The review itself is not in this repo. A bug in that code would make a wrong key, the
rebuild would reproduce it byte for byte, and the reward would then pay for the wrong answer.

Decision:

- `tests/key_oracle.py` takes a rendered prompt and returns the answer. It reads the question, the
  threshold, the run length, the cover dates, the statuses, the scale and the rows out of the prompt
  text. It imports only the standard library, which a test holds it to, and it raises `ValueError`
  on text it cannot read.
- `tests/test_key_oracle.py` compares it with every bundled key, 300 heat and 300 storm, and sends
  its answers through each environment's own reward. It runs in CI, with no network and no pinned
  file.
- A separate AI agent (Claude Fable 5.1) wrote the oracle blind. It was given the rendered prompts
  alone, with no keys or item ids, told not to open this repo, and asked to apply each rule
  literally. The build session had already read the key code, so an oracle written there would have
  copied its reading. The 14 tool calls in the agent's transcript name no path in this repo. The
  tests were written first, with the fixtures' answers worked out from the prompts' rules without
  running code.

Result: on the first comparison, with the module as the agent delivered it, all 600 keys match and
every test passes, so no key changed. The module's code has changed since only by a docstring, by
`strict=True` on two `zip` calls and by `ruff format`.

A clean comparison is worth what it could have caught, so `WRONG_RULES` in the test pins how many of
a question's 100 keys each wrong rule would change. Most would show at once: hours from every HU row
99, events at more than k days 50, trigger days above the threshold 93. Some clauses are barely
tested by the bundled keys:

- The 34 kt floor in ACE changes 0 keys: no named six-hourly row in these 100 storms is below it.
  Nothing tested the floor on a named row, so `tests/test_ibtracs_stats.py` now does.
- HU rows only, for the peak category, changes 0 keys: the highest wind in these storms is on an HU
  row. `tests/test_ibtracs_stats.py` already tests that clause.
- A dash ending a run changes 1 key, and a missing index value in missed days 8, which fits the one
  index season with gaps. `tests/test_heat_policy.py` already tests both.

What it does not show:

- That a prompt is right about the world. The oracle shows that a key follows from its prompt. The
  rows and the rule text reach both from this repo's code, so a wrong column, a misread archive or a
  wrong rule in the prompt would pass. The reproductions of NCEI's and NWS Phoenix's published
  counts (`reports/ibtracs/2026-11-01-ncei-reproduction.md`,
  `reports/heat/2026-11-01-nws-phoenix-reproduction.md`) are what test those.
- That anyone but a machine checked it. Separate here means separate code and a separate context,
  not a person and not another vendor. My review of this record is still to come
  (`docs/human-checks/decisions.md`).
- The other prompt versions. The terms-only, rules-hidden and tools prompts share these keys, and
  the oracle reads only the rules-shown one.

The oracle matches the prompts' sentences whole, so rewording a prompt makes it raise and the test
fail. I keep that: a changed prompt should be read again against the oracle.

The main alternative was HURDAT2, NHC's own archive (`docs/radar.md`, assess), as a second source
for the storm keys. It would also test the rows, but it needs a new pinned file, a parser and a
match from each storm to its IBTrACS SID, so it stays in the assess ring. Putting the oracle under
`src/` was the other choice; nothing at run time needs it, so it sits with the tests.
