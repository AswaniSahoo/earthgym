# ibtracs-storm-v1: rules shown against rules hidden

Model `anthropic/claude-sonnet-5-5` on the same 300 items, once with each question's rule in the prompt and once with the rule left out (`-T rules=false`).

| question | n | accuracy, rules shown | accuracy, rules hidden |
|---|---|---|---|
| ace | 100 | 0.990 | 0.990 |
| peak_category | 100 | 1.000 | 0.990 |
| hurricane_hours | 100 | 1.000 | 0.130 |
| all | 300 | 0.997 | 0.703 |

Wrong answers in the rules hidden run that equal a careless reading of the rule:

| question | careless reading | misses that match |
|---|---|---|
| ace | ACE over every row | 0 |
| ace | ACE ignoring status | 0 |
| ace | ACE from TS and HU only | 0 |
| peak_category | category ignoring status | 0 |
| peak_category | category from synoptic rows only | 0 |
| peak_category | category by the mph thresholds | 0 |
| hurricane_hours | hours over every HU row | 0 |
| hurricane_hours | each row's status holds until the next row | 15 |
| hurricane_hours | elapsed time of each hurricane spell | 48 |

## What this means for RL

With the rules shown the model is right on 299 of 300 items. That run is the control: nearly every rollout earns the same reward, so an RL policy this strong gets almost no signal to learn from. Per question, against rules hidden:

- ace: 0.990 with the rules shown, 0.990 hidden: near the ceiling either way, so the model fills in this rule itself.
- peak_category: 1.000 with the rules shown, 0.990 hidden: near the ceiling either way, so the model fills in this rule itself.
- hurricane_hours: 1.000 with the rules shown, 0.130 hidden, and 63 of the 87 misses follow a careless reading of the rule: a convention gap, and, as an untested guess, one a policy would close as a constant offset rather than learn as a skill.

Replies that name the storm or its season: 2 of 300 with the rules shown, 4 hidden.
