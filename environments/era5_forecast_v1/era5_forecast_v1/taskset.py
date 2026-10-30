"""era5-forecast-v1 as a verifiers v1 taskset: 720 forecast items, rewarded by the contract."""

import json
from importlib.resources import files

import verifiers.v1 as vf

from era5_forecast_v1 import contract

DATA_FILE = "era5_forecast_v1.jsonl"


def records() -> list[dict]:
    """The bundled items, one dict each; shared with the Inspect task."""
    lines = files("era5_forecast_v1").joinpath(DATA_FILE).read_text("utf-8").splitlines()
    return [json.loads(line) for line in lines]


class ForecastData(vf.TaskData):
    variable: str
    truth: float
    persistence: float
    climatology: float
    floor: float


class ForecastTask(vf.Task[ForecastData]):
    @vf.reward(weight=1.0)
    async def skill(self, trace: vf.Trace) -> float:
        d = self.data
        forecast = contract.answer(trace.last_reply)
        return contract.reward(forecast, d.truth, d.persistence, d.climatology, d.floor)


class ForecastConfig(vf.TasksetConfig):
    variables: list[str] = list(contract.VARIABLES)


class ForecastTaskset(vf.Taskset[ForecastTask, ForecastConfig]):
    def load(self) -> list[ForecastTask]:
        return [
            ForecastTask(to_data(row), self.config.task)
            for row in records()
            if row["variable"] in self.config.variables
        ]


def to_data(row: dict) -> ForecastData:
    return ForecastData(
        id=row["id"],
        prompt=contract.prompt(row),
        variable=row["variable"],
        truth=row["truth"],
        persistence=row["history"][-1],
        climatology=row["climatology"],
        floor=row["floor"],
    )
