"""Core parser functions that extract a piece of data from a TeraChem output file.

All parsers should follow a basic pattern:

1. Set the parsed data, cast to its appropriate Python type, on the results object.
2. Raise a MatchNotFound error if a match was not found

Use the regex_search() helper function implemented below in place of re.search() to ensure
that a MatchNotFoundError will be raised in a parser. More sophisticated parsers that
use re.findall (like parse_hessian) or rely upon not finding a match may implement a
different interface, but please strive to follow this basic patterns as much as
possible.
"""

import re
from enum import Enum
from pathlib import Path

from qcio import CalcType, Molecule

from qcparse.exceptions import MatchNotFoundError
from qcparse.models import ParsedDataCollector

from .decorators import parser
from .utils import regex_search
from typing import Union, Optional, List
from qcio import SinglePointInput

__all__ = [
    "get_calc_type",
    "calculation_succeeded",
    "parse_method",
    "parse_basis",
    "parse_version",
    "parse_natoms",
    "parse_nmo",
    "parse_xyz_filepath",
    "parse_energy",
    "parse_gradient",
    "parse_hessian",
    "parse_failure_text",
    "CalcType",
]


class FileType(str, Enum):
    stdout = "stdout"


def get_calc_type(string: str) -> CalcType:
    """Parse the driver from TeraChem stdout."""
    calc_types = (
        (CalcType.energy, r"SINGLE POINT ENERGY CALCULATIONS"),
        (CalcType.gradient, r"SINGLE POINT GRADIENT CALCULATIONS"),
        (CalcType.hessian, r" FREQUENCY ANALYSIS "),
    )
    for calc_type, regex in calc_types:
        match = re.search(regex, string)
        if match:
            return calc_type
    raise MatchNotFoundError(regex, string)


def post_process(
    output: ParsedDataCollector,
    file_content: Union[str, bytes],
    filetype: str,
    filepath: Optional[Path] = None,
    input_data: Optional[SinglePointInput] = None,
):
    """Any post processing required after parsing is done here.

    Args:
        Must accept 'output' and then all args passed to parse().
    """

    if not input_data and filetype == FileType.stdout and isinstance(file_content, str):
        # Parse Molecule object from xyz file and parse correct multiplicity and charge
        tcin_filepath = Path(filepath) if filepath else Path(".")
        relative_xyz_path = parse_xyz_filepath(file_content)
        raw_molecule = Molecule.open(tcin_filepath.parent / relative_xyz_path)
        mol_dict = raw_molecule.dict()
        mol_dict["charge"] = parse_total_charge(file_content)
        mol_dict["multiplicity"] = parse_spin_multiplicity(file_content)

        output.input_data.molecule = Molecule(**mol_dict)


@parser(filetype=FileType.stdout)
def parse_energy(string: str, output: ParsedDataCollector):
    """Parse the final energy from TeraChem stdout.

    NOTE:
        - Works on frequency files containing many energy values because re.search()
            returns the first result
    """
    regex = r"FINAL ENERGY: (-?\d+(?:\.\d+)?)"
    output.computed.energy = float(regex_search(regex, string).group(1))


@parser(filetype=FileType.stdout, input_data=True)
def parse_method(string: str, output: ParsedDataCollector):
    """Parse the method from TeraChem stdout."""
    regex = r"Method: (\S+)"
    output.input_data.program_args.model.method = regex_search(regex, string).group(1)


@parser(filetype=FileType.stdout, input_data=True)
def parse_basis(string: str, output: ParsedDataCollector):
    """Parse the basis from TeraChem stdout."""
    regex = r"Using basis set: (\S+)"
    output.input_data.program_args.model.basis = regex_search(regex, string).group(1)


def _parse_version(string: str) -> str:
    """Parse TeraChem version from TeraChem stdout."""
    regex = r"TeraChem (v\S*)"
    return regex_search(regex, string).group(1)


@parser(filetype=FileType.stdout)
def parse_version(string: str, output: ParsedDataCollector):
    """Parse TeraChem version from TeraChem stdout."""
    output.provenance.program_version = _parse_version(string)


# Factored out for use in calculation_succeeded and parse_failure_text
FAILURE_REGEXPS = (
    r"DIE called at line number .*",
    r"CUDA error:.*",
)


