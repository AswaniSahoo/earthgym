import pydantic
import pytest
from climaqa_v1 import contract as climaqa
from climaqa_v1 import taskset as climaqa_ts
from era5_forecast_v1 import contract as era5
from era5_forecast_v1 import taskset as era5_ts
from heat_basis_v1 import contract as heat
from heat_basis_v1 import taskset as heat_ts
from ibtracs_storm_v1 import contract as ibtracs
from ibtracs_storm_v1 import taskset as ibtracs_ts

ENVS = {
    "climaqa": (climaqa, climaqa_ts, climaqa_ts.ClimaqaTaskset, climaqa_ts.ClimaqaConfig),
    "era5": (era5, era5_ts, era5_ts.ForecastTaskset, era5_ts.ForecastConfig),
    "ibtracs": (ibtracs, ibtracs_ts, ibtracs_ts.StormTaskset, ibtracs_ts.StormConfig),
    "heat": (heat, heat_ts, heat_ts.HeatTaskset, heat_ts.HeatConfig),
}


def test_each_environment_groups_items_that_share_their_data():
    assert climaqa.group({"id": "gold/mcq/1"}) == "gold/mcq/1"  # no source passage is given
    assert ibtracs.group({"sid": "1980245N16322", "question": "ace"}) == "1980245N16322"
    # every station's season in one group: the four station pairs share stations
    pairs = [{"index": i, "site": s, "year": 2019} for i in "AB" for s in "XY"]
    assert {heat.group(p) for p in pairs} == {"2019"}


@pytest.mark.parametrize("name", ENVS)
def test_the_split_option_partitions_the_items_by_group(name):
    contract, ts, taskset, config = ENVS[name]
    rows = {r["id"]: r for r in ts.records()}
    ids = {s: {t.data.id for t in taskset(config(split=s)).load()} for s in ("train", "test")}
    assert ids["train"] | ids["test"] == {t.data.id for t in taskset(config()).load()}
    assert not ids["train"] & ids["test"]
    groups = {s: {contract.group(rows[i]) for i in ids[s]} for s in ids}
    assert not groups["train"] & groups["test"]
    assert 0.1 < len(ids["test"]) / len(rows) < 0.35


@pytest.mark.parametrize("name", ENVS)
def test_the_split_option_takes_only_train_or_test(name):
    assert ENVS[name][3](split="test").split == "test"
    with pytest.raises(pydantic.ValidationError):
        ENVS[name][3](split="dev")
