# 0024: a small GRPO run on climaqa-v1 MCQ, Qwen3.5-2B with a LoRA on one Kaggle T4

Date: 2026-11-02. Status: proposed, 2026-11-02: the smoke run is done; the 250-step run on
climaqa-v1 MCQ was stopped after about 26 minutes when the plan changed (the change below).

Context: Phase 7 asks whether an earthgym environment gives a small open model a signal it can
learn from: GRPO-style training on the train split, with the reward on the train and the
held-out split before and after (`docs/roadmap.md`). GRPO learns only from items whose reward
varies across a group of samples. Of the small-model runs of decision 0022, only ClimaQA has
finished. In it, Qwen3.5-2B's MCQ items vary on 93 of the 170 train items (mean reward 0.687,
67 always right) and on 18 of the 52 test items (mean 0.781, 31 always right), from
`reports/climaqa/results/2026-11-02-qwen3.5-2b-q8_0-8-samples-mcq.jsonl` split by decision
0017. This laptop's 4 GB GPU is below Unsloth's stated GRPO minimum of 5 GB and is busy with
the decision 0022 runs; Kaggle's free T4 x2 machine gives 16 GB a GPU (`docs/radar.md`,
2026-11-02).

Decision:

- Environment: climaqa-v1 MCQ, the one environment with a measured signal for this model:
  train on its train split, hold out its test split (decision 0017). The reward is the
  environment's own, `contract.mcq_correct`. `earthgym.grpo.kernel` writes the items as the
  taskset loads them, `climaqa_v1/contract.py` and the reward wrapper
  `earthgym/grpo/rollout.py` into the kernel script as the repo holds them, so training pays
  what the environment pays (`tests/test_grpo.py`).
- Model: `Qwen/Qwen3.5-2B` at 15852e8c16360a2fea060d615a32b45270f8a8fc (Apache-2.0), the model
  of decision 0022, with a LoRA of rank 16 and alpha 32 on the attention and MLP projections.
- Trainer: TRL's `GRPOTrainer` through Unsloth 2026.10.11 with its own generation
  (`fast_inference=False`), which Unsloth's docs give for Qwen3.5 since vLLM does not run it
  (the radar's trial rows).
- Settings: 8 completions of one prompt a step; sampling as in decision 0022 (temperature 0.7,
  top_p 0.8, top_k 20, thinking off), so the variance measured there applies; at most 1,024
  completion tokens, with cut-off completions left out of the loss
  (`mask_truncated_completions`); learning rate 5e-5 with a linear decay after a 10% warmup and
  `adamw_8bit`, the values of Unsloth's GRPO notebooks; seed 3407.
- Measured: the train reward at each step, from the trainer's log; and before and after
  training, 8 samples of every test item, scored by the same contract, for the mean reward,
  the items whose reward varies, pass@1 and pass@8 (`earthgym.samples`), the items that got
  better or worse with a sign test, and the replies cut at the cap (`earthgym.grpo.report`).
- Order: a smoke run of 10 steps, sampling 4 items of each split twice, to measure the step
  time, the memory and the share of cut replies; then the run itself, 250 steps, sized from the
  smoke to fit one 12-hour Kaggle session (the `run` preset of `earthgym.grpo.kernel`).

The main alternative was plain TRL with PEFT and no Unsloth: fewer moving parts, but Unsloth is
the one path with a documented Qwen3.5 GRPO run on a free T4 (the radar). It stays the fallback
if Unsloth fails in the smoke.

Out of scope: a hyperparameter search, more than one seed, other environments, full
fine-tuning and vLLM.

Consequences:

- The kernel is private and has internet for the installs and the model download. The Kaggle
  key stays in this machine's Kaggle CLI; nothing in the repo holds it.
- The smoke run (`reports/grpo/2026-11-02-smoke.md`, 1,527 s on one T4 of the two) ran end to
  end. pip resolved trl 1.15.0 from the unsloth pin, not the radar's 1.17.1; the run pins every
  version the smoke got (`PINS` in `earthgym/grpo/kernel.py`) but torch 2.11.0+cu128 and triton
  3.6.0, which are recorded; whether those came with Kaggle's image or with the install is
  UNKNOWN (pip ran quietly). Unsloth trained in float32, since the T4 has no bf16: its log
  says "Using float16 precision for qwen3_5 won't work! Using float32." Its GRPO default is
  TRL's `loss_type` dapo with beta 0, so there is no KL term. Peak memory was 5.36 GiB; the first
  step took 328 s and the median one after it 43.3 s; 5 of the 10 steps had the same reward on
  all 8 completions and so no signal; sampling took about 25 to 60 s an item for 2 samples.
- So the run samples only the test split before and after, and takes the train reward from
  the trainer's log rather than from a second sampling: at the smoke's rates, 250 steps take
  about 3 to 4 hours and the two samplings of 52 items about 2 to 4 more.
- The held-out side has little room: 31 of the 52 test items are always right before any
  training.

Change, 2026-11-02, set before any result of decision 0025: the training run follows the
small-model runs, now on Kaggle (decision 0025), and trains on the environment where they show
the most reward variance, so I stopped the run on MCQ.

- Candidates: the five tasks of those runs, for Qwen3.5-2B: climaqa MCQ, climaqa cloze,
  ibtracs-storm-v1, heat-basis-v1 and era5-forecast-v1.
- Only a task whose median reply in those runs fits the 1,024-token cap above can be trained
  here: the smoke generated about one token every 120 ms, so 8 completions of 4,096 tokens a
  step would take days.
- Of those, the one with the highest mean, over its train-split items, of the variance of each
  item's 8 rewards; a tie goes to the larger share of train items whose reward varies.
- The report gives the train and the held-out reward before and after training: 8 samples of
  every test item and of as many train items, the first ones of the train split.

