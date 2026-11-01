# climaqa-v1

ClimaQA clean set v1 as a verifiers v1 taskset: 222 MCQ and 128 cloze items from the
expert-validated Gold split, with the items found verbatim in Silver (the paper's fine-tuning set)
the defective items and the items that give their answer away removed. Source: Rose-STL-Lab/ClimaQA at revision 3f084a0, Apache-2.0,
arXiv 2410.16701.

The filter removes exact overlaps only. 21 kept items (12 MCQ, 9 cloze) are near matches of
Silver that no human has ruled on yet; their ids are in `climaqa_v1/near_matches.json`. The
strict variant leaves them out, 329 items: `ClimaqaConfig(strict=True)` in the taskset, or
`-T strict=true` on the Inspect tasks.

A held-out split by item, since ClimaQA gives no source passage to group by:
`ClimaqaConfig(split="train")` loads 269 items and `split="test"` 81 (decision 0017).

Rewards follow `climaqa_v1/contract.py`, the same contract the Inspect tasks use: an MCQ reply
must end with a line that is only `ANSWER: X`; a cloze reply must equal the key after SQuAD-style
normalization (case, articles and punctuation ignored, except signs, decimal points between
digits and the operators + / ^ = < >; decision 0016).

Regenerate the bundled file from the repo root:

    uv run python -m earthgym.climaqa.clean --out environments/climaqa_v1/climaqa_v1

Run locally without uploading anything, against an OpenAI-compatible server:

    uv run vf-eval climaqa-v1 --no-push -n 20 --env.agent.harness.id null \
      --env.agent.runtime.type subprocess --client.base_url http://127.0.0.1:8080/v1
