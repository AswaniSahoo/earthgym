# Review: the Jev provider change, 2026-11-19

Not a phase review. An EGM-lite Goldfish diff review of the change behind the 2026-11-19
amendment to decision 0008: provider choice for the Jev third reader, its pacing, retries, resume
and failure accounting, the amendment itself, and one note in climate-risk-agent's `DEPLOY.md`.
The reviewer was Google's Elephant-Goldfish Model plugin (egm 0.1.1), agent
`egm:egm-codebase-details`: a fresh reader given only the checklist, the diff against `2ed5f18`,
the files the amendment cites and saved copies of the pages it quotes, with no session history.
It is not the reviewer agent in `.claude/agents/reviewer.md`.

Priorities: P1 defect, P2 polish, P3 nit (no P0). Every code fix landed test-first; findings 5 to
8, 12 and 15 were edits to documents.

| # | priority | finding | resolution |
|---|---|---|---|
| 1 | P1 | A failed call was neither logged nor charged, so a relaunch sent it again outside the budget. | Fixed: a failure record with the error and an estimate; every try charged; a relaunch resends failed calls only. |
| 2 | P1 | Resume removed the guard against two launches at once. | Fixed: an exclusive lock file next to the log. |
| 3 | P1 | Nothing enforced "vetted but not used" for the gateway. | Withdrawn: the decision changed the same day, and the gateway is now the fallback. |
| 4 | P2 | A key was not tied to its provider, so the gateway key could reach TypeSafe. | Fixed: each provider reads only its own key. |
| 5 | P2 | The `DEPLOY.md` line citations went stale. | Fixed. |
| 6 | P2 | The amendment left out the last sentence of the gateway's terms, section 7.4, and cited no source for the 2026-11-11 notice. | Fixed: quoted, and the notice cited to climate-risk-agent's run record. |
| 7 | P2 | Three quoted gateway pages were not among the saved sources. | Fixed: read again on 2026-11-19; each quote is on its page. |
| 8 | P2 | The new `DEPLOY.md` note contradicted step 4 below it. | Fixed: the note is now a condition on step 4. |
| 9 | P2 | No request id was kept, and no single call could be made. | Request id fixed; a single-call mode withdrawn, since a run stops at the first refusal. |
| 10 | P2 | Two resume paths had no test, and a damaged log failed without naming its line. | Fixed. |
| 11 | P2 | A key ending in CR or LF could appear in a traceback. | Fixed: keys stripped, odd keys refused by name. |
| 12 | P2 | The human-checks row no longer matched the amendment. | Fixed. |
| 13 | P3 | Pacing ran on wall time, and `JEV_MIN_INTERVAL_S` was not validated. | Fixed: monotonic clock, finite and 0 or more. |
| 14 | P3 | TypeSafe's `detail` refusals were not read. | Fixed. |
| 15 | P3 | Wrapping and two citations in the amendment. | Fixed. |

## Second review, 2026-11-19

A fresh `egm:egm-codebase-details` reader of the fixed diff, the new results file and report, and
the same sources. It also checked that the first round's resolutions were real.

| # | priority | finding | resolution |
|---|---|---|---|
| 1 | P1 | A 200 with a usage count but an unusable answer was neither logged nor charged, and a relaunch sent it again. | Fixed: every 200 is checked against the options sent; a bad one is a failed call. |
| 2 | P2 | `items_sha256` hashed the whole expert sheet, including the columns the expert review will fill. | Fixed: it hashes only what each request sends. |
| 3 | P2 | The results header's commit was a constant. | Fixed: each record carries its commit and whether the tree was dirty; the old log falls back to `2ed5f18`, from git reflog. |
| 4 | P2 | Two claims in the build log about the run's history had no source. | Fixed: the reflog is cited and the report claim narrowed. |
| 5 | P2 | The headline rule left out that `JEV_BASE_URL` comes first, and overstated the match with climate-risk-agent. | Fixed. |
| 6 | P2 | 0008 still said its outputs never train a model. | Fixed: limited to this repository's own use, with the MCA 2.3(b) question marked UNKNOWN. |
| 7 | P2 | The report gave neither its exact config nor its sources. | Fixed: items revision, prompt location, results file and the sources of both reference sorts. |
| 8 | P2 | Several new branches had no test. | Fixed. |
| 9 | P3 | Retrying a 5xx through the gateway went against its Jev page. | Fixed: read in full, the page asks for no automatic retries at all, so nothing is retried through the gateway. |
| 10 | P3 | The build log overstated the first round's count. | Fixed. |
| 11 | P3 | Status lines would have been committed stale. | Fixed. |
| 12 | P3 | The Data controls quote had no address. | Fixed: the page address, as the owner's own account settings. |
| 13 | P3 | Citations into climate-risk-agent named no commit. | Fixed: pinned to `d5d7c84`. |
| 14 | P3 | Output tokens were not kept per row. | Fixed. |

