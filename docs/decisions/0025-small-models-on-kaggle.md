# 0025: the small-model runs move to Kaggle's T4s

Date: 2026-11-02. Status: done, 2026-11-13 (session 3 below).

Context: decision 0022 ran the two small open models on this laptop's GPU. On 2026-11-02 I took that
GPU back for my own work: from then on no model runs on this machine, and every GPU job goes to
Kaggle. I stopped the laptop run then, with Qwen3.5-2B's ClimaQA done and its ERA5 at 1,280 of 5,184
samples, hours from the end. I use one Kaggle account, the one the Kaggle CLI is set up with, since
Kaggle's terms say "You also may not have, control, or operate under more than one active Kaggle
account or Kaggle User ID". Its weekly GPU allowance on 2026-11-02 (`kaggle quota`): 30 hours, 0.97
used, renewed on 2026-11-07 at 00:00 UTC. Two sessions on the T4 x2 machine of about 25 minutes each
used those 0.97 hours, so its two GPUs count once.

Decision:

- What stays as in decision 0022: the two models and their GGUF files, llama.cpp build b11960 with
  its CUDA 12.8 runtime, Inspect 0.3.286 with `openai==3.42.1` for the run, and every sampling
  setting: 8 samples an item, temperature 0.7, top_p 0.8, top_k 20, thinking off, up to 4,096 output
  tokens.
- Where: one private Kaggle kernel on the T4 x2 machine, one model a GPU, each with its own
  llama-server. A T4 has 16 GB, so each server gets 32 slots and a 131,072-token cache: the laptop's
  4,096 tokens a slot, with twice the slots. The slots set how many requests run at once, not what a
  request samples.
- The code: a git bundle of the commit in a private dataset, `earthgym-src`. The kernel clones it,
  checks the commit and builds the environment from `uv.lock` with uv 0.12.18 and Python 3.12. It
  downloads llama.cpp from the release and the GGUF files from Hugging Face at their pinned
  revisions, and checks each against its sha256 (`earthgym.kaggle.samples_kernel`,
  `tests/test_kaggle_samples.py`).
- Resuming: each model and environment is an Inspect eval set with its own log directory under
  `/kaggle/working/logs`. An eval set run again on the same directory skips a complete log and
  reruns the rest, reusing every finished sample. At 11 hours, before Kaggle stops a session at 12,
  the workers interrupt their evals, which then write their logs. Those logs go into a second
  private dataset, `earthgym-small-models-logs`, which the next session mounts.
- Results: the logs come back with `kaggle kernels output`, and the per-item results and the reports
  are made here as in decision 0022 (`earthgym.results`, `earthgym.samples`).
- The laptop's Qwen3.5-2B ClimaQA run stays out of the reports, so that every reported small-model
  run comes from one setup.

The main alternative was vLLM on the T4s, faster for batches, but Unsloth's docs say its vLLM path
does not support Qwen3.5 GRPO (decision 0024), and llama.cpp keeps the runner of decision 0022.

Consequences:

- Kaggle GPU time is now the budget, alongside the GRPO run of decision 0024. How long D takes on a
  T4 is UNKNOWN until the first session measures it. On the laptop Qwen produced about 480 tokens a
  second, and its replies run long: on ERA5 a median of 2,193 tokens, 154 of the first 426 at the
  cap.
- The kernel and its datasets are private, and the Kaggle key stays in this machine's Kaggle CLI;
  nothing in the repo or in a kernel holds it.
- `progress.jsonl` in each session's output records the GPUs, every start and end, and any server
  restart.

Session 1, 2026-11-02, from 03:50 UTC, at commit e74bb0c: it ran its 11 hours. Granite 4.0 H-1B
finished all four environments in 3.7 hours, Qwen3.5-2B ClimaQA in 51 minutes and IBTrACS in 8.4
hours; Qwen's heat stopped at the deadline with 149 samples done and 32 interrupted, and its ERA5
never started. Qwen decoded a median of 89 ms a token in each slot, and its server logged "failed to
find free space in the KV cache" and "failed to find a memory slot for batch" thousands of times: 32
sequences of up to 8,810 tokens do not fit 131,072 cache tokens, so requests waited for room. The
waits slow a run; they change no sample (every finished slot reported `truncated = 0`). Session 2,
the `qwen-rest` plan of `earthgym.kaggle.samples_kernel`, asked for 10,240 tokens a slot and got
8,192, the most the server grants this model (262,144 in all, about 3 GB of cache; its log says
"capping", and no KV message followed). It runs Qwen on both GPUs: its heat resumed from session 1's
log, then ERA5 in two parts, the first 460 items on one GPU and the last 188 after heat on the
other, each part its own eval set. Its evals run at e74bb0c too, since no task, environment or lock
has changed since.

Session 2, 2026-11-02 to 2026-11-03, the full 11 hours at commit e74bb0c: Qwen's heat and the first
460 ERA5 items finished. The last 188 ERA5 items started only after heat, on the GPU that had it,
and the deadline stopped them with 21 samples unfinished, all of the last epoch, on 21 items; the
other GPU had sat idle for its last 4.1 hours, so my split between the two was off. The report for
ERA5 left those 21 items out and said so (`reports/era5/2026-11-02-small-models.md`): Qwen3.5-2B
on 627 of the 648 items, Granite on all. The sessions and the GRPO run used the week's 30 hours
(`kaggle quota`: 30.69 used, renewed on 2026-11-07 at 00:00 UTC). Finishing those samples needs one
short resumed session after that.

Session 3, 2026-11-13, at commit e74bb0c: the same `qwen-rest` kernel with `--resume`, as version 3
of the kernel `aswanisahoo/earthgym-small-models`, mounting session 2's logs from the
`earthgym-small-models-logs` dataset. The pushes planned for the 2026-11-07 renewal never ran, since
this laptop was off at the time. Heat and the first 460 ERA5 items found their logs complete and
ended at once; the last 188 resumed and finished the 21 samples in 210 seconds (`progress.jsonl`).
The resumed log keeps the other 1,483 samples of that part as they were, row for row. It holds each
of the 21 samples twice, the errored entry of session 2 and the finished one, and Inspect
0.3.286 reads the finished one; a reader that took the first entry would see 21 errors
(`docs/reviews/2026-11-13-go-public.md`). The ERA5 report now covers all 648 items for both models:
Qwen3.5-2B's mean reward stays 0.029, and the share of items whose reward varies goes from 0.357 to
0.352.
