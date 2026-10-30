# 0001: the Phase 1 audit uses the standard library only

Date: 2026-10-30. Status: accepted.

Context: ClimaQA ships as six small CSV files (about 1.3 MB). The audit needs download, hashing,
CSV parsing and string checks, nothing else.

Decision: `urllib`, `hashlib`, `csv` and `re` from the standard library. pytest and ruff are dev
tools only.

Consequences: nothing to install at runtime and nothing to keep patched. When Phase 2 needs Inspect
or verifiers, they come in as dependencies of that phase with their own decision record.
