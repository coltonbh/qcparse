"""Top level functions for the tcparse library"""

from importlib import import_module
from pathlib import Path
from typing import List, Optional, Union

from qcio import SinglePointFailedOutput, SinglePointInput, SinglePointSuccessfulOutput

from .exceptions import MatchNotFoundError
from .models import single_point_data_collector
from .parsers import ParserSpec, registry
from .utils import get_file_content

__all__ = ["parse"]


def parse(
    data_or_path: Union[str, bytes, Path],
    program: str,
    filetype: str,
    input_data: Optional[SinglePointInput] = None,
) -> Union[SinglePointSuccessfulOutput, SinglePointFailedOutput]:
    """Parse a file using the parsers registered for the given program.

    Args:
        data_or_path: File contents (str or bytes) or path to the file to parse.
        program: The QC program that generated the output file.
            To see the available programs run:
            >>> from qcparse import registry
            >>> registry.supported_programs()
        filetype: The type of file to parse (e.g. 'stdout' for the log output).
            To see the available filetypes for a given program run
            >>> from qcparse import registry
            >>> registry.supported_filetypes('program_name')
        input_data: An optional SinglePointInput object containing the input data
            for the calculation. This will be added to the SinglePointOutput object
            returned by this function and no input data will be parsed from the file.


    Returns:
        SinglePointOutput or SinglePointFailure object encapsulating the parsed data.
    """
    file_content = get_file_content(data_or_path)

    # Get the calculation type if filetype is 'stdout'
    if filetype == "stdout":
        get_calc_type = import_module(f"qcparse.parsers.{program}").get_calc_type
        calc_type = get_calc_type(file_content)
    else:
        calc_type = None

    collect_inputs = input_data is None
    # Get all the parsers for the program and filetype
    parsers: List[ParserSpec] = registry.get_parsers(
        program,
        filetype=filetype,
        collect_inputs=collect_inputs,
        calc_type=calc_type,
    )

    # Parsers add its results to this object.
    # TODO: Handle failed calculations
    data_collector = single_point_data_collector(collect_inputs)

    # Apply parsers to the file content.
    for parser_info in parsers:
        try:
            # This will raise a MatchNotFound error if the parser can't find its data
            parser_info.parser(file_content, data_collector)
        except MatchNotFoundError:
            if parser_info.required:
                raise
            else:
                # Parser didn't find anything, but it wasn't required
                pass

    data_collector.provenance.program = program

    if input_data:
        # Add the input data to the results object
        data_collector.input_data = input_data

    # Remove scratch data
    del data_collector.scratch

    return SinglePointSuccessfulOutput(**data_collector.dict())


if __name__ == "__main__":
    output = parse("./tests/data/water.gradient.out", "terachem", "stdout")
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
