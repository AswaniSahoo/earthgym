"""ClimaQA clean set v1 as a verifiers v1 taskset: MCQ and cloze with exact rewards."""

import json
import re
from importlib.resources import files

import verifiers.v1 as vf

LETTERS = "ABCD"
MCQ_PROMPT = "{question}\n\n{options}\n\nAnswer with only the letter of the correct option."
CLOZE_PROMPT = (
    "Fill in the <MASK> in this climate science statement. "
    "Reply with only the missing word or phrase.\n\n{question}"
)


def mcq_reward(reply: str, key: str) -> float:
    """1.0 when the last standalone capital letter A to D in the reply is the key."""
    letters = re.findall(r"\b([A-D])\b", reply)
    return float(bool(letters) and letters[-1] == key)


def words(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.casefold()))


def cloze_reward(reply: str, key: str) -> float:
    """1.0 when the reply is the key, ignoring case and punctuation."""
    return float(words(key) != "" and words(reply) == words(key))


class ClimaqaData(vf.TaskData):
    kind: str
    answer: str
    key_text: str


class ClimaqaTask(vf.Task[ClimaqaData]):
    @vf.reward(weight=1.0)
    async def correct(self, trace: vf.Trace) -> float:
        score = mcq_reward if self.data.kind == "mcq" else cloze_reward
        return score(trace.last_reply, self.data.answer)


class ClimaqaConfig(vf.TasksetConfig):
    kinds: list[str] = ["mcq", "cloze"]


class ClimaqaTaskset(vf.Taskset[ClimaqaTask, ClimaqaConfig]):
    def load(self) -> list[ClimaqaTask]:
        lines = (
            files("climaqa_v1").joinpath("climaqa_clean_v1.jsonl").read_text("utf-8").splitlines()
        )
        rows = [json.loads(line) for line in lines]
        return [
            ClimaqaTask(self.to_data(row), self.config.task)
            for row in rows
            if row["task"] in self.config.kinds
        ]

    def to_data(self, row: dict) -> ClimaqaData:
        if row["task"] == "cloze":
            prompt = CLOZE_PROMPT.format(question=row["question"])
            return ClimaqaData(
                id=row["id"],
                prompt=prompt,
                kind="cloze",
                answer=row["answer"],
                key_text=row["answer"],
            )
        options = row["options"]  # already shuffled once, per item id, by rlenv.climaqa.clean
        listed = "\n".join(
            f"{letter}) {text}" for letter, text in zip(LETTERS, options, strict=True)
        )
        prompt = MCQ_PROMPT.format(question=row["question"], options=listed)
        return ClimaqaData(
            id=row["id"],
            prompt=prompt,
            kind="mcq",
            answer=row["answer"],
            key_text=options[LETTERS.index(row["answer"])],
        )
