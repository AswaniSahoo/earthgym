"""Every environment runs on verifiers' null harness unless a run names another: the default
for a taskset that names none is `bash`, which gives the model a shell (decision 0023)."""

import pytest
from verifiers.v1.harnesses.null.harness import NullHarness
from verifiers.v1.taskset import Taskset
from verifiers.v1.utils import loaders

ENVS = ["climaqa-v1", "era5-forecast-v1", "ibtracs-storm-v1", "heat-basis-v1"]


@pytest.mark.parametrize("env", ENVS)
def test_each_environment_defaults_to_the_harness_that_runs_no_code(env):
    assert loaders.harness_class(loaders.default_harness_id(env)) is NullHarness
    assert NullHarness.EXECUTES_CODE is False


@pytest.mark.parametrize("env", ENVS)
def test_each_environment_still_exports_one_taskset(env):
    assert issubclass(loaders.taskset_class(env), Taskset)
