# Does the reward teach a small model? GRPO on climaqa-v1 MCQ

Phase 7 of earthgym, run on 2026-11-02 and 2026-11-03, written up on 2026-11-06. The numbers come
from `reports/grpo/2026-11-02-run.md`, which re-renders from
`reports/grpo/results/2026-11-02-run-metrics.json` (`tests/test_published_numbers.py`). The counts
of right answers and cut replies come from the per-item rows in that file.

**The result: the model learned the train items, with no measurable transfer to held-out items.**
One seed, one run. The before and after samplings stopped on different tokens, a flaw in my kernel
that the review found. This headline holds under the worst case of that flaw, but the numbers below
will change when the samplings run again under one stop set; that rerun is scheduled.

## The question

An environment is useful for RL only if a model can learn from its reward. GRPO compares several
completions of one prompt, so it needs items whose reward varies. I fixed the rule for choosing the
task after the laptop's ClimaQA numbers and before any other small-model result (decision 0024), and
it picked climaqa-v1 MCQ: of the five tasks, it has the highest mean reward variance on its train
items, 0.0958, and its median reply fits the training cap.

## The run

Qwen3.5-2B with a LoRA of rank 16, trained by TRL's `GRPOTrainer` through Unsloth on one Kaggle T4:
250 steps of one prompt and 8 completions, 1.47 passes over the 170 train items, at most 1,024
completion tokens, with cut completions left out of the loss. Before and after training, 8 samples
of each of the 52 test items and of the first 52 train items, scored by the environment's own
contract. All settings are in decision 0024.

## Results

| split | items | when | mean reward | right, of 416 | replies cut | right among uncut | median reply | pass@8 |
|---|---|---|---|---|---|---|---|---|
| train | 52 | before | 0.728 | 303 | 24 | 0.773 | 369 | 0.942 |
| train | 52 | after | 0.832 | 346 | 5 | 0.842 | 681 | 0.962 |
| test | 52 | before | 0.740 | 308 | 39 | 0.817 | 356.5 | 0.942 |
| test | 52 | after | 0.750 | 312 | 19 | 0.776 | 675 | 0.885 |

- Train items: 22 better, 5 worse, 25 the same; two-sided sign test p 0.0015; mean item change
  +0.103 (SE 0.031).
- Held-out items: 12 better, 10 worse, 30 the same; two-sided sign test p 0.83; mean item change
  +0.010 (SE 0.027).
- In the trainer's own log, the reward averages 0.615 over the first 25 steps and 0.800 over the
  last 25. Each step is a different prompt, so that curve is noisy. 149 of the 250 steps had the
  same reward on all 8 completions and so gave no signal.

## A flaw in the samplings

The kernel read its stop tokens from the model's generation config on each sampling. At the pinned
revision that config named only `<|endoftext|>` (the revision has no `generation_config.json`),
while a chat turn ends with `<|im_end|>`. The trainer added `<|im_end|>` when it was built, between
the two samplings (the kernel's log, at 4,886 s). So a reply before training did not stop at the end
of its turn: it could run on, which zeroes it, since the rule reads the last line, or reach the cap
and count as cut. The reply texts were not kept, so how often that happened is UNKNOWN
(`docs/reviews/phase-7-grpo.md`, H1).

Every cut reply before training scored 0, so the worst case is that all of them would have scored.
Then the before means would be at most 0.786 on train and 0.834 on test. Train's 0.832 still beats
0.786, and on test there would be no gain either. So both halves of the result hold. What does not
hold is any reading of the fall in cut replies, because that is the number the stop set moves.

## What this means

- The reward moves the policy on items it trains on: 43 more right samples of 416, and more of the
  uncut replies right.
- It does not move held-out reward by a measurable amount: 4 more right samples of 416, and the
  items that got better about match the ones that got worse.
- Replies got longer, not shorter: the median nearly doubled on both splits, and the trainer's mean
  completion length went from 473 to 671 tokens between the first and last 25 steps. That part of
  the change does not depend on the stop set, since the trainer's own samples shared one throughout.
- The held-out items had limited but real room: 29 of the 52 were always right before training, and
  pass@8 stood at 0.942. After training it is 0.885, with 6 items never right in 8 samples against 3
  before. These counts carry the flaw above.

## Limits

- One seed and one run, so the spread between runs is not measured.
- 52 items a split, 8 samples each. The sign test counts only items whose mean moved.
- The train items were seen in training, on 1.47 passes over 170 items; only 52 of the 170 were
  sampled before and after.
- ClimaQA gives no source passage to group by, so its split is by item (decision 0017). The set is
  exact-overlap-filtered, and 21 near matches of Silver remain unresolved
  (`reports/climaqa/clean_v1_manifest.json`).
- The starting point differs from the small-model run of decision 0025 (test mean 0.786): this run
  sampled float16 weights with a float32 LoRA and no autocast, under a 1,024-token cap, and that one
  the Q8_0 GGUF under 4,096.
- The samplings were not seeded. The LoRA covers every layer's MLP and the q, k, v and o projections
  of the 6 full-attention layers only (10,911,744 parameters, 0.49%).
- 250 steps is small. A longer run or other settings could differ; I did not search them.
- The adapter, 42 MB, is not in git. It stays in the kernel's private output.

## Reproduce

    uv run python -m earthgym.grpo.pick                # the task, from the committed results
    uv run python -m earthgym.grpo.kernel <folder> --user <kaggle user> --preset run
    kaggle kernels push -p <folder> -t 43200           # a private kernel on Kaggle's T4 x2
    kaggle kernels output <kaggle user>/earthgym-grpo -p <dir>
    uv run python -m earthgym.grpo.report <dir>/metrics.json --name "250 steps" \
        --date 2026-11-02 --window 25 --out <report>.md