# TODO: Handle failures
def calculation_succeeded(string: str) -> bool:
    """Determine from TeraChem stdout if a calculation competed successfully."""
    for regex in FAILURE_REGEXPS:
        if re.search(regex, string):
            return False
    return True


# TODO: Handle Failures
@parser(filetype=FileType.stdout)
def parse_failure_text(string: str, output: ParsedDataCollector) -> str:
    """Parse failure message in TeraChem stdout."""
    for regex in FAILURE_REGEXPS:
        match = re.search(regex, string)
        if match:
            return match.group()

    return (
        "Could not extract failure message from TeraChem stdout. Look at the last "
        "lines of stdout for clues."
    )


@parser(filetype=FileType.stdout, only=[CalcType.gradient, CalcType.hessian])
def parse_gradient(string: str, output: ParsedDataCollector):
    """Parse gradient from TeraChem stdout."""
    # This will match all floats after the dE/dX dE/dY dE/dZ header and stop at the
    # terminating ---- line
    regex = r"(?<=dE\/dX\s{12}dE\/dY\s{12}dE\/dZ\n)[\d\.\-\s]+(?=\n-{2,})"
    gradient_string = regex_search(regex, string).group()

    # split string and cast to floats
    values = [float(val) for val in gradient_string.split()]

    # arrange into N x 3 gradient
    gradient = []
    for i in range(0, len(values), 3):
        gradient.append(values[i : i + 3])

    output.computed.gradient = gradient


@parser(filetype=FileType.stdout, only=[CalcType.hessian])
def parse_hessian(string: str, output: ParsedDataCollector):
    """Parse Hessian Matrix from TeraChem stdout

    Notes:
        This function searches the entire document N times for all regex matches where
        N is the number of atoms. This makes the function's code easy to reason about.
        If performance becomes an issues for VERY large Hessians (unlikely) you can
        accelerate this function by parsing all Hessian floats in one pass, like the
        parse_gradient function above, and then doing the math to figure out how to
        properly sequence those values to from the Hessian matrix given TeraChem's
        six-column format for printing out Hessian matrix entries.

    """
    # requires .format(int). {{}} values are to escape {15|2} for .format()
    regex = r"(?:\s+{}\s)((?:\s-?\d\.\d{{15}}e[+-]\d{{2}})+)"
    hessian = []

    # Match all rows containing Hessian data; one set of rows at a time
    count = 1
    while matches := re.findall(regex.format(count), string):
        row = []
        for match in matches:
            row.extend([float(val) for val in match.split()])
        hessian.append(row)
        count += 1

    if not hessian:
        raise MatchNotFoundError(regex, string)

    # Assert we have created a square Hessian matrix
    for i, row in enumerate(hessian):
        assert len(row) == len(
            hessian
        ), "We must have missed some floats. Hessian should be a square matrix. Only "
        f"recovered {len(row)} of {len(hessian)} floats for row {i}."

    output.computed.hessian = hessian


@parser(filetype=FileType.stdout)
def parse_natoms(string: str, output: ParsedDataCollector):
    """Parse number of atoms value from TeraChem stdout"""
    regex = r"Total atoms:\s*(\d+)"
    output.computed.calcinfo_natom = int(regex_search(regex, string).group(1))


@parser(filetype=FileType.stdout)
def parse_nmo(string: str, output: ParsedDataCollector):
    """Parse the number of molecular orbitals TeraChem stdout"""
    regex = r"Total orbitals:\s*(\d+)"
    output.computed.calcinfo_nmo = int(regex_search(regex, string).group(1))


def parse_xyz_filepath(string: str) -> Path:
    """Parse the path to the xyz file from TeraChem stdout.

    NOTE: This is a bit of a hack to handle the fact that TeraChem does not have the
    molecular coordinates in the output file and that parsers are not passed file
    paths, but rather the file contents as a string. So we return the parsed path
    relative to the stdout file and then the top-level parse function will open the
    xyz file and parse the molecule.
    """
    regex = r"XYZ coordinates (.+)"
    return Path(regex_search(regex, string).group(1))


def parse_total_charge(string: str) -> int:
    """Parse Molecule charge from TeraChem stdout"""
    regex = r"Total charge:\s*(\d+)"
    return int(regex_search(regex, string).group(1))


def parse_spin_multiplicity(string: str) -> int:
    """Parse Molecule spin multiplicity from TeraChem stdout"""
    regex = r"Spin multiplicity:\s*(\d+)"
    return int(regex_search(regex, string).group(1))
