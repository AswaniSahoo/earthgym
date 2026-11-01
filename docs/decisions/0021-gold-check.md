# 0021: a gold check for every environment

Date: 2026-11-02. Status: accepted, 2026-11-02. From the market review of 2026-11-02, which
found that no taskset checks its reference answers.

Context: verifiers' `vf-validate` can run a gold check on every task, "Apply and check the
reference answer" (`_gold` in `verifiers/v1/cli/validate.py`, verifiers 0.4.0), by calling the
task's `validate`. The default `Task.validate` returns None, "when no model-free check exists"
(`verifiers/v1/task.py:195-197`), and none of the four tasksets overrode it, so the check never
ran; CI ran `vf-validate --only-noop`.

Decision:

- Each contract has `gold`, the reference reply: for ClimaQA MCQ the key's answer line and for
  cloze the key itself, for ERA5 the truth, for IBTrACS the key with ACE rounded to one decimal,
  for heat the count. Each taskset's `validate` scores that reply through the task's own reward
  and passes only at 1.0. CI runs `vf-validate` in full, the gold check and the untouched one, on
  all four environments.
- An item that fails the gold check leaves the set. ClimaQA (350 items), IBTrACS (300) and heat
  (300) pass on every item. ERA5 fails on 72 of the 720 drawn: where the floor binds (a better
  baseline error b below the floor, 36 items per variable), a perfect forecast earns b / floor,
  below 1, and on 3 of them 0, because a baseline is exact. The item builder now drops them after
  the floors are set from the whole draw. The manifest records the draw (720 items, sha256
  c4a1dd7c..., the file the 2026-11-01 runs were scored on), the 72 dropped and the 648 kept
  (sha256 b0ae4063...).
- A report of a run scored on the draw covers the 648 kept items and says how many it leaves out.
  The per-item results keep all 720 rows, as the run recorded them.

The main alternative was to keep the 72 items and change the reward so that a perfect forecast
earns 1 on them too, for example by dividing by b instead of max(b, floor). That would change
the reward rule of decision 0007 and let a near-zero b inflate the reward, which is what the
floor is there to stop. The dropped items left little to earn: Sonnet 5.5 averaged 0.0118 on them.

Consequences, every number recomputed from the committed per-item results, with no new run:

| number | on the 720 drawn items | on the 648 kept |
|---|---|---|
| Sonnet 5.5 mean reward | 0.1161 (stderr 0.0093) | 0.1277 (stderr 0.0102) |
| midpoint of persistence and climatology | 0.1074 | 0.1175 |
| Sonnet minus midpoint, item by item | +0.0087 (SE 0.0077) | +0.0102 (SE 0.0085) |
| IFS HRES, per variable and lead | 0.30 to 0.67 | 0.34 to 0.71 |
| test split: n, HRES, midpoint, mixture | 119, 0.478, 0.098, 0.094 | 102, 0.554, 0.109, 0.108 |
| train and test items (decision 0017) | 601 and 119 | 546 and 102 |

The Sonnet result against the midpoint stays not significant at two standard errors, and the
mixture's fitted weight stays 0.67. The floor now binds on none of the kept items. The ClimaQA,
IBTrACS and heat numbers do not change.
