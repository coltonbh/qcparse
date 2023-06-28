from pathlib import Path

import pytest

from qcparse.models import single_point_data_collector


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
    return single_point_data_collector(collect_inputs=True)
