# Does the reward teach a small model? GRPO on climaqa-v1 MCQ

Phase 7 of earthgym. The training ran on 2026-11-02 and 2026-11-03; the before and after samplings
ran again under one stop set on 2026-11-13, and this write-up takes its numbers from that rerun. They
come from `reports/grpo/2026-11-13-resample.md`, which re-renders from
`reports/grpo/results/2026-11-13-resample-metrics.json` (`tests/test_published_numbers.py`). The
counts of right answers and cut replies come from the per-item rows in that file. The trainer's own
log comes from the first run, `reports/grpo/2026-11-02-run.md`.

**The result: the model learned the train items, with no measurable transfer to held-out items.**
One seed, one training run.

## The question

An environment is useful for RL only if a model can learn from its reward. GRPO compares several
completions of one prompt, so it needs items whose reward varies. I fixed the rule for choosing the
task after the laptop's ClimaQA numbers and before any other small-model result (decision 0024), and
it picked climaqa-v1 MCQ: of the five tasks, it has the highest mean reward variance on its train
items, 0.0958, and its median reply fits the training cap.

## The run

Qwen3.5-2B with a LoRA of rank 16, trained by TRL's `GRPOTrainer` through Unsloth on one Kaggle T4:
250 steps of one prompt and 8 completions, 1.47 passes over the 170 train items, at most 1,024
completion tokens, with cut completions left out of the loss. Then, from the saved adapter, 8
samples of each of the 52 test items and of the first 52 train items, with the adapter disabled
(before) and enabled (after), under one stop set, `<|im_end|>` and `<|endoftext|>` (token ids
248046 and 248044), each sampling seeded, scored by the environment's own contract. All settings
are in decision 0024.

## Results

| split | items | when | mean reward | right, of 416 | replies cut | right among uncut | median reply | pass@8 |
|---|---|---|---|---|---|---|---|---|
| train | 52 | before | 0.712 | 296 | 40 | 0.785 | 380.5 | 0.904 |
| train | 52 | after | 0.844 | 351 | 7 | 0.858 | 688.5 | 0.962 |
| test | 52 | before | 0.750 | 312 | 39 | 0.828 | 353.5 | 0.904 |
| test | 52 | after | 0.774 | 322 | 25 | 0.808 | 669 | 0.885 |

- Train items: 23 better, 4 worse, 25 the same; two-sided sign test p 0.0003 (the report rounds it
  to 0.000; `earthgym.grpo.report.sign_test(23, 4)` gives 0.00031); mean item change
  +0.132 (SE 0.032).
- Held-out items: 14 better, 10 worse, 28 the same; two-sided sign test p 0.54; mean item change
  +0.024 (SE 0.035).
- In the trainer's own log, the reward averages 0.615 over the first 25 steps and 0.800 over the
  last 25. Each step is a different prompt, so that curve is noisy. 149 of the 250 steps had the
  same reward on all 8 completions and so gave no signal.

## The first samplings and the rerun

The first run sampled before and after training itself, and those two samplings did not share a
stop set. The kernel read its stop tokens from the model's generation config, which at the pinned
revision named only `<|endoftext|>`, and the trainer added `<|im_end|>` between the samplings
(`docs/reviews/phase-7-grpo.md`, H1). The kernel now fixes the stop set once from the tokenizer,
keeps the reply texts and seeds each sampling, and the `resample` preset ran the two samplings
again from the saved adapter. The first run gave:

| split | when | mean reward | replies cut | items better, worse, same | sign test p |
|---|---|---|---|---|---|
| train | before | 0.728 | 24 | 22, 5, 25 | 0.0015 |
| train | after | 0.832 | 5 | | |
| test | before | 0.740 | 39 | 12, 10, 30 | 0.83 |
| test | after | 0.750 | 19 | | |

The headline is the same both times. Under one stop set, 40 train and 39 test replies of 416 still
reach the 1,024-token cap before training, against 24 and 39 the first time. Why the first run's
replies were cut is UNKNOWN, since its reply texts were not kept. The fall in cut replies after
training, 40 to 7 on train and 39 to 25 on test, is now like for like. Besides the stop set, the two
runs differ in the sampling seed (none the first time, 3407 now), in torch (2.11.0+cu128 against
2.11.0+cu130) and python (3.13.15 against 3.13.16), and in what "before" is: a fresh, untrained LoRA
the first time, the trained adapter disabled now. How much of the change between them is chance is
UNKNOWN.

Of the 79 replies cut before training, 1 scored. If every one of them had scored, the before means
would be 0.805 on train and 0.844 on test. Train's 0.844 after still beats 0.805; on test, 0.774
after would be no gain. So both halves of the result hold under that worst case too.

## What this means

- The reward moves the policy on items it trains on: 55 more right samples of 416, and more of the
  uncut replies right.
- It does not move held-out reward by a measurable amount: 10 more right samples of 416, and the
  items that got better about match the ones that got worse.
- Replies got longer, not shorter: the median nearly doubled on both splits, and the trainer's mean
  completion length went from 473 to 671 tokens between the first and last 25 steps. Fewer replies
  reach the cap after training all the same.
- The held-out items had limited but real room: 27 of the 52 were always right before training, and
  pass@8 stood at 0.904. After training it is 0.885, with 6 items never right in 8 samples against 5
  before.

## Limits

- One seed and one training run, so the spread between runs is not measured.
- 52 items a split, 8 samples each. The sign test counts only items whose mean moved.
- The train items were seen in training, on 1.47 passes over 170 items; only 52 of the 170 were
  sampled before and after.
- ClimaQA gives no source passage to group by, so its split is by item (decision 0017). The set is
  exact-overlap-filtered, and 21 near matches of Silver remain unresolved
  (`reports/climaqa/clean_v1_manifest.json`).
- The starting point differs from the small-model run of decision 0025 (test mean 0.786): these
  samplings used float16 weights with a float32 LoRA and no autocast, under a 1,024-token cap, and
  that one the Q8_0 GGUF under 4,096.
- "Before" is the base model with the adapter disabled, not a separate load of the base weights.
- The LoRA covers every layer's MLP and the q, k, v and o projections of the 6 full-attention
  layers only (10,911,744 parameters, 0.49%).
- 250 steps is small. A longer run or other settings could differ; I did not search them.
- The adapter, 42 MB, is not in git. It is in the first kernel's private output and in the private
  Kaggle dataset `aswanisahoo/earthgym-grpo-adapter`, which the resample kernel mounts.

## Reproduce

    uv run python -m earthgym.grpo.pick                # the task, from the committed results
    uv run python -m earthgym.grpo.kernel <folder> --user <kaggle user> --preset run
    kaggle kernels push -p <folder> -t 43200           # a private kernel on Kaggle's T4 x2
    kaggle kernels output <kaggle user>/earthgym-grpo -p <dir>
    kaggle datasets create -p <dir>/adapter            # a private dataset <kaggle user>/earthgym-grpo-adapter,
                                                       # named by a dataset-metadata.json in that folder
    uv run python -m earthgym.grpo.kernel <folder2> --user <kaggle user> --preset resample
    kaggle kernels push -p <folder2> -t 43200          # mounts that dataset
    kaggle kernels output <kaggle user>/earthgym-grpo-resample -p <dir2>
    uv run python -m earthgym.grpo.report <dir2>/metrics.json \
        --name "the two samplings again, under one stop set" --date 2026-11-13 \
        --out <report>.md
