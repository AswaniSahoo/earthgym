"""The reward a GRPO trainer pays, from climaqa-v1's own answer contract. The Kaggle kernel
carries this file and climaqa_v1/contract.py as they are (earthgym.grpo.kernel), so training
pays exactly what the environment pays."""

from climaqa_v1 import contract


def text(completion) -> str:
    """A completion as TRL hands it to a reward function: a string, or a list of messages whose
    last one is the model's reply."""
    if isinstance(completion, str):
        return completion
    return completion[-1].get("content") or ""


def reward(completions, answer, **_) -> list[float]:
    """climaqa-v1's MCQ reward (contract.mcq_correct) for each completion against its item's
    key, called as TRL's GRPOTrainer calls a reward function: the dataset's `answer` column
    comes as a keyword argument, and the other arguments are not needed."""
    pairs = zip(completions, answer, strict=True)  # a key for every completion, or ValueError
    return [float(contract.mcq_correct(text(c), key)) for c, key in pairs]
