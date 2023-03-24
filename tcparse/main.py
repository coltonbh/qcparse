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

__all__ = ["parse"]


def parse(
    outfile: Union[Path, str] = Path("tc.out"), ignore_molecule: bool = False
) -> Union[AtomicResult, FailedOperation]:
    """Parse a TeraChem stdout file

    Args:
        outfile: Path to the file containing stdout

    Returns:
        AtomicResult or FailedOperation object encapsulating the data from the TeraChem
        output directory.
    """
    outfile = Path(outfile)  # Cast outfile to Path

    # Read in TeraChem's stdout
    with open(outfile) as f:
        tcstdout = f.read()

    if ignore_molecule:
        # Use a placeholder Hydrogen Atom
        molecule = Molecule.from_data(
            """
    H  0.000000   0.000000   0.000000
    """,
            extras={
                "NOTICE": (
                    "This the data parsed in this AtomicResult does NOT "
                    "correspond to this molecule. This is a simple Hydrogen atom used "
                    "as a placeholder."
                )
            },
        )
    else:
        molecule = Molecule.from_file(outfile.parent / parse_xyz_filepath(tcstdout))

    # Values to parse whether calculation was a success or failure
    driver = parse_driver(tcstdout)  # returns SupportedDriver
    model = {"method": parse_method(tcstdout), "basis": parse_basis(tcstdout)}
    tc_version = parse_version(tcstdout)
    success = calculation_succeeded(tcstdout)

    if success:
        # Define basic objects for capturing output values
        atomic_result_properties: Dict[
            str, Any
        ] = {}  # Will become AtomicResultProperties
        return_result: Union[
            float, List[List[float]]
        ]  # May be energy, gradient, or hessian
        # Properties from Molecule (silly qcel requires these for grad/hess validation)
        atomic_result_properties["calcinfo_natom"] = len(molecule.symbols)
        # Always parse energy
        energy = parse_energy(tcstdout)  # Always parse energy for all drivers

        # Parse gradient/hessian if these were the given drivers
        if driver == SupportedDrivers.gradient:
            gradient = parse_gradient(tcstdout)
            atomic_result_properties["return_gradient"] = gradient
            return_result = gradient
        elif driver == SupportedDrivers.hessian:
            hessian = parse_hessian(tcstdout)
            gradient = parse_gradient(tcstdout)
            atomic_result_properties["return_hessian"] = hessian
            atomic_result_properties["return_gradient"] = gradient
            return_result = hessian
        else:
            atomic_result_properties["return_energy"] = energy
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


if __name__ == "__main__":
    ar = parse("tests/data/failure.nocuda.out")
