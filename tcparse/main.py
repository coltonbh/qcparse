"""Top level functions for the tcparse library"""

from pathlib import Path
from typing import Any, Dict, List, Union

from qcelemental.models import AtomicInput, AtomicResult, FailedOperation, Molecule

from .helpers import hydrogen
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
    parse_natoms,
    parse_nmo,
    parse_spin_multiplicity,
    parse_total_charge,
    parse_version,
    parse_xyz_filepath,
)

__all__ = ["parse"]


def parse(
    outfile: Union[Path, str], *, ignore_xyz: bool = False
) -> Union[AtomicResult, FailedOperation]:
    """Parse a TeraChem stdout file into structured Python objects.

    Args:
        outfile: Path to the TeraChem stdout file.
        ignore_xyz: If True do not look for the xyz file referenced in the TeraChem
            stdout on the `XYZ coordinates` line. Use a dummy hydrogen atom instead.

    Returns:
        AtomicResult or FailedOperation object encapsulating the TeraChem stdout data.
    """
    outfile_path = Path(outfile)  # Cast outfile to Path

    # Read in TeraChem's stdout
    with open(outfile_path) as f:
        tcout = f.read()

    if ignore_xyz:
        # Use a placeholder hydrogen atom
        molecule = hydrogen
    else:
        # Load the actual xyz structure referenced in the stdout
        molecule = Molecule.from_file(outfile_path.parent / parse_xyz_filepath(tcout))

    # Values to parse whether calculation was a success or failure
    driver = parse_driver(tcout)  # returns SupportedDriver
    model = {"method": parse_method(tcout), "basis": parse_basis(tcout)}
    tc_version = parse_version(tcout)

    success = calculation_succeeded(tcout)

    if success:
        properties: Dict[str, Any] = {}  # Various computed properties
        return_result: Union[float, List[List[float]]]  # energy or grad/hess matrix

        # Update Molecule with computed properties
        mol_dict = molecule.dict()
        mol_dict["molecular_charge"] = parse_total_charge(tcout)
        mol_dict["molecular_multiplicity"] = parse_spin_multiplicity(tcout)

        # Always parse these values
        return_result = properties["return_energy"] = parse_energy(tcout)
        properties["calcinfo_natom"] = parse_natoms(tcout)
        properties["calcinfo_nmo"] = parse_nmo(tcout)

        if driver in (SupportedDrivers.gradient, SupportedDrivers.hessian):
            return_result = properties["return_gradient"] = parse_gradient(tcout)

        if driver == SupportedDrivers.hessian:
            return_result = properties["return_hessian"] = parse_hessian(tcout)

        return AtomicResult(
            molecule=mol_dict,
            driver=driver,
            model=model,
            return_result=return_result,
            provenance={"creator": "TeraChem", "version": tc_version},
            properties=properties,
            stdout=tcout,
            success=success,
        )
    else:
        return FailedOperation(
            input_data=AtomicInput(
                molecule=molecule,
                driver=driver,
                model=model,
            ),
            success=success,
            error={
                "error_type": "compute_error",
                "error_message": parse_failure_text(tcout),
                "extras": {"stdout": tcout},
            },
            extras={"provenance": tc_version},
        )
