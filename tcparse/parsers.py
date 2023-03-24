import re
from enum import Enum
from pathlib import Path
from typing import List

from .exceptions import MatchNotFoundError


class SupportedDrivers(str, Enum):
    energy = "energy"
    gradient = "gradient"
    hessian = "hessian"


def _search(regex, string) -> re.Match:
    """Generic Function for matching

    Args:
        regex: A regular expression
        string: The string to match on

    Returns:
        The matched data

    Raises:
        MatchNotFoundError if no match found
    """
    match = re.search(regex, string)
    if not match:
        raise MatchNotFoundError(
            f"Could not locate match for regex: {regex} in string: {string}"
        )
    return match


def parse_energy(string: str) -> float:
    """Parse the final energy from TeraChem stdout

    NOTE:
        - Works on frequency files containing many energy values because re.search()
            returns the first result
    """
    regex = r"FINAL ENERGY: (-?\d+(?:\.\d+)?)"
    return float(_search(regex, string).group(1))


def parse_driver(string: str) -> SupportedDrivers:
    """Parse the driver from TeraChem stdout"""
    runtypes = (
        (SupportedDrivers.energy, r"SINGLE POINT ENERGY CALCULATIONS"),
        (SupportedDrivers.gradient, r"SINGLE POINT GRADIENT CALCULATIONS"),
        (SupportedDrivers.hessian, r" FREQUENCY ANALYSIS "),
    )
    for runtype, regex in runtypes:
        match = re.search(regex, string)
        if match:
            return runtype

    raise MatchNotFoundError(f"Could not identify run type in string {string}")


def parse_xyz_filepath(string: str) -> Path:
    """Parse the path to the xyz file from TeraChem stdout"""
    regex = r"XYZ coordinates (.+)"
    return Path(_search(regex, string).group(1))


def parse_method(string: str) -> str:
    """Parse the method from TeraChem stdout"""
    regex = r"Method: (\S+)"
    return _search(regex, string).group(1)


def parse_basis(string: str) -> str:
    """Parse the basis from TeraChem stdout"""
    regex = r"Using basis set: (\S+)"
    return _search(regex, string).group(1)


def parse_version(string: str) -> str:
    """Parse TeraChem version from TeraChem stdout"""
    regex = r"TeraChem (v\S*)"
    return _search(regex, string).group(1)


def calculation_succeeded(string: str) -> bool:
    """Determine if a calculation competed successfully from TeraChem stdout"""
    failure_regexps = (
        r"DIE called at line number",
        r"CUDA error: no CUDA-capable device is detected",
    )
    for regex in failure_regexps:
        if re.search(regex, string):
            return False
    return True


def parse_failure_text(string: str) -> str:
    """Parse failure message in TeraChem stdout"""
    failure_regexps = (
        r"DIE called at line number .*",
        r"CUDA error: no CUDA-capable device is detected.*",
    )
    for regex in failure_regexps:
        match = re.search(regex, string)
        if match:
            return match.group()

    return (
        "Could not extract failure message from TeraChem stdout. Look at the last "
        "lines of stdout for clues."
    )


def parse_gradient(string: str) -> List[List[float]]:
    """Parse gradient from TeraChem stdout

    Matching on text like this:

        Gradient units are Hartree/Bohr
    ---------------------------------------------------
            dE/dX            dE/dY            dE/dZ
       -0.0000269528    -0.0000388595     0.0000306421
        0.0000115012     0.0000239264     0.0000042012
        0.0000154480     0.0000149307    -0.0000348414
    ---------------------------------------------------
    """
    # This will match all floats after the dE/dX dE/dY dE/dZ header and stop at the
    # terminating ---- line
    regex = r"(?<=dE\/dX\s{12}dE\/dY\s{12}dE\/dZ\n)[\d\.\-\s]+(?=\n-{2,})"
    string_vals = _search(regex, string).group()

    # split string and cast to floats
    values = [float(val) for val in string_vals.split()]

    # arrange into N x 3 gradient
    gradient = []
    for i in range(0, len(values), 3):
        gradient.append(values[i : i + 3])
    return gradient


def parse_hessian(string: str) -> List[List[float]]:
    """Parse Hessian Matrix from TeraChem stdout

    Notes:
        This function searches the entire document for all regex match N times where N
        is the number of atoms. This makes the function's code easy to reason about.
        If performance becomes an issues for VERY large Hessians (unlikely) you can
        accelerate this function by parsing all Hessian floats in one pass, like the
        parse_gradient function above, and then doing the math to figure out how to
        properly sequence those values to from the Hessian matrix.

    """
    regex = r"(?:\s+{}\s)((?:\s-?\d\.\d{{15}}e[+-]\d{{2}})+)"  # requires .format(int)
    hessian = []

    # Match all rows containing Hessian data; one set of rows at a time
    count = 1
    while matches := re.findall(regex.format(count), string):
        row = []
        for match in matches:
            row.extend([float(val) for val in match.split()])
        hessian.append(row)
        count += 1

    # Assert we have created a square Hessian matrix
    for i, row in enumerate(hessian):
        assert len(row) == len(
            hessian
        ), "We must have missed some floats. Hessian should be a square matrix. Only "
        f"recovered {len(row)} of {len(hessian)} floats for row {i}."

    return hessian