## Third review, 2026-11-19

A fresh `egm:egm-codebase-details` reader of the fixed diff, with the same sources.

| # | priority | finding | resolution |
|---|---|---|---|
| 1 | P2 | A redirect from a vetted host would carry the bearer key to whatever host it names. | Fixed: redirects are refused, and a 3xx is a failed call after one request. |
| 2 | P2 | A shell set up as climate-risk-agent's default (a TypeSafe key in `JEV_API_KEY`) would send that key to the gateway. | Fixed: falling back to the gateway needs `JEV_API_KEY` in `.env`, and the provider and key source are printed before the first call. |
| 3 | P3 | A run that stopped early could not be reported or told apart from a finished one. | Fixed: incomplete rotation sets are left out and counted; the header records planned and answered calls and `complete`. |
| 4 | P3 | `usage.output_tokens` was not checked, and an empty model name passed. | Fixed: a missing count is 0, as in climate-risk-agent; a present one must be a whole number of 0 or more. |
| 5 | P3 | Branches of the answer check had no test. | Fixed. |
| 6 | P3 | The amendment's wrapping broke again. | Fixed: rewrapped at 100 columns. |
| 7 | P3 | 0008's Status line did not mention the amendment or the run. | Fixed. |
| 8 | P3 | The run's times were cited to the report, which does not hold them. | Fixed: cited to the results header. |

## Fourth review, 2026-11-19

| # | priority | finding | resolution |
|---|---|---|---|
| 1 | P2 | A gateway `JEV_BASE_URL` in `.env` with climate-risk-agent's `JEV_API_KEY` exported in the shell still sent a TypeSafe key to the gateway. | Fixed: the gateway's key must come from the same place as the choice of provider. |
| 2 | P2 | The token-count check did not match the documented rule (9.5 accepted, 53.0 refused). | Fixed: whole numbers of 0 or more, int or integer float. |
| 3 | P3 | The 2026-11-11 notice quote had no source. | Fixed: cited to climate-risk-agent's run record. |
| 4 | P3 | Two module docstrings described the old fallback. | Fixed. |
| 5 | P3 | Citations into climate-risk-agent in code comments named no commit. | Fixed: pinned to `d5d7c84`. |
| 6 | P3 | Runs with 0 or 1 answered calls, or an empty log, could not be reported. | Fixed. |
| 7 | P3 | The success message had no test. | Fixed. |
| 8 | P3 | The build log's review count would be stale. | Fixed. |
| 9 | P3 | The checklist was behind the diff. | Fixed. |
| 10 | P3 | `completed` was the last call's start, and `docs/reproduce.md` did not describe this results file. | Fixed: `completed` is the last call's end (the same second for this run); reproduce.md names the report and its per-call rows. |

## Fifth review, 2026-11-19

Limited to material issues (P0 to P2).

| # | priority | finding | resolution |
|---|---|---|---|
| 1 | P2 | 0008 described the gateway key's sources differently from the code, which fails closed. | Fixed: 0008 states the code's rule. |
| 2 | P2 | The refusal of an exported `JEV_API_KEY` advised exporting `JEV_BASE_URL` too, which would send a TypeSafe key to the gateway. | Fixed: the advice depends on which kind of key was exported. |
| 3 | P2 | The estimate of one token per 2 characters ran 6 to 12% below the reported counts, so the cap check was not an upper bound. | Fixed: one token per 1.4 characters, below the minimum of 1.634 measured over all 626 calls, with a test for each call. |

## Sixth check, 2026-11-19

Of the fifth review's three fixes only, material issues only. It found all three resolved, and one
P1 in the code they touched.

| # | priority | finding | resolution |
|---|---|---|---|
| 1 | P1 | A `JEV_BASE_URL` of only slashes counted as unset but kept its source, so an exported `JEV_API_KEY` reached the gateway with no refusal. | Fixed: a `JEV_BASE_URL` that is set but names no vetted provider is refused before any key is read. |

## Seventh check, 2026-11-19

Of that fix only. No defect in the code, and one P2.

| # | priority | finding | resolution |
|---|---|---|---|
| 1 | P2 | No test pinned that a blank exported `JEV_BASE_URL` keeps the gateway key off the environment, so a refactor of `found` could reopen the leak with every test passing. | Fixed: blank rows in the key-source test; under that refactor 3 of them fail, and on the code they pass. |

The loop closed here: the last finding was a test gap, fixed and shown to catch the failure it
names.
