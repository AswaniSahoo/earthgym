# climaqa-v1

ClimaQA clean set v0 as a verifiers v1 taskset: 226 MCQ and 151 cloze items from the
expert-validated Gold split, with the items found verbatim in Silver (the paper's fine-tuning set)
and the defective items removed. Source: Rose-STL-Lab/ClimaQA at revision 3f084a0, Apache-2.0,
arXiv 2410.16701.

Rewards are exact: MCQ scores 1 when the last standalone capital letter A to D in the reply is the
key (options are shuffled per item with a fixed seed); cloze scores 1 when the reply equals the
key, ignoring case and punctuation.

Regenerate the bundled file from the repo root:

    uv run python -m rlenv.climaqa.clean --out environments/climaqa_v1/climaqa_v1

Run locally without uploading anything, against an OpenAI-compatible server:

    uv run vf-eval climaqa-v1 --no-push -n 20 --env.agent.harness.id null \
      --env.agent.runtime.type subprocess --client.base_url http://127.0.0.1:8080/v1
