# Draft: the eval logs as a release asset

Not published. The Inspect logs behind every reported number live under `logs/`, which git
ignores; the per-item results in `reports/<env>/results/` already let anyone recompute the
numbers (decision 0019), and the logs add the full replies.

## What would go up

| logs | size | runs |
|---|---|---|
| `logs/2026-10-30-gemini-3.8-flash` | 2.9 MB | ClimaQA clean v1, MCQ and cloze |
| `logs/2026-11-01-climaqa-claude-sonnet-5-5` | 1.2 MB | ClimaQA clean v1, MCQ and cloze |
| `logs/2026-11-01-era5-claude-sonnet-5-5` | 2.7 MB | ERA5, the 720 drawn items |
| `logs/2026-11-01-ibtracs-claude-sonnet-5-5` and `-hidden-` | 1.5 and 1.8 MB | IBTrACS, rules shown and hidden |
| `logs/2026-11-01-heat-claude-sonnet-5-5` and `-heat-terms-` | 1.8 and 1.9 MB | heat, rules shown and terms only |
| `logs/2026-11-02-ibtracs-tools-claude-sonnet-5-5` | 2.8 MB | IBTrACS tools mode (decision 0023) |
| the eight probe logs | 0.5 MB in all | the probes in `reports/spend.md` |

About 17 MB for the Sonnet and Gemini runs (`du`, 2026-11-02). The small-model logs of decision
0025 come on top: 113 MB of `.eval` files (`du`, 2026-11-06).

## Before uploading

- The two Gemini logs carry Python tracebacks from retried calls with local paths
  (a home-directory path 28 and 60 times, the repository's path 244 and 520 times);
  the Sonnet logs carry neither (checked 2026-11-02 on the ClimaQA, heat, ERA5 and IBTrACS
  tools-mode logs). Decide
  whether to upload them as they are or rewrite those paths, and say so in the release notes.
  No key or token appears in any log checked.
- List each file with its sha256 in the release notes, as for `data-v1`.

## How, when I decide

    tar -czf earthgym-logs-v1.tar.gz logs/2026-10-30-gemini-3.8-flash logs/2026-11-01-*
    sha256sum earthgym-logs-v1.tar.gz
    gh release create logs-v1 earthgym-logs-v1.tar.gz --title "Eval logs v1" --notes-file <notes>

The inspect_evals Register takes its two full ClimaQA logs separately, through its own upload
page (`docs/release/inspect-evals-register.md`).
