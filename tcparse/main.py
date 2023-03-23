from pathlib import Path
from typing import Any, Dict, List, Union

from qcelemental.models import AtomicInput, AtomicResult, FailedOperation, Molecule

from .parsers import (
    SupportedDrivers,
    calculation_succeeded,
    parse_basis,
    parse_driver,
    parse_energy,
    parse_failure_text,
    parse_gradient,
    parse_hessian,
    parse_method,
    parse_version,
    parse_xyz_filepath,
)


def parse(
    outfile: Union[Path, str] = Path("tc.out")
) -> Union[AtomicResult, FailedOperation]:
    """Parse a TeraChem stdout file

    Args:
        outfile: Path to the file containing stdout

    Returns:
        AtomicResult or FailedOperation object encapsulating the data from the TeraChem
        output directory.
    """
    outfile = Path(outfile)

    # Read stdout
    with open(outfile) as f:
        tcstdout = f.read()

    molecule = Molecule.from_file(outfile / parse_xyz_filepath(tcstdout))

    # Values to parse whether calculation was a success or failure
    driver = str(parse_driver(tcstdout))  # returns SupportedDriver
    method = parse_method(tcstdout)
    basis = parse_basis(tcstdout)
    model = {"method": method, "basis": basis}
    tc_version = parse_version(tcstdout)
    success = calculation_succeeded(tcstdout)

    if success:
        atomic_result_properties: Dict[str, Any] = {}  # Define for collecting values
        energy = parse_energy(tcstdout)  # always parse energy
        # Parse gradient/hessian only if this is the specific runtype
        return_result: Union[float, List[List[float]]]
        if driver == SupportedDrivers.gradient:
            gradient = parse_gradient(tcstdout)
            atomic_result_properties["return_gradient"] == gradient
            return_result = gradient
        elif driver == SupportedDrivers.hessian:
            hessian = parse_hessian(tcstdout)
            atomic_result_properties["return_hessian"] == hessian
            return_result = hessian
        else:
            atomic_result_properties["return_energy"] == energy
            return_result = energy

        return AtomicResult(
            molecule=molecule,
            driver=driver,
            model=model,
            return_result=return_result,
            provenance={"creator": "TeraChem", "version": tc_version},
            properties=atomic_result_properties,
            stdout=tcstdout,
            success=True,
        )
    else:
        # If calculation failed
        error_message = parse_failure_text(tcstdout)
        return FailedOperation(
            input_data=AtomicInput(
                molecule=molecule,
                driver=driver,
                model=model,
            ),
            success=success,
            error={
                "error_type": "compute_error",
                "error_message": error_message,
                "extras": {"stdout": tcstdout},
            },
        )
