# 0024: a small GRPO run on climaqa-v1 MCQ, Qwen3.5-2B with a LoRA on one Kaggle T4

Date: 2026-11-02. Status: open, 2026-11-06: the 250-step run finished and
`reports/grpo/2026-11-02-phase-7-writeup.md` reports it, but its two samplings did not share a stop
set, so they run again (the rerun below). A first attempt was stopped after about 26 minutes when
the plan changed (the change below).

Context: Phase 7 asks whether an earthgym environment gives a small open model a signal it can learn
from: GRPO-style training on the train split, with the reward on the train and the held-out split
before and after (`docs/roadmap.md`). GRPO learns only from items whose reward varies across a group
of samples. When I planned this, only Qwen3.5-2B's ClimaQA run on the laptop had finished: its MCQ
items varied on 93 of the 170 train items (mean reward 0.687, 67 always right) and on 18 of the 52
test items (mean 0.781, 31 always right), split by decision
0017. Decision 0025 reran it on Kaggle, and that run's file, the one under
      `reports/climaqa/results/`, gives 89 of 170 (0.687, 67) and 18 of 52 (0.786, 32). The laptop's
      4 GB GPU was below Unsloth's stated GRPO minimum of 5 GB and busy with the decision 0022 runs;
      Kaggle's free T4 x2 machine gives 16 GB a GPU (`docs/radar.md`, 2026-11-02).

Decision:

- Environment: climaqa-v1 MCQ, the one environment with a measured signal for this model: train on
  its train split, hold out its test split (decision 0017). The reward is the environment's own,
  `contract.mcq_correct`. `earthgym.grpo.kernel` writes the items as the taskset loads them,
  `climaqa_v1/contract.py` and the reward wrapper `earthgym/grpo/rollout.py` into the kernel script
  as the repo holds them, so training pays what the environment pays (`tests/test_grpo.py`).
- Model: `Qwen/Qwen3.5-2B` at 15852e8c16360a2fea060d615a32b45270f8a8fc (Apache-2.0), the model of
  decision 0022, with a LoRA of rank 16 and alpha 32 on every layer's MLP and on the q, k, v and o
  projections of the 6 full-attention layers (10,911,744 parameters, 0.49%).
- Trainer: TRL's `GRPOTrainer` through Unsloth 2026.10.11 with its own generation
  (`fast_inference=False`), which Unsloth's docs give for Qwen3.5 GRPO (the radar's trial rows).
- Settings: 8 completions of one prompt a step; sampling as in decision 0022 (temperature 0.7, top_p
  0.8, top_k 20, thinking off), so the variance measured there applies; at most 1,024 completion
  tokens, with cut-off completions left out of the loss (`mask_truncated_completions`); learning
  rate 5e-5 with a linear decay after a 10% warmup and `adamw_8bit`, the values of Unsloth's GRPO
  notebooks; seed 3407.
- Measured: the train reward at each step, from the trainer's log; and before and after training, 8
  samples of every test item and of the first 52 train items, scored by the same contract, for the
  mean reward, the items whose reward varies, pass@1 and pass@8 (`earthgym.samples`), the items that
  got better or worse with a sign test, and the replies cut at the cap (`earthgym.grpo.report`).
- Order: a smoke run of 10 steps, sampling 4 items of each split twice, to measure the step time,
  the memory and the share of cut replies; then the run itself, 250 steps, sized from the smoke to
  fit one 12-hour Kaggle session (the `run` preset of `earthgym.grpo.kernel`).

The main alternative was plain TRL with PEFT and no Unsloth: fewer moving parts, but Unsloth is the
one path with a documented Qwen3.5 GRPO run on a free T4 (the radar). It stays the fallback if
Unsloth fails in the smoke.

Out of scope: a hyperparameter search, more than one seed, other environments, full fine-tuning and
vLLM.

Consequences:

- The kernel is private and has internet for the installs and the model download. The Kaggle key
  stays in this machine's Kaggle CLI; nothing in the repo holds it.
