# ibtracs-storm-v1: the rows in the prompt against a query tool

Model `anthropic/claude-sonnet-5-5` on the same 300 items three ways: the rules and the rows in the prompt; the rule left out (`-T rules=false`); and the rule left out with the rows behind the query tool (`-T tools=true`, decision 0023).

| question | n | rules shown | rules hidden | tools |
|---|---|---|---|---|
| ace | 100 | 0.990 | 0.990 | 0.990 |
| peak_category | 100 | 1.000 | 0.990 | 1.000 |
| hurricane_hours | 100 | 1.000 | 0.130 | 0.250 |
| all | 300 | 0.997 | 0.703 | 0.747 |

Wrong answers that equal a careless reading of the rule, with the rows in the prompt and with the tool:

| question | careless reading | rules hidden | tools |
|---|---|---|---|
| ace | ACE over every row | 0 | 0 |
| ace | ACE ignoring status | 0 | 0 |
| ace | ACE from TS and HU only | 0 | 0 |
| peak_category | category ignoring status | 0 | 0 |
| peak_category | category from synoptic rows only | 0 | 0 |
| peak_category | category by the mph thresholds | 0 | 0 |
| hurricane_hours | hours over every HU row | 0 | 0 |
| hurricane_hours | each row's status holds until the next row | 15 | 38 |
| hurricane_hours | elapsed time of each hurricane spell | 48 | 25 |

## What the tool changes

Both runs leave the rule out. They differ in where the rows are and in react's system prompt and submit tool, which the prompt run did not have (decision 0023). Per question:

- ace: 0.990 with the rows in the prompt, 0.990 with the tool: about the same (within five points).
- peak_category: 0.990 with the rows in the prompt, 1.000 with the tool: about the same (within five points).
- hurricane_hours: 0.130 with the rows in the prompt, 0.250 with the tool: higher by 0.120.

Items that only one of the two runs gets right, per question, with an exact two-sided McNemar test on them (each run answers each item once):

| question | right only with the rows in the prompt | right only with the tool | p |
|---|---|---|---|
| ace | 1 | 1 | 1.000 |
| peak_category | 0 | 1 | 1.000 |
| hurricane_hours | 4 | 16 | 0.012 |
