from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory Path"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def energy_output(test_data_dir):
    with open(test_data_dir / "water.energy.out") as f:
        return f.read()
