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
| peak_category | category ignoring status | 0 |
| peak_category | category from synoptic rows only | 0 |
| hurricane_hours | hours over every HU row | 0 |
| hurricane_hours | elapsed time, first to last HU row | 41 |

## What this means for RL

With the rules shown the model is right on 299 of 300 items, so nearly every rollout earns the same reward and an RL policy this strong gets almost no signal to learn from; that version serves as a regression check, or for weaker models. With rules hidden, accuracy falls to 0.703: the gap is what the left-out rules carry, so the rules hidden version has room to learn.

On hurricane_hours, 41 of the 87 wrong answers equal 'elapsed time, first to last HU row'. With the rule left out, that can follow a convention other than ours, so this part of the gap measures which convention the model picks, not its skill.
