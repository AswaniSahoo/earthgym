# climaqa-v1

ClimaQA clean set v1 as a verifiers v1 taskset.

## What an item asks

One question from ClimaQA's expert-validated Gold split: 222 multiple choice and 128 cloze. The set
leaves out items found verbatim in Silver (the paper's fine-tuning set), defective items and items
that give their answer away.

The held-out split goes by item, since ClimaQA gives no source passage to group by:
`ClimaqaConfig(split="train")` loads 269 items and `split="test"` 81 (decision 0017).

## Reward

`climaqa_v1/contract.py`, the same contract the Inspect tasks use. An MCQ reply must end with a line
that is only `ANSWER: X`. A cloze reply must equal the key after SQuAD-style normalization: case,
articles and punctuation are ignored, except signs, decimal points between digits and the operators
+ / ^ = < > (decision 0016).

## How to run

From the repo root, with a model behind an OpenAI-compatible server for `vf-eval`:

    uv run vf-eval climaqa-v1 --no-push -m <model> -n 20 --env.agent.runtime.type subprocess \
      --client.base-url http://127.0.0.1:8080/v1
    uv run inspect eval src/earthgym/climaqa/tasks.py@climaqa_mcq --model <provider/model>
    uv run vf-validate climaqa-v1 --runtime.type subprocess        # the gold check
    uv run python -m earthgym.climaqa.audit                        # pinned CSVs to data/, the audit to reports/climaqa/
    uv run python -m earthgym.climaqa.clean --out environments/climaqa_v1/climaqa_v1   # rebuild the items

`ClimaqaConfig(strict=True)`, or `-T strict=true` on the Inspect tasks, runs the strict variant.

## Data and licence

Source: Rose-STL-Lab/ClimaQA at revision 3f084a0, arXiv 2410.16701. The items stay under Apache-2.0
(`climaqa_v1/LICENSE-Apache-2.0.txt`), and `climaqa_v1/NOTICE` says what changed. The code is MIT
(`LICENSE`).

## Known limits

The filter removes exact overlaps only. 21 kept items (12 MCQ, 9 cloze) are near matches of Silver
that no human has ruled on yet; their ids are in `climaqa_v1/near_matches.json`, and the strict
variant, 329 items, leaves them out.
