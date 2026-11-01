"""One answer contract for the ERA5 forecast tasks: the answer line and the reward (0007).

The Inspect task and the verifiers taskset both import this module, so they read the same
replies and pay the same reward.
"""

import hashlib
import re
from datetime import datetime

VARIABLES = {  # WB2 name: (name in the prompt, unit); each item carries its reward floor
    "mean_sea_level_pressure": ("mean sea level pressure", "Pa"),
    "2m_temperature": ("2 m temperature", "K"),
}
PROMPT = (
    "Forecast {name} at one cell of the 64x32 ERA5 grid, centred at latitude {latitude:.4f} "
    "and longitude {longitude:.4f}. The forecast is issued at {init_time} UTC for "
    "{valid_time} UTC, {lead_hours} hours ahead.\n\n"
    "ERA5 {name} at this cell, every 6 hours up to the issue time, in {unit}:\n{lines}\n\n"
    "ERA5 1990 to 2019 climatology for this cell at the valid time: {climatology} {unit}.\n\n"
    "Give your forecast in {unit}. The last line of your response must be 'ANSWER: <number>'."
)
NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
ANSWER_LINE = re.compile(  # horizontal space only, so the number sits on the answer line
    rf"^[ \t]*ANSWER[ \t]*:[ \t]*({NUMBER})[ \t]*(?:Pa|K)?[ \t]*\.?[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)


def prompt(item: dict) -> str:
    """The task text: the cell, the times, the ERA5 history and the climatology; never the
    truth or the HRES forecast."""
    name, unit = VARIABLES[item["variable"]]
    pairs = zip(item["history_times"], item["history"], strict=True)
    lines = "\n".join(f"{time} UTC: {value}" for time, value in pairs)
    return PROMPT.format(**{**item, "name": name, "unit": unit, "lines": lines})


def answer(reply: str) -> float | None:
    """The number on the last line, wherever it sits in the reply, that is only
    'ANSWER: <number>' with an optional Pa or K and full stop, as in contract 0004; markdown
    bold, code marks and the Unicode minus sign are read as plain text. None when no line
    follows the format."""
    plain = reply.replace("*", "").replace("`", "").replace("\u2212", "-")
    found = ANSWER_LINE.findall(plain)
    return float(found[-1]) if found else None


def reward(
    forecast: float | None, truth: float, persistence: float, climatology: float, floor: float
) -> float:
    """Skill over the better of persistence and climatology for this item, clipped to [0, 1].

    Copying either baseline gives an error no smaller than the better one, so it earns 0; the
    floor (each item's, set by the rule in decision 0007) only stops a near-zero baseline error
    from inflating the reward."""
    if forecast is None:
        return 0.0
    baseline = min(abs(persistence - truth), abs(climatology - truth))
    scale = max(baseline, floor)
    if scale == 0:
        return 0.0  # a baseline is exact and there is no floor: no skill left to earn
    return min(1.0, max(0.0, (baseline - abs(forecast - truth)) / scale))


def group(item: dict) -> str:
    """The held-out group: the ISO week of the init time, so forecasts that share the same
    weather fall on one side of a split."""
    year, week, _ = datetime.strptime(item["init_time"], "%Y-%m-%dT%H").isocalendar()
    return f"{year}-W{week:02d}"


def split(item: dict) -> str:
    """'test' for about one group in five, picked by a hash of the group key, else 'train'."""
    return "test" if hashlib.sha256(group(item).encode()).digest()[0] % 5 == 0 else "train"
