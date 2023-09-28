from pathlib import Path

import pytest
from qcio import ProgramInput
from qcio.utils import water

from qcparse.models import single_point_results_namespace


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory Path"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def terachem_energy_stdout(test_data_dir):
    with open(test_data_dir / "water.energy.out") as f:
        return f.read()


@pytest.fixture(scope="function")
def data_collector():
    return single_point_results_namespace()


@pytest.fixture(scope="session")
def prog_inp():
    """Create a function that returns a ProgramInput object with a specified
    calculation type."""

    def create_prog_input(calctype):
        return ProgramInput(
            molecule=water,
            calctype=calctype,
            # Integration tests depend up this model; do not change
            model={"method": "hf", "basis": "sto-3g"},
            # Tests depend upon these keywords; do not change
            keywords={
                "purify": "no",
                "some-bool": False,
            },
        )

    return create_prog_input
