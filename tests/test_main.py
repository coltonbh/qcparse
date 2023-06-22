import pytest
from qcelemental.models import AtomicResult, FailedOperation

from qcparse import parse
from qcparse.parsers import SupportedDrivers


@pytest.mark.parametrize(
    "filename,instance,driver",
    (
        ("water.energy.out", AtomicResult, SupportedDrivers.energy.value),
        ("water.gradient.out", AtomicResult, SupportedDrivers.gradient.value),
        ("water.frequencies.out", AtomicResult, SupportedDrivers.hessian.value),
        ("caffeine.gradient.out", AtomicResult, SupportedDrivers.gradient.value),
        ("caffeine.frequencies.out", AtomicResult, SupportedDrivers.hessian.value),
        ("failure.basis.out", FailedOperation, SupportedDrivers.gradient.value),
        ("failure.nocuda.out", FailedOperation, SupportedDrivers.gradient.value),
    ),
)
def test_parse(test_data_dir, filename, instance, driver):
    output = parse(test_data_dir / filename)
    assert isinstance(output, instance)
    if isinstance(output, AtomicResult):
        assert output.driver == driver
    else:
        # FailedOperation
        assert output.input_data.driver == driver
        # Guarantee stdout included
        assert isinstance(output.error.extras["stdout"], str)


@pytest.mark.parametrize(
    "filename,driver",
    (
        ("water.gradient.out", "gradient"),
        ("water.frequencies.out", "hessian"),
        ("water.molecule_moved.out", "energy"),
    ),
)
def test_parse_ignore_xyz(test_data_dir, filename, driver):
    # This tests that qcel still does correct validation on the gradient and
    output = parse(test_data_dir / filename, ignore_xyz=True)
    assert isinstance(output, AtomicResult)
    assert output.driver == driver
    # Using a hydrogen atoms as dummy
    assert output.molecule.symbols[0] == "H"


def test_parse_moved_molecule(test_data_dir):
    with pytest.raises(FileNotFoundError):
        parse(test_data_dir / "water.molecule_moved.out")
