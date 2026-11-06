# Phase 7 review: a small GRPO run, Qwen3.5-2B with a LoRA on climaqa-v1 MCQ, one Kaggle T4

Reviewed 2026-11-06 at commit `c435e9d` on `main`, the commit that closes decisions 0024 and
0025. While the review ran, four later commits landed (`23a33a1` to `fbfca35`, on licences, the
heat and ibtracs write-ups and the digest); none is Phase 7, none was read beyond its name, and
every file below was read with `git show c435e9d:<path>` or from a clean export of that commit.
The phase is the fifteen commits `b6b25a4` through `c435e9d`. Nothing below is taken from memory;
where a claim could not be checked it is marked UNKNOWN. No GPU was used, no model server
started, no paid call made, nothing on Kaggle started or changed, and no download over 100 MB.

What was run: on a `git archive c435e9d` export in the session scratchpad, `uv sync --locked
--all-groups` (clean), `uv run ruff check .` (clean), `uv run ruff format --check .` (201 files,
clean), `uv lock --check` (clean) and `uv run pytest -q` (425 passed, 14 skipped, 1 failed: the
bundle test runs `git rev-parse HEAD` and the export is not a repository; it passes in the live
tree and is skipped in CI's shallow clone). In the live tree, which had moved to `fbfca35`, `uv
run pytest -q` gave 440 passed and 7 failed, all in tests the four later commits touch
(`test_licences.py`, `test_ibtracs_report.py`, `test_published_numbers.py`), so they are not
Phase 7's. `gh run list`: success on every push of the phase. Read-only Kaggle calls: `kaggle
quota`, `kaggle kernels list --mine`, `kaggle datasets list --mine`, `kaggle kernels pull -m` of
the three kernels and `kaggle datasets metadata` of the two datasets, into the scratchpad. Four
scratch scripts, standard library only and importing nothing from `earthgym`: a recompute of
every number in the run report and the write-up from
`reports/grpo/results/2026-11-02-run-metrics.json`; a recompute of the four small-model reports
and of the pick from the eleven `*8-samples*.jsonl` files (the train ids dumped once from the
tasksets); a parse of the saved adapter's safetensors header; and a parse of the session-1
llama-server log. Sources read at their root: the kernel's stdout `logs/2026-11-02-grpo/
earthgym-grpo.log` and its `metrics.json` (byte-identical to the committed file), the twelve
Inspect logs under `logs/2026-11-02-small-models-kaggle-1/` and `-2/` through `inspect_ai
0.3.286`, both sessions' `progress.jsonl` and server logs, the pinned wheels of `unsloth` and
`unsloth_zoo` 2026.10.11, `trl` 1.15.0 and `transformers` 5.16.1 from PyPI, `config.json` and
`tokenizer_config.json` of `Qwen/Qwen3.5-2B` at `15852e8c` from the Hub (its
`generation_config.json` does not exist at that revision: "Entry not found"), and
kaggle.com/terms through Firecrawl. No em or en dash in any Phase 7 prose file or module.

Spot checks against the raw data:

- The run's metrics: `config` and `versions` as the run report prints them; the `train_args`
  the trainer recorded: `loss_type dapo`, `beta 0.0`, `epsilon 0.2`, `num_iterations 1`,
  `scale_rewards group`, `mask_truncated_completions True`, `shuffle_dataset True`, `fp16
  False`, `bf16 False` (the kernel passed `fp16=True`; Unsloth's patch set both False),
  `warmup_steps 0.1` (forwarded from `warmup_ratio`, log line 22), `seed 3407`. 250 steps with
  a reward, `train_runtime 15957 s`, `epoch 1.4706`, wall 27,728 s, peak 5.36 GiB.
- The curve: first 25 steps 0.615, last 25 0.800; 149 steps with `frac_reward_zero_std 1.0`,
  on exactly those 149 `grad_norm 0` and `loss 0`; clipped share 0.0445; median step 58.9 s
  after a first of 352.4 s; `learning_rate` 0 at step 1, 4.8e-05 at 25, 5e-05 at 26, 2.2e-07
  at 250. All equal the run report.
- Before and after, train (52 items, the first 52 train ids of the taskset, checked id by id;
  8 samples each, the same id sequence both times): 303 of 416 right (0.7284) then 346
  (0.8317); 24 cut then 5, none of the cut ones scored; right among uncut 0.7730 then 0.8418;
  varies 0.519 then 0.327; pass@8 0.942 then 0.962; 22 better, 5 worse, 25 same, exact
  two-sided sign test p 0.00151. Test (the 52 test ids): 308 (0.7404) then 312 (0.7500); 39
  cut then 19, of which 4 scored; right among uncut 0.8170 then 0.7758; varies 0.385 then
  0.365; pass@8 0.942 then 0.885; 12 better, 10 worse, 30 same, p 0.8318; 29 items always
  right before, 3 never right before and 6 after. 87 cut replies in all, 4 scored. All equal
  the published numbers but one cell (M1).
- The LoRA: `adapter_config.json` has `r 16`, `lora_alpha 32`, `lora_dropout 0.0`,
  `init_lora_weights true`, `peft_version 0.20.0`; the safetensors holds 192 F32 tensors and
  10,911,744 parameters, the log's "Trainable parameters = 10,911,744 of 2,224,153,408";
  `gate_proj`, `up_proj` and `down_proj` on all 24 layers, `q_proj`, `k_proj`, `v_proj` and
  `o_proj` on 6 layers only, which `config.json`'s `layer_types` explains: 18 `linear_attention`
  layers and 6 `full_attention` layers (3, 7, 11, 15, 19, 23). 43,675,104 bytes, the write-up's
  42 MB.
- The small-model reports: every cell of the four `2026-11-02-small-models.md` tables and every
  number in their Settings and cost lines (samples, output tokens, replies at the cap, replies
  without an answer, the 21 items left out) reproduce from the eleven files. The pick: climaqa
  MCQ median 382.5 tokens, 170 train items, mean variance 0.0958, varying share 0.524; cloze 3,
  99, 0.0600, 0.343; ibtracs 1,323, 233, 0.0510, 0.318; heat 3,493.5, 245, 0.0824, 0.490; ERA5
  2,426.5, 528, 0.0156, 0.362; MCQ wins with and without the cap. The Kaggle MCQ numbers of
  decision 0024: train 89 of 170 varying, mean 0.687, 67 always right; test 18 of 52, 0.786, 32.
- The twelve Inspect logs: every header says commit `e74bb0c`, `dirty False`, epochs 8. The
  three ERA5 and heat timestamps and sample counts match the results headers (ERA5 b: 1,483 of
  1,504, `cancelled`; heat session 1: `cancelled`, 181 samples in the log, 149 scored, 32
  errored by the interrupt; heat session 2: 2,400 of 2,400, and its 149 (id, epoch) pairs in
  common with session 1 carry byte-identical completions, so the resume reused them).
- `progress.jsonl`: Granite's four environments 116.7 s to 13,216.9 s (3.64 h); Qwen ClimaQA
  121.4 s to 3,191.5 s (51.2 min); IBTrACS to 33,341.9 s (8.37 h); heat interrupted at the
  deadline; ERA5 "not started, past the deadline". Session 2: ERA5 part a ended at 24,748.6 s,
  the deadline at 39,608.9 s, 4.13 h idle; part b interrupted. Both sessions `begin` at
  `e74bb0c`.
- The session-1 Qwen server log: "failed to find free space in the KV cache" 3,311 times,
  "failed to find a memory slot for batch" 3,412 times, 8,611 `truncated = 0` and no
  `truncated` of another value, the largest `n_past` 8,810, 5,349 decode records with a median
  of 89.2 ms a token and a mean of 98.7 (the decision's "about 91"). `n_ctx_slot = 131072`.
- Kaggle: `earthgym-grpo`, `earthgym-grpo-smoke` and `earthgym-small-models` all `is_private
  true`, `enable_internet true`, `NvidiaTeslaT4`; `earthgym-src` and `earthgym-small-models-logs`
  `isPrivate true`. `kaggle quota`: GPU 30.69 h used of 30.00, refresh 2026-11-07T00:00:00.
  `kaggle kernels push -t` exists ("Limit the run time of a kernel"). `git grep` finds no
  Kaggle key, token or `kaggle.json` in the tree; no kernel folder, `train.py`, `run.py` or
  bundle is committed; the username appears once, in `pyproject.toml`.
- Git order: `73cee49` (the rule) is authored and committed 2026-11-02 09:22:06 +0530, 03:52
  UTC, two minutes after session 1 began (03:50 UTC) and 52 minutes before Qwen's Kaggle MCQ log
  completed (04:44 UTC); `f75bc3b` (the results) and `451d0f9` (the pick) at 22:26:11 +0530,
  16:56 UTC. Author and committer dates agree on every commit.
- kaggle.com/terms, line 29 of the scraped text, holds the sentence decision 0025 quotes, word
  for word.

## 1. Ratings

| Area | Score | Justification |
|---|---|---|
| Correctness | 6 | The report code is right: every number `report.py` renders reproduces, the sign test is the exact doubled binomial tail, `compare` refuses mismatched item sets, the reward wrapper is the contract's own rule, and the small-model pipeline and the pick reproduce to the last digit. Against that: the kernel's two samplings did not stop on the same tokens, since `sample()` reads `model.generation_config.eos_token_id` on each call and the trainer rewrote it in between (H1), which is the one thing the comparison must hold fixed; and one hand-computed cell of the write-up's table is wrong (M1). |
| Minimalism and clarity | 8 | Standard library plus the pins the run needs; the kernel is a template with four constants filled from the repo, so the environment's contract trains what it scores; `report.py` is 160 lines, `pick.py` 86, `rollout.py` 21. Clutter is small: `constants()` is duplicated in two test files, and `samples.py` carries the ClimaQA strict variant inside a generic renderer. |
| Test coverage | 5 | Each pure function has a test that fails without it (the reward rule, the items, the private metadata, the pins, the curve, the item-by-item comparison, the pick and its cap, `finished` and the left-out count, every report re-rendered byte for byte). But the two scripts that ran on Kaggle, `train_kernel.py` and `samples_job.py`, are only compiled (`tests/test_grpo.py:55`, `tests/test_kaggle_samples.py:82`): `sample()`'s stop set, the cut flag, the before and after symmetry, `fetch`'s sha256 refusal and the deadline interrupt have no test, and H1 lives there. |
| Reproducibility | 7 | `metrics.json` is committed and identical to the kernel's output; the run and smoke reports re-render by test; the model revision, the adapter config and nine package pins are recorded; every small-model log says `e74bb0c` clean and the binaries and GGUFs are sha256-checked. Gaps: the samplings are unseeded (L5); the sampled reply texts were not saved, so H1 cannot be settled from the record; torch and triton came from the image or the install, UNKNOWN as stated; the adapter stays in a private kernel output. |
| CI/CD | 7 | Green on all eight pushes of the phase, actions pinned by commit, `--locked --all-groups`, the published-numbers test covers both GRPO reports and the four small-model reports. CI runs nothing of the two Kaggle scripts beyond `compile`. The scheduled `reproduce` workflow has been red since 2026-11-02 12:19 UTC: `earthgym.heat.data` refuses a new NCEI build of USW00023183 (sha256 3a32b0b4...), not a Phase 7 change, but the dashboard the phase sits on. |
| Research rigor | 5 | The task was picked by a written rule, the test is paired and exact, one seed is stated as one seed, and the Limits name the split, the overlap filter and the cap. Against that: the before and after samplings differ in their stop set and the write-up calls them "the same settings" (H1); the replies nearly doubled in length after training and nothing says so (M2); the precision sentences do not match the record (M3); the rule was fixed after the laptop's MCQ and cloze numbers were known (L6); and no interval accompanies "no measurable transfer" (L7). |
| Readiness to publish | 4 | The kernel, the reports and the small-model evidence are sound. Not yet: the "learned to finish" finding cannot be separated from H1 until both samplings are redone under one stop set (the saved adapter makes that a sampling job, not a training job); the 0.786 cell; the float32 sentences; `README.md:19` says Phase 7 is "in progress" and `SUMMARY.md:3` says "six phases" (M4). |

## 2. Plain answers to the checks asked

**The run's numbers, recomputed without `report.py`.** All reproduce (the spot checks above):
the four means, the right counts (303, 346, 308, 312), the cut counts (24, 5, 39, 19), three of
the four "right among uncut" cells, both pass@8 columns, the better, worse and same counts, both
p values (0.00151, which the decision prints as 0.0015 and the report as 0.002; 0.832), the
curve's 0.615 and 0.800, the 149 no-signal steps, "4 of these 87 scored", "29 of the 52 were
always right", "6 items never right ... against 3", "43 more right samples", "4 more right
samples", 1.47 passes, 42 MB, 27,728 s. One cell does not: the test split's "right among uncut"
after training is 308 of 397, 0.776, not 0.786 (M1).

**Is the reading supported?** "Learned the train items": yes, and it survives the worst case of
H1. Even if all 24 cut train replies before training had scored (they are the only replies H1
can have hurt, since every cut reply before training had no parseable answer), the before mean
would be at most 0.786 against 0.832 after; the paired interval on the 52 item means is +0.103
[0.041, 0.165] (t with 51 degrees of freedom). "No measurable transfer": yes, +0.010 [-0.045,
0.064] on the test items, and under H1's worst case (39 cut test replies, before mean at most
0.834) the sign would even turn. "Part of the gain is that the model learned to finish": not
separable from H1, because the fall in cut replies is exactly the quantity the changed stop set
moves, in the direction observed (section 3, H1). Left out: the replies got much longer, not
shorter, after training (M2); the base weights were float16 throughout, not float32 (M3); the
first 52 train items are easier than the other 118 (0.719 against 0.673 in the 0025 run), which
does not bias the paired comparison but is worth a clause.

**Is the sign test the right test, and did the run compute what it says?** The sign test is a
valid exact paired test on the direction of each item's change; it drops ties (25 and 30 items)
and ignores magnitude, so it is conservative, and the paired t on the item means agrees with it
on both splits. It should be reported with an interval (L7). The same items were sampled before
and after, in the same order, 8 times each, by the same `sample()` under the same temperature,
top_p, top_k, cap and `enable_thinking False`, and scored by the environment's own
`contract.mcq_correct` (the kernel writes `contract.py` into the script, `tests/test_grpo.py:57`;
the trainer's reward is `rollout.reward`, the same rule). What was not the same is the set of
tokens on which generation stops and the cut flag is judged (H1). The reward during training is
the environment's own: the log's `rewards/reward/mean` is 0.125, 1, 0.125, 0.75 on the first
four steps, a multiple of 1/8 each, as 8 MCQ rewards give.

**Did GRPO train?** Yes. 250 logged steps, each one prompt and 8 completions
(`per_device_train_batch_size 8`, `num_generations 8`, `generation_batch_size 8`,
`steps_per_generation 1`, `num_iterations 1`), "Num examples = 170 | Num Epochs = 2 | Total
steps = 250" in the log; 101 steps with a nonzero loss and a grad norm up to 1.59, 149 with
none; the schedule warms up over 25 steps and decays linearly; `mask_truncated_completions
True`; DAPO loss with `beta 0`, so no reference model and no KL (the `kl` column is 0 on every
step, as `beta 0` gives). The adapter saved at the end has nonzero B matrices (its tensors are
not all zero, since the file is 43.7 MB of F32 and the train reward moved), and its config
records the LoRA as trained. The precision: `unsloth_zoo/model_lists.py:36` lists `qwen3_5` in
`FORCE_FLOAT32` ("GDN layers NaN on fp16"); `unsloth/models/vision.py:3744` says "Forced float32
loads in bfloat16 then casts to float16", which is why both runs' `loaded` event says
`torch.float16`; `unsloth/models/rl.py:2655-2665` then sets `args.fp16 = False`, `args.bf16 =
False`, `mixed_precision = 'no'` and prints the line the log shows at 4,885 s. So: base weights
in float16, the LoRA in float32 (the adapter's dtype), the training arithmetic without autocast.

**Does `for_inference` leave the LoRA active, and is "before" the base model?**
`unsloth/models/vision.py:5630-5660` (`FastBaseModel.for_inference`, the class `loader.py:2207`
dispatches to) sets `training False`, turns gradient checkpointing off and sets a generation
flag on each module; it never touches the adapters, so the after sampling is the trained policy.
`for_training` (5676-5701) reverses it. Before training the LoRA contributes nothing:
`init_lora_weights true` (B is zero) and `lora_dropout 0.0`, so the before sampling is the base
model in float16, up to the float32 LoRA path adding zeros. One more thing the trainer changed
between the two samplings is the stop set (H1); nothing else in `run()` differs between the two
`evaluate` calls (`train_kernel.py:153-160`).

**The pick.** Decision 0024's rule (`73cee49`, 03:52 UTC) predates every Kaggle result (the
first, Qwen's cloze, completed 04:04 UTC; the results commit is 16:56 UTC), and `pick.py`
implements it as written: the cap on the median reply, then the mean population variance over
train items, then the varying share. Its five numbers reproduce, and MCQ wins uncapped too, so
the cap decided nothing. What the rule could not be blind to: the decision itself says that when
it was set, only the laptop's ClimaQA run had finished, with MCQ varying on 93 of 170 train items
against cloze's 29 of 99 (`docs/radar.md:58`), and ERA5's long replies were known
(`0025:52-54`); the length cap, justified by the smoke's 120 ms a token, was always going to
exclude the three tasks whose numbers were unknown. So the rule was fixed before the Kaggle
results, as the write-up says, but after MCQ was known to beat cloze; I found no sign of fitting
after `f75bc3b`, and the test `test_the_grpo_pick_is_climaqa_mcq_on_all_five_tasks_of_the_
committed_results` pins the outcome (L6).

**The small-model runs.** Every report number reproduces (spot checks). Session 1 and 2 ran at
`e74bb0c`, clean, in all twelve logs. The 21 unfinished ERA5 samples are all epoch 8, on 21
distinct items, all `2m_temperature` (the b part is the last 188 items of the records, all
`2m_temperature`), spread through the part (positions 3 to 181), the ones whose eighth sample
was in flight at the interrupt. `samples.finished` (`samples.py:51-57`) drops an item only when
the file's header carries a status, and drops the whole item rather than scoring the missing
sample 0, which is right. The selection effect is small and towards a worse model: the 21
items' 147 finished samples average 0.0147 against 0.0226 for the other b items, and keeping
them with 7 samples would move Qwen's ERA5 mean from 0.0290 to 0.0289. The structural effect is
that Qwen's per-variable row for `2m_temperature` rests on 167 items where Granite's rests on
188, and the two models' overall rows are over different item sets (627 against 648), which the
report's last line says. Decision 0025's "181 samples done" for session 1's heat is the log's
sample count; 149 were scored and 32 were cut by the interrupt (L3), and session 2 reused the
149. Session 2's "10,240 tokens a slot" was asked for and not granted: llama-server capped the
pool at the model's training context (L2).

**Kaggle and secrets.** All three kernels and both datasets are private by Kaggle's own
metadata, the kernel builders write `is_private True` and the tests assert it, the dataset
metadata carries no `isPrivate` key and the CLI's default is private (asserted in
`test_the_source_dataset_is_a_bundle_of_the_commit_and_private_by_default`). No key, token or
credentials file is in the tree; the kernels read the Hub unauthenticated (log line 2).

**Every claim in decisions 0024 and 0025 and the write-up.** Supported, checked at the source:
the model revision, LoRA rank and alpha; the trainer, its loss type and beta; the sampling
settings; the pins and the two unpinned packages marked UNKNOWN; peak 5.36 GiB, first step 328
s, median 43.3 s, 5 of 10 steps without signal, "about 25 to 60 s an item" (22 to 60 in the
smoke events) and 1,527 s; the 3 to 4 hour and 1 to 3 hour projections (actual: 4.4 h of
training, 1.3 h and 1.9 h of sampling); the Kaggle MCQ numbers (89, 0.687, 67, 18, 0.786, 32);
the five pick numbers; the result paragraph's numbers; Granite's 3.7 h, Qwen's 51 min and 8.4
h, the heat interrupt, ERA5 not started; the two server messages "thousands of times", 8,810
tokens, `truncated = 0`, "about 91 ms a token"; the 460 and 188 split; part a done, 21 samples
of the last epoch on 21 items, 4.1 idle hours, 627 of 648; `kaggle quota` 30.69; the terms
sentence; the radar's 5 GB, trl 1.17.1 against the `trl<=1.15.0` pin, the T4's 16 GB.
Not supported by the cited record: "the model learned to finish" as a separate finding (H1);
"sampled the full weights in float32" (write-up 66) and "Unsloth trained in float32" (0024:60),
since the `loaded` event of both runs says `torch.float16` and Unsloth's source says the forced
path loads bfloat16 and casts to float16 (M3); "0.786" (write-up 51 and 34, M1); "on the
attention and MLP projections" (0024:27), true of 6 of 24 layers for attention (L1); "gives
each slot 10,240 tokens" (0025:61, L2); "181 samples done" (0025:56, L3); "since vLLM does not
run it" (0024:29) and "among the models vLLM does not run" (0025:40), where the radar it cites
(`docs/radar.md:58`) records that vLLM's model list has `Qwen3_5ForConditionalGeneration` and
that Unsloth's docs say GRPO works "if you disable fast vLLM inference" (L4). The laptop figures
of 0024 (93 of 170, 0.781, 31) rest on a file that is deliberately not in the repository, so
they are UNKNOWN here; the write-up uses the run's own 29.

**The tests.** Each new test fails without the code it covers: the reward test needs
`rollout.reward` and its `strict=True` zip; the items test needs `kernel.items` in taskset
order; the kernel test needs `write`, `metadata` and the four constants; the preset test pins
the nine pins and the six fields the run changes; the report tests pin the curve, the no-signal
count, the median after the first step, the item-by-item counts and p 0.5, and the rendered
lines; the pick tests pin the cap, the tie and the empty case; the Kaggle tests pin the two
models' revisions and hashes, the Inspect flags, the slot arithmetic, the private metadata, the
bundle and the `qwen-rest` split; `test_main_leaves_out_the_items_a_stopped_run_did_not_finish`
fails without `finished`. Untested: everything in `train_kernel.py` and `samples_job.py` beyond
`compile`, in particular `sample()`'s stop set and cut flag (H1, M5); `compare`'s "not of the
same items" error; `sign_test` on a tie and on zero moves; `_event`'s UNKNOWN fallback;
`kernel.script`'s placeholder error; `samples_kernel.plan` on an unknown name; `fetch`'s sha256
refusal; the deadline interrupt.

## 3. Issues by severity

### High

- **H1. The before and after samplings stopped on different tokens, and the cut counts the
  write-up interprets are judged on different tokens.** `train_kernel.py:75-76` builds the stop
  set from `model.generation_config.eos_token_id` on every call of `sample()`, and lines 97 and
  106 use that set to end the decoded reply and to flag a reply as cut. At the before sampling
  (lines 153-162, before `GRPOTrainer` exists) that attribute came from `config.json`, since the
  revision ships no `generation_config.json`: `text_config.eos_token_id` is 248044,
  `<|endoftext|>`, and `transformers/generation/configuration_utils.py:1285-1288` takes the
  generation attributes from `text_config` when the top level has none. The chat template ends
  an assistant turn with `<|im_end|>`, 248046 (`tokenizer_config.json`), which was not in that
  set. At trainer construction, after both before samplings, `transformers/trainer_utils.py:
  1196-1214` turned the int into a list and set `model.generation_config.eos_token_id` to
  `[248046, 248044]`; the log records it at 4,886 s: "The tokenizer has new PAD/BOS/EOS tokens
  ... Updated tokens: {'eos_token_id': 248046}." So before training a reply did not stop at
  `<|im_end|>` and was cut if `<|endoftext|>` did not arrive within 1,024 tokens; after
  training it stopped at either. Any text the model emitted after `<|im_end|>` before training
  went into the decoded reply, and `contract.py:40-42` scores the last non-empty line only, so
  such a reply scores 0 whatever it answered. The run report's "Each item sampled 8 times with
  the same settings" (`report.py:118`) and the write-up's "learned to finish" (48-51) and
  decision 0024:98-99 treat the fall in cut replies as the policy's doing. How much of it is the
  stop set is UNKNOWN: the reply texts were not kept (`sample()` stores answer, reward, tokens
  and cut), and every cut reply before training had no parseable answer, as both mechanisms
  predict. The bounds in section 2 hold: the before cut shares (5.8% train, 9.4% test) sit at
  or below the 10.2% of MCQ replies that ran past 1,024 tokens in the 0025 run under a 4,096
  cap, so the artifact is not large, the train gain survives its worst case, and the test
  conclusion does too; the finishing claim does not. Smallest fix, test-first: in `sample()`
  take the stop set once from the tokenizer (`{tokenizer.eos_token_id, tokenizer.pad_token_id}`,
  248046 and 248044) and pass it as `eos_token_id` to `generate`, keep each reply's text in its
  row, and add a stub-model test that a reply ending in `<|im_end|>` is neither cut nor
  extended; then rerun the two samplings only, with the saved adapter disabled
  (`model.disable_adapter()`) and enabled, about 3 hours of one T4 at the run's rates, and
  rewrite the finishing sentence from what comes back.

### Medium

- **M1. One published cell is wrong.** `reports/grpo/2026-11-02-phase-7-writeup.md:34` prints
  0.786 for the test split's "right among uncut" after training and line 51 repeats it. 312
  right of 416 and 19 cut, but 4 of the cut replies scored (the write-up's own "4 of these 87
  scored", all four in this cell), so right among uncut is 308 of 397, 0.776. The other three
  cells have no scored cut reply and are right. The column is computed by hand, outside
  `report.py`, so `test_published_numbers.py` cannot catch it. Smallest fix: compute `right`,
  `right_uncut` and the share in `report.compare` and render them, so the write-up copies a
  tested number; correct both lines (the sentence's direction is unchanged, and stronger).
- **M2. The replies nearly doubled in length after training, and nothing says so.** In the
  samplings the median reply went from 369 to 681 tokens on train and from 356 to 675 on test
  (means 417 to 685 and 429 to 678); in the trainer's log `completions/mean_length` averages
  473.5 over the first 25 steps and 671.2 over the last 25, and `completions/min_length` 293.3
  to 586.4, so by the end almost no completion was short. That is the most visible change in
  the policy, it is consistent with the DAPO loss's token-level normalisation (my reading, not
  tested), and it bears on "learned to finish": a model whose replies grew by 300 tokens and
  were cut less often did not learn brevity. The write-up's Results and What this means (27-54)
  have no length figure. Smallest fix: a length column in the before and after table (the
  rows carry `tokens`) and the per-block mean length in the curve table (`log_history` carries
  it), one sentence in the write-up.
- **M3. The precision sentences do not match the record.** Write-up 65-66: "this run sampled the
  full weights in float32"; decision 0024:60-62: "Unsloth trained in float32, since the T4 has
  no bf16". Both runs' `loaded` event says `dtype torch.float16` (`metrics.json`, log line 18);
  `unsloth/models/vision.py:3744-3747`: "Forced float32 loads in bfloat16 then casts to
  float16"; `rl.py:2655-2665` sets `fp16` and `bf16` False (the recorded `train_args`); the
  adapter is F32. What the run did: float16 base weights, a float32 LoRA, no mixed-precision
  autocast. The write-up's comparison with the Q8_0 GGUF run stands (different weights, cap and
  runner) but names the wrong dtype. Smallest fix: "the float16 weights with a float32 LoRA and
  no autocast" in both places.
- **M4. The repository's own records are behind the phase at c435e9d.** `README.md:19`: Phase 7
  "in progress: the smoke run is done ... the 250-step run next"; `SUMMARY.md:3`: "built in six
  phases", with no Phase 7 section; `docs/roadmap.md` names the 21 ERA5 samples but no Phase 7
  follow-up. `docs/log.md:5-16` is current. Smallest fix: one README row with the result as the
  write-up states it, a Phase 7 section in the summary, and the H1 rerun on the roadmap. (Edits
  to the README and docs were landing while this review ran; this is their state at c435e9d.)
- **M5. The two Kaggle scripts have no test beyond `compile`.** `tests/test_grpo.py:55` and
  `tests/test_kaggle_samples.py:82` compile `train.py` and `run.py`; nothing exercises
  `sample()` (`train_kernel.py:69-109`), `evaluate` (153-160), `fetch`'s refusal
  (`samples_job.py:41-50`) or the deadline interrupt (142-149). H1 is the cost. Smallest fix: a
  stub model and tokenizer for `sample()` (a `generate` that returns fixed ids with `<|im_end|>`
  and padding) asserting the stop set, the reply text, the token count and the cut flag; an
  `evaluate` test that the two calls see one stop set; a `fetch` test with a wrong sha256 on a
  temp file.

### Low

- **L1.** `docs/decisions/0024-small-grpo-run.md:27`: "on the attention and MLP projections".
  The adapter holds q, k, v and o projections for the 6 full-attention layers only; the 18
  Gated DeltaNet layers have no `q_proj` to match, and the log warned "adapters attach only
  where both select". Fix: "on every layer's MLP and on the 6 full-attention layers' q, k, v and
  o (10,911,744 parameters, 0.49%)".
- **L2.** `docs/decisions/0025-small-models-on-kaggle.md:61`, `samples_kernel.py:122, 145-146`
  and `tests/test_kaggle_samples.py:129-130`: session 2 asked for `-c 327680`, and the server
  log says "the slot context (327680) exceeds the training context of the model (262144) -
  capping", then `n_ctx_slot = 262144`, both servers. So the pool was 262,144, 8,192 a slot on
  average, not 10,240; no KV message followed, so the run was unaffected. Fix: say what the
  server granted, and request 262144 or less in the plan.
- **L3.** `0025:56`: "with 181 samples done". The log holds 181 samples, 149 scored and 32
  errored by the interrupt; session 2 reused the 149. Fix: "149 done and 32 interrupted".
- **L4.** `0024:29` and `0025:40` say vLLM does not run Qwen3.5. `docs/radar.md:58` records
  vLLM's supported list has `Qwen3_5ForConditionalGeneration` and that Unsloth's docs say GRPO
  works "if you disable fast vLLM inference and use Unsloth inference instead". Fix: "Unsloth's
  vLLM path does not support Qwen3.5 GRPO".
- **L5.** The samplings are unseeded: `sample()` passes no generator, the before sampling runs
  before anything seeds torch, and the trainer's `set_seed(3407)` at construction seeds the
  process before the after sampling. Not a bias, but "seed 3407" (0024:35) covers the LoRA
  init and training only. Fix: `torch.manual_seed` before each `evaluate`, and say so.
- **L6.** Write-up 14-15: "I fixed the rule for choosing the task before the small-model runs
  reported". True of the Kaggle runs; the decision itself (10-13) says MCQ's and cloze's laptop
  variance were known when the rule was set, and the cap excluded the three unknown tasks. Fix:
  one clause, "after the laptop's ClimaQA numbers and before any other".
- **L7.** `report.compare` gives counts and a sign test and no interval. The paired t on the 52
  item means: train +0.103 [0.041, 0.165], test +0.010 [-0.045, 0.064]. "No measurable
  transfer" is right; a reader wants to see what size of transfer the run could not see. Fix:
  the mean item difference with its standard error in `compare`, one more cell in the table.
- **L8.** `pick.stats` (`pick.py:23`) takes the median reply over all of a task's items and the
  variance over train items only; decision 0024:76-78 says "median reply in those runs" and
  "over its train-split items", so the code matches the words, but the two populations differ
  and the pick paragraph does not say so. Over train items only the medians are 394, 3,
  1,306.5, 3,541 and 2,326, the same verdict. Fix: a clause.
- **L9.** `0025:57`: "about 91 ms a token". The 5,349 decode records give a median of 89.2 ms
  and a mean of 98.7; which statistic 91 is, is unstated. Fix: say the median, 89.
- **L10.** The scheduled `reproduce` workflow fails since 2026-11-02 12:19 UTC in `heat`:
  "NCEI now serves another build of USW00023183: sha256 3a32b0b4cc3889cc9b8643ce72449c8a0697
  d2223fbc40238f76f9621eb882ae". Not this phase's change, but a red check on the repository.
  Fix: decide in decision 0018's terms whether to repin or to keep the archived copy as the
  reference, and record it.
- **L11 (nit).** `constants()` is defined twice (`tests/test_grpo.py:33`,
  `tests/test_kaggle_samples.py:65`); the `tokens` field of a sampled row is the count up to the
  first stop token, so for a cut reply it is always 1,024 and the field says nothing the flag
  does not.

## 4. What is missing to close Phase 7

- H1 settled test-first: the stop set fixed and tested, the reply texts kept, the two samplings
  rerun with and without the saved adapter under one stop set, and the finishing sentence,
  decision 0024's result paragraph and the run report rewritten from that rerun. This is a
  sampling job on the kernel's saved output, not a new training run.
- M1 to M5: the uncut share computed in `report.py` and corrected in the write-up, the length
  figures added, the precision sentences corrected, the README, summary and roadmap brought up
  to the phase, and the kernel scripts given tests.
- L1 to L9, one sentence each, in the two decisions and the write-up.
- The 21 ERA5 samples (decision 0025's own open item) after the 2026-11-07 renewal, so Qwen's
  ERA5 row covers the same 648 items as Granite's.

## 5. What I would not publish yet, and why

- The write-up's "The model also learned to finish" bullet (48-51) and decision 0024's "so part
  of the gain is that the model learned to finish" (98-99), until the rerun under one stop set
  says whether the cut replies before training were the policy's or the stop set's (H1).
- The write-up's table and the sentence that carry 0.786 (34, 51), until they say 0.776 (M1).
- "sampled the full weights in float32" and "Unsloth trained in float32" (M3), since the record
  says float16 weights.
- `README.md:19` and `SUMMARY.md` as they stand at c435e9d, which say the run has not happened
  (M4).
- The headline "learned the train items, with no measurable transfer" can be published as it is:
  both halves hold under the worst case of H1, and the Limits say one seed and 52 items a split.
