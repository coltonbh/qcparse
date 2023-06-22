"""Top level functions for the tcparse library"""

from pathlib import Path
from typing import Union

from qcio import SinglePointOutput

# from .parsers import (
#     SupportedDrivers,
#     calculation_succeeded,
#     parse_basis,
#     parse_driver,
#     parse_energy,
#     parse_failure_text,
#     parse_gradient,
#     parse_hessian,
#     parse_method,
#     parse_natoms,
#     parse_nmo,
#     parse_spin_multiplicity,
#     parse_total_charge,
#     parse_version,
#     parse_xyz_filepath,
# )
from .exceptions import MatchNotFoundError
from .models import single_point_result_ns
from .parsers import parser_registry

__all__ = ["parse"]


def parse(
    filepath: Union[str, Path],
    program: str,
    filetype: str,
    parse_input_data: bool = False,
) -> SinglePointOutput:
    """Parse a file using the parsers registered for the given program.

    Args:
        filepath: Path to the file to parse.
        program: The QC program that generated the output file.
            To see the available programs run
            >>> from qcparse import parser_registry
            >>> parser_registry.get_programs()
        filetype: The type of file to parse (e.g. 'stdout' for the log output).
            To see the available filetypes for a given program run
            >>> from qcparse import parser_registry
            >>> parser_registry.get_filetypes('program_name')
        parse_input_data: If True, parse the input data as well as the output data.
    """
    filepath = Path(filepath)
    # Each parser will add its results to this object. Each value can only be set once.
    # This is to prevent parsers from overwriting each other's results.
    # results_obj structured like SinglePointOutput but mutable
    results_obj = single_point_result_ns()

    # Get all the parsers for the program
    parsers = parser_registry.get_parsers(program)

    # Read the file contents
    file_content = filepath.read_bytes()
    try:
        file_content = file_content.decode("utf-8")
    except UnicodeDecodeError:
        # File is binary data
        pass
    print(parsers)
    # Apply all parsers to the file content
    for parser_info in parsers:
        if parser_info.filetype == filetype:
            try:
                # This will raise a MatchNotFound error if the parser can't find its data
                parser_info.parser(file_content, results_obj)
                print(f"Ran parser: {parser_info.parser.__name__}")
            except MatchNotFoundError:
                if parser_info.required:
                    raise
                else:
                    # Parser didn't find anything, but it wasn't required
                    pass

    results_dict = results_obj.dict()
    if not parse_input_data:
        # Clear the input data
        results_dict["input_data"] = None

    return SinglePointOutput(**results_dict)


if __name__ == "__main__":
    output = parse("./tests/data/water.energy.out", "terachem", "stdout")
    print(output)


# def parse(
#     outfile: Union[Path, str], *, ignore_xyz: bool = False
# ) -> Union[AtomicResult, FailedOperation]:
#     """Parse a TeraChem stdout file into structured Python objects.

#     Args:
#         outfile: Path to the TeraChem stdout file.
#         ignore_xyz: If True do not look for the xyz file referenced in the TeraChem
#             stdout on the `XYZ coordinates` line. Use a dummy hydrogen atom instead.

#     Returns:
#         AtomicResult or FailedOperation object encapsulating the TeraChem stdout data.
#     """
#     outfile_path = Path(outfile)  # Cast outfile to Path

#     # Read in TeraChem's stdout
#     with open(outfile_path) as f:
#         tcout = f.read()

#     if ignore_xyz:
#         # Use a placeholder hydrogen atom
#         molecule = hydrogen
#     else:
#         # Load the actual xyz structure referenced in the stdout
#         molecule = Molecule.from_file(outfile_path.parent / parse_xyz_filepath(tcout))

#     # Values to parse whether calculation was a success or failure
#     driver = parse_driver(tcout)  # returns SupportedDriver
#     model = {"method": parse_method(tcout), "basis": parse_basis(tcout)}
#     tc_version = parse_version(tcout)

#     success = calculation_succeeded(tcout)

#     if success:
#         properties: Dict[str, Any] = {}  # Various computed properties
#         return_result: Union[float, List[List[float]]]  # energy or grad/hess matrix

#         # Update Molecule with computed properties
#         mol_dict = molecule.dict()
#         mol_dict["molecular_charge"] = parse_total_charge(tcout)
#         mol_dict["molecular_multiplicity"] = parse_spin_multiplicity(tcout)

#         # Always parse these values
#         return_result = properties["return_energy"] = parse_energy(tcout)
#         properties["calcinfo_natom"] = parse_natoms(tcout)
#         properties["calcinfo_nmo"] = parse_nmo(tcout)

#         if driver in (SupportedDrivers.gradient, SupportedDrivers.hessian):
#             return_result = properties["return_gradient"] = parse_gradient(tcout)

#         if driver == SupportedDrivers.hessian:
#             return_result = properties["return_hessian"] = parse_hessian(tcout)

#         return AtomicResult(
#             molecule=mol_dict,
#             driver=driver,
#             model=model,
#             return_result=return_result,
#             provenance={"creator": "TeraChem", "version": tc_version},
#             properties=properties,
#             stdout=tcout,
#             success=success,
#         )
#     else:
#         return FailedOperation(
#             input_data=AtomicInput(
#                 molecule=molecule,
#                 driver=driver,
#                 model=model,
#             ),
#             success=success,
#             error={
#                 "error_type": "compute_error",
#                 "error_message": parse_failure_text(tcout),
#                 "extras": {"stdout": tcout},
#             },
#             extras={"provenance": tc_version},
#         )
