# 0004: one answer contract for Inspect and verifiers

Date: 2026-10-30. Status: accepted. Supersedes the scorer part of 0002.

Context: the Phase 2 review found the verifiers reward and Inspect's built-in `choice()` disagreed
on 14 of 38 test replies, and Inspect's `exact()` dropped articles while the verifiers reward did
not. Two harnesses that count different replies as correct cannot be compared.

Decision: `environments/climaqa_v1/climaqa_v1/contract.py` holds the prompts and the rules, and
both harnesses import it. MCQ: the reply's last line must be only `ANSWER: X` (case and markdown
bold ignored); anything else is wrong, including a bare letter. Cloze: SQuAD-style exact match
(casefold, punctuation to spaces, articles dropped). The Inspect tasks use a small custom scorer
over the contract; options come pre-shuffled from the clean set, so no harness shuffles.

Consequences: format failures count as wrong in every harness, so reports also give the share of
replies that broke the format. Plurals still count as wrong for cloze.
