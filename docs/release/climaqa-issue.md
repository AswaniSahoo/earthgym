# Draft: an issue for the ClimaQA maintainers

Not posted. I post it myself, if and when I decide, as an issue on
[Rose-STL-Lab/genie-climaqa](https://github.com/Rose-STL-Lab/genie-climaqa) or a discussion on
the Hugging Face dataset. Every line in brackets is mine to write in my own words; the rest is
the facts, each checked against the files.

Where it would land (checked 2026-11-02): genie-climaqa has no issue template and no
CONTRIBUTING file, has never had an issue or a pull request, and was last pushed 2025-03-14. The
Hugging Face dataset has 2 discussions, both from 2025-03-17. The paper names the repository as
its code ("The source code is publicly available at" github.com/Rose-STL-Lab/genie-climaqa) and
gives correspondence to Rose Yu and Taylor Berg-Kirkpatrick. Its dataset link,
`UCSD-GENIE/ClimaQA`, redirects to `Rose-STL-Lab/ClimaQA`.

**Title:** 43 Gold test questions appear verbatim in the Silver training set

[In my own words: one or two sentences on who I am and why I looked at the dataset.]

On the Hugging Face dataset `Rose-STL-Lab/ClimaQA` at revision `3f084a0202c6260e588fb5b681d2e4ec859a3845`:

- 43 questions of the expert-validated Gold set (`Validation` True) appear word for word, with
  case and whitespace folded, in the Silver set of the same task: 17 multiple choice, 9 cloze and
  17 freeform. For 29 of them the answer is the same as well; for 14 it differs.
- 6 more Gold questions appear in the Silver set of another task.
- The paper fine-tunes on Silver and evaluates on Gold: "we fine-tune LLaMA3.1-8B-Instruct and
  Mistral-7B-v0.3-Instruct on the ClimaQA-Silver dataset ... We then evaluate the impact of this
  task-specific fine-tuning by assessing the models’ performance on the ClimaQA-Gold dataset"
  (arXiv 2410.16701v2). The ft-silver results include these items.
- The Gold multiple-choice and freeform files also hold the rows the experts rejected
  (`Validation` False: 47 multiple choice, 20 freeform). The evaluation notebooks keep only
  `Validation` True, which matches the paper's counts, but a loader that reads the files directly
  scores the rejected rows too.

[In my own words: what I would suggest, for example marking the overlaps or leaving them out of
Silver.]

How I checked: a standard-library audit of the six CSV files at that revision
(`uv run python -m earthgym.climaqa.audit` in https://github.com/AswaniSahoo/earthgym, which
writes `reports/climaqa/findings.json` with every pair below).

### Gold questions found in the same task's Silver set (43)

| Gold item | Silver items | answer |
|---|---|---|
| gold/cloze:0 | silver/cloze:86 | same |
| gold/cloze:6 | silver/cloze:566, silver/cloze:885 | same |
| gold/cloze:44 | silver/cloze:216 | same |
| gold/cloze:50 | silver/cloze:733 | same |
| gold/cloze:78 | silver/cloze:592 | same |
| gold/cloze:94 | silver/cloze:233, silver/cloze:560 | same |
| gold/cloze:104 | silver/cloze:106, silver/cloze:454 | same |
| gold/cloze:119 | silver/cloze:429, silver/cloze:463 | same |
| gold/cloze:123 | silver/cloze:234 | same |
| gold/ffq:4 | silver/ffq:34 | same |
| gold/ffq:12 | silver/ffq:630 | same |
| gold/ffq:16 | silver/ffq:631 | same |
| gold/ffq:21 | silver/ffq:671 | differs |
| gold/ffq:63 | silver/ffq:492 | same |
| gold/ffq:73 | silver/ffq:21, silver/ffq:491 | same |
| gold/ffq:76 | silver/ffq:970 | same |
| gold/ffq:79 | silver/ffq:22 | same |
| gold/ffq:84 | silver/ffq:560 | differs |
| gold/ffq:94 | silver/ffq:26 | same |
| gold/ffq:103 | silver/ffq:969 | differs |
| gold/ffq:108 | silver/ffq:790, silver/ffq:911 | same |
| gold/ffq:142 | silver/ffq:730 | same |
| gold/ffq:161 | silver/ffq:27 | same |
| gold/ffq:162 | silver/ffq:559 | differs |
| gold/ffq:178 | silver/ffq:588 | same |
| gold/ffq:179 | silver/ffq:590 | differs |
| gold/mcq:2 | silver/mcq:188, silver/mcq:399, silver/mcq:576 | same |
| gold/mcq:22 | silver/mcq:176 | same |
| gold/mcq:61 | silver/mcq:114 | differs |
| gold/mcq:93 | silver/mcq:895 | same |
| gold/mcq:100 | silver/mcq:903 | same |
| gold/mcq:112 | silver/mcq:553 | differs |
| gold/mcq:139 | silver/mcq:812 | differs |
| gold/mcq:158 | silver/mcq:943 | differs |
| gold/mcq:163 | silver/mcq:652 | differs |
| gold/mcq:171 | silver/mcq:75, silver/mcq:760, silver/mcq:805 | same |
| gold/mcq:176 | silver/mcq:787 | same |
| gold/mcq:191 | silver/mcq:593 | differs |
| gold/mcq:201 | silver/mcq:555 | differs |
| gold/mcq:220 | silver/mcq:55 | differs |
| gold/mcq:225 | silver/mcq:405, silver/mcq:872 | same |
| gold/mcq:240 | silver/mcq:844 | same |
| gold/mcq:287 | silver/mcq:50, silver/mcq:281 | differs |

### Gold questions found in another task's Silver set (6)

| Gold item | Silver items |
|---|---|
| gold/ffq:60 | silver/mcq:908 |
| gold/ffq:92 | silver/mcq:657 |
| gold/ffq:113 | silver/mcq:656 |
| gold/ffq:150 | silver/mcq:439 |
| gold/mcq:2 | silver/ffq:272, silver/ffq:415 |
| gold/mcq:17 | silver/ffq:281 |
