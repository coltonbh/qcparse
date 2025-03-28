from pathlib import Path

import pytest
from qcio import ProgramInput
from qcio.utils import water


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory Path"""
    return Path(__file__).parent / "data"


@pytest.fixture
def terachem_file(test_data_dir):
    """Return a function that reads a file from the 'terachem' subdirectory."""

    def _read(filename: str) -> str:
        return (test_data_dir / "terachem" / filename).read_text()

    return _read


@pytest.fixture
def crest_file(test_data_dir):
    """Return a function that reads a file from the 'crest' subdirectory."""

    def _read(filename: str) -> str:
        return (test_data_dir / "crest" / filename).read_text()

    return _read


@pytest.fixture(scope="session")
def prog_inp():
    """Create a function that returns a ProgramInput object with a specified
    calculation type."""

    def create_prog_input(calctype):
        return ProgramInput(
            structure=water,
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
