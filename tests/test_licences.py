"""What the environment packages must carry for their code and for the data they bundle."""

import hashlib
import tomllib
from pathlib import Path

import climaqa_v1
import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ["climaqa_v1", "era5_forecast_v1", "ibtracs_storm_v1", "heat_basis_v1"]


def test_the_climaqa_package_carries_its_items_licence_and_says_what_changed():
    package = Path(climaqa_v1.__file__).parent
    text = (package / "LICENSE-Apache-2.0.txt").read_bytes()
    # https://www.apache.org/licenses/LICENSE-2.0.txt, fetched 2026-11-06
    assert hashlib.sha256(text).hexdigest() == (
        "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
    )
    notice = (package / "NOTICE").read_text("utf-8")
    for needed in (
        "Rose-STL-Lab/ClimaQA",
        "3f084a0202c6260e588fb5b681d2e4ec859a3845",
        "arXiv 2410.16701",
        "Apache-2.0",
        "changed",
    ):
        assert needed in notice, needed
    project = tomllib.loads((ROOT / "environments/climaqa_v1/pyproject.toml").read_text("utf-8"))
    assert project["project"]["license"] == "MIT AND Apache-2.0"
    files = project["project"]["license-files"]
    assert {"LICENSE", "climaqa_v1/LICENSE-Apache-2.0.txt", "climaqa_v1/NOTICE"} == set(files)


@pytest.mark.parametrize("package", PACKAGES)
def test_every_package_carries_the_mit_licence_it_declares(package):
    folder = ROOT / "environments" / package
    assert (folder / "LICENSE").read_text("utf-8") == (ROOT / "LICENSE").read_text("utf-8")
    project = tomllib.loads((folder / "pyproject.toml").read_text("utf-8"))["project"]
    assert "MIT" in project["license"] and "LICENSE" in project["license-files"]
