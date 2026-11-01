# heat-basis-v1: rules shown against terms only

Model `anthropic/claude-sonnet-5-5` on the same 300 items, once with each question's rule in the prompt and once with the policy terms alone (`-T rules=false`).

| question | n | accuracy, rules shown | accuracy, terms only |
|---|---|---|---|
| trigger_days | 100 | 1.000 | 0.990 |
| events | 100 | 1.000 | 1.000 |
| missed_days | 100 | 0.960 | 0.890 |
| all | 300 | 0.987 | 0.960 |

Wrong answers in the terms only run that equal a careless reading of the rule:

| question | careless reading | misses that match |
|---|---|---|
| trigger_days | above, not at, the threshold | 0 |
| trigger_days | the site's column | 0 |
| events | trigger days, not events | 0 |
| events | every run, whatever its length | 0 |
| events | missing days skipped | 0 |
| missed_days | both ways | 0 |
| missed_days | every hot site day | 0 |
| missed_days | missing index days left out | 6 |

## What this means for RL

With the rules shown the model is right on 296 of 300 items. That run is the control: nearly every rollout earns the same reward, so an RL policy this strong gets almost no signal to learn from. Per question, against terms only:

- trigger_days: 1.000 with the rules shown, 0.990 with terms only: near the ceiling either way, so the model fills in this rule itself.
- events: 1.000 with the rules shown, 1.000 with terms only: near the ceiling either way, so the model fills in this rule itself.
- missed_days: 0.960 with the rules shown, 0.890 with terms only, and 6 of the 11 misses follow a careless reading of the rule: a convention gap, which a policy would close as a constant offset rather than learn as a skill.