- The smoke run (`reports/grpo/2026-11-02-smoke.md`, 1,527 s on one T4 of the two) ran end to end.
  pip resolved trl 1.15.0 from the unsloth pin, not the radar's 1.17.1; the run pins every version
  the smoke got (`PINS` in `earthgym/grpo/kernel.py`) but torch 2.11.0+cu128 and triton 3.6.0, which
  are recorded; whether those came with Kaggle's image or with the install is UNKNOWN (pip ran
  quietly). The T4 has no bf16, and Unsloth's log says "Using float16 precision for qwen3_5 won't
  work! Using float32.": in the run that meant float16 base weights, a float32 LoRA and no autocast
  (`docs/reviews/phase-7-grpo.md`, M3). Its GRPO default is TRL's `loss_type` dapo with beta 0, so
  there is no KL term. Peak memory was 5.36 GiB; the first step took 328 s and the median one after
  it 43.3 s; 5 of the 10 steps had the same reward on all 8 completions and so no signal; sampling
  took about 25 to 60 s an item for 2 samples.
- At the smoke's rates, 250 steps take about 3 to 4 hours, and each sampling of 104 items (52 test,
  52 train) 1 to 3 more, before and after, which fits one 12-hour session.
- The held-out side has little room: 31 of the 52 test items are always right before any training.

Change, 2026-11-02, set before any result of decision 0025: the training run follows the small-model
runs, now on Kaggle (decision 0025), and trains on the environment where they show the most reward
variance, so I stopped the run on MCQ.

- Candidates: the five tasks of those runs, for Qwen3.5-2B: climaqa MCQ, climaqa cloze,
  ibtracs-storm-v1, heat-basis-v1 and era5-forecast-v1.
- Only a task whose median reply in those runs fits the 1,024-token cap above can be trained here:
  the smoke generated about one token every 120 ms, so 8 completions of 4,096 tokens a step would
  take days.
- Of those, the one with the highest mean, over its train-split items, of the variance of each
  item's 8 rewards; a tie goes to the larger share of train items whose reward varies.
- The report gives the train and the held-out reward before and after training: 8 samples of every
  test item and of as many train items, the first ones of the train split.

The pick, 2026-11-02 (`uv run python -m earthgym.grpo.pick`, from the committed results of decision
0025): climaqa MCQ. Its median reply is 382.5 tokens, and its 170 train items have a mean reward
variance of 0.0958, with 0.524 of them varying. Cloze fits the cap (median 3 tokens) but has 0.0600
and 0.343 on its 99 train items. ibtracs-storm-v1 is out on length, a median of 1,323 tokens (0.0510
and 0.318 on 233 train items). When I made the pick the heat and ERA5 runs of Qwen3.5-2B had not
finished. Now that they have, they are out on length too and lower anyway: heat a median of 3,493.5
tokens (0.0824 and 0.490 on 245 train items), ERA5 2,452 (0.0154 and 0.357 on its 546 train items,
since the resumed session of 2026-11-13; 2,426.5, 0.0156 and 0.362 on the 528 that had finished
before). So climaqa MCQ has the highest variance of the five
with or without the length rule (`tests/test_published_numbers.py`). The medians are over all of a
task's items and the variances over its train items; train items alone give the same verdict. The
run is the `run` preset of `earthgym.grpo.kernel`.

The result (`reports/grpo/2026-11-02-run.md`): the model learned the train items, with no measurable
transfer. On the first 52 train items the mean reward went from 0.728 to 0.832 (22 items better, 5
worse, 25 the same, two-sided sign test p 0.0015), on the 52 test items from 0.740 to 0.750 (12, 10,
30, p 0.83). One seed. Replies cut at the cap fell from 24 to 5 on train and from 39 to 19 on test,
but those counts are not like for like (the rerun below).

The rerun, 2026-11-06. The review of this phase found that the two samplings stopped on different
tokens: `sample()` read them from the model's generation config, which named only `<|endoftext|>`,
and the trainer added `<|im_end|>` between the samplings (`docs/reviews/phase-7-grpo.md`, H1). The
headline holds under the worst case of that flaw, and the reading of the cut replies does not. The
kernel now fixes the stop set once from the tokenizer, keeps the reply texts in its output and seeds
each sampling (`tests/test_grpo.py`). The `resample` preset runs only the two samplings from the
saved adapter, disabled for "before" and enabled for "after", after the Kaggle allowance renews on
2026-11-07. The run's numbers then get replaced in the write-up, and this decision closes.

