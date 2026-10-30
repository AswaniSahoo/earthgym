"""One answer contract for the ERA5 forecast tasks: the answer line and the reward (0007).

The Inspect task and the verifiers taskset both import this module, so they read the same
replies and pay the same reward.
"""

import re

NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
ANSWER_LINE = re.compile(
    rf"^\s*ANSWER\s*:\s*({NUMBER})\s*(?:Pa|K)?\s*$", re.MULTILINE | re.IGNORECASE
)


def answer(reply: str) -> float | None:
    """The number on the last line that is only 'ANSWER: <number>', with an optional Pa or K;
    markdown bold and code marks are ignored. None when no line follows the format."""
    found = ANSWER_LINE.findall(reply.replace("*", "").replace("`", ""))
    return float(found[-1]) if found else None


def reward(
    forecast: float | None, truth: float, persistence: float, climatology: float, floor: float
) -> float:
    """Skill over the better of persistence and climatology for this item, clipped to [0, 1].

    Copying either baseline gives an error no smaller than the better one, so it earns 0; the
    floor keeps a near-zero baseline error from inflating the reward."""
    if forecast is None:
        return 0.0
    baseline = min(abs(persistence - truth), abs(climatology - truth))
    skill = (baseline - abs(forecast - truth)) / max(baseline, floor)
    return min(1.0, max(0.0, skill))
