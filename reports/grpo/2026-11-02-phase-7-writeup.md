# Does the reward teach a small model? GRPO on climaqa-v1 MCQ

Phase 7 of earthgym, run on 2026-11-02 and 2026-11-03, written up on 2026-11-06. The numbers come
from `reports/grpo/2026-11-02-run.md`, which re-renders from
`reports/grpo/results/2026-11-02-run-metrics.json` (`tests/test_published_numbers.py`). The counts
of right answers and cut replies come from the per-item rows in that file.

**The result: the model learned the train items, with no measurable transfer to held-out items.**
One seed, one run.

## The question

An environment is useful for RL only if a model can learn from its reward. GRPO compares several
completions of one prompt, so it needs items whose reward varies. I fixed the rule for choosing
the task before the small-model runs reported (decision 0024), and it picked climaqa-v1 MCQ: of
the five tasks, it has the highest mean reward variance on its train items, 0.0958, and its median
reply fits the training cap.

## The run

Qwen3.5-2B with a LoRA of rank 16, trained by TRL's `GRPOTrainer` through Unsloth on one Kaggle T4:
250 steps of one prompt and 8 completions, 1.47 passes over the 170 train items, at most 1,024
completion tokens, with cut completions left out of the loss. Before and after training, 8 samples
of each of the 52 test items and of the first 52 train items, scored by the environment's own
contract. All settings are in decision 0024.

## Results

| split | items | when | mean reward | right, of 416 | replies cut | right among uncut | pass@8 |
|---|---|---|---|---|---|---|---|
| train | 52 | before | 0.728 | 303 | 24 | 0.773 | 0.942 |
| train | 52 | after | 0.832 | 346 | 5 | 0.842 | 0.962 |
| test | 52 | before | 0.740 | 308 | 39 | 0.817 | 0.942 |
| test | 52 | after | 0.750 | 312 | 19 | 0.786 | 0.885 |

- Train items: 22 better, 5 worse, 25 the same; two-sided sign test p 0.0015.
- Held-out items: 12 better, 10 worse, 30 the same; two-sided sign test p 0.83.
- In the trainer's own log, the reward averages 0.615 over the first 25 steps and 0.800 over the
  last 25. Each step is a different prompt, so that curve is noisy. 149 of the 250 steps had the
  same reward on all 8 completions and so gave no signal.

## What this means

- The reward moves the policy on items it trains on: 43 more right samples of 416, and more of the
  uncut replies right.
- It does not move held-out reward by a measurable amount: 4 more right samples of 416, and the
  items that got better about match the ones that got worse.
- The model also learned to finish. Cut replies fell on both splits, 24 to 5 and 39 to 19. A cut
  reply rarely has an answer line (4 of these 87 scored), so finishing alone can raise the reward.
  On the held-out items it did not add up to better answers: replies cut fell by 20, right samples
  rose by 4, and the share right among uncut replies fell from 0.817 to 0.786.
- The held-out items had limited but real room: 29 of the 52 were always right before training, and
  pass@8 stood at 0.942. After training it is 0.885, with 6 items never right in 8 samples against
  3 before.

## Limits

- One seed and one run, so the spread between runs is not measured.
- 52 items a split, 8 samples each. The sign test counts only items whose mean moved.
- The train items were seen in training, on 1.47 passes over 170 items; only 52 of the 170 were
  sampled before and after.
- ClimaQA gives no source passage to group by, so its split is by item (decision 0017). The set is
  exact-overlap-filtered, and 21 near matches of Silver remain unresolved
  (`reports/climaqa/clean_v1_manifest.json`).
- The starting point differs from the small-model run of decision 0025 (test mean 0.786): this run
  sampled the full weights in float32 under a 1,024-token cap, that one the Q8_0 GGUF under 4,096.
- 250 steps is small. A longer run or other settings could differ; I did not search them.
- The adapter, 42 MB, is not in git. It stays in the kernel's private output.

## Reproduce

    uv run python -m earthgym.grpo.pick                # the task, from the committed results
    uv run python -m earthgym.grpo.kernel <folder> --user <kaggle user> --preset run
    kaggle kernels push -p <folder> -t 43200           # a private kernel on Kaggle's T4 x2
    kaggle kernels output <kaggle user>/earthgym-grpo -p <dir>
    uv run python -m earthgym.grpo.report <dir>/metrics.json --name "250 steps" \
        --date 2026-11-02 --window 25 --out <report>.md
