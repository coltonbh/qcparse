import pytest
from qcelemental.models import AtomicResult, FailedOperation

from tcparse import parse
from tcparse.parsers import SupportedDrivers


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
