"""Core parser functions that extract a piece of data from a TeraChem stdout file.

All parsers should follow a basic pattern:

1. Return the corresponding data cast to its appropriate Python type
2. Raise a MatchNotFound error if a match was not found

Use the _search() helper function implemented below in place of re.search() to ensure
that a MatchNotFoundError will be raised in a parser. More sophisticated parsers that
use re.findall (like parse_hessian) or rely upon not finding a match may implement a
different interface, but please strive to follow this basic patterns as much as
possible.
"""

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
    """Generic function for matching encapsulating exception raising for a parser.

    Parsers should use this _search function instead of re.search unless they are
    matching multiple objects with re.findall or relying upon a lack of match for
    signal.

    Args:
        regex: A regular expression string.
        string: The string to match on.

    Returns:
        The re.Match object, if a match is found.

    Raises:
        MatchNotFoundError if no match found.
    """
    match = re.search(regex, string)
    if not match:
        raise MatchNotFoundError(
            f"Could not locate match for regex: {regex} in string: {string}"
        )
    return match


def parse_energy(string: str) -> float:
    """Parse the final energy from TeraChem stdout.

    NOTE:
        - Works on frequency files containing many energy values because re.search()
            returns the first result
    """
    regex = r"FINAL ENERGY: (-?\d+(?:\.\d+)?)"
    return float(_search(regex, string).group(1))


def parse_driver(string: str) -> SupportedDrivers:
    """Parse the driver from TeraChem stdout."""
    drivers = (
        (SupportedDrivers.energy, r"SINGLE POINT ENERGY CALCULATIONS"),
        (SupportedDrivers.gradient, r"SINGLE POINT GRADIENT CALCULATIONS"),
        (SupportedDrivers.hessian, r" FREQUENCY ANALYSIS "),
    )
    for driver, regex in drivers:
        match = re.search(regex, string)
        if match:
            return driver

    raise MatchNotFoundError(f"Could not identify driver in string {string}")


def parse_xyz_filepath(string: str) -> Path:
    """Parse the path to the xyz file from TeraChem stdout."""
    regex = r"XYZ coordinates (.+)"
    return Path(_search(regex, string).group(1))


def parse_method(string: str) -> str:
    """Parse the method from TeraChem stdout."""
    regex = r"Method: (\S+)"
    return _search(regex, string).group(1)


def parse_basis(string: str) -> str:
    """Parse the basis from TeraChem stdout."""
    regex = r"Using basis set: (\S+)"
    return _search(regex, string).group(1)


def parse_version(string: str) -> str:
    """Parse TeraChem version from TeraChem stdout."""
    regex = r"TeraChem (v\S*)"
    return _search(regex, string).group(1)


# Factored out for use in calculation_succeeded and parse_failure_text
FAILURE_REGEXPS = (
    r"DIE called at line number .*",
    r"CUDA error:.*",
)


def calculation_succeeded(string: str) -> bool:
    """Determine from TeraChem stdout if a calculation competed successfully."""
    for regex in FAILURE_REGEXPS:
        if re.search(regex, string):
            return False
    return True


def parse_failure_text(string: str) -> str:
    """Parse failure message in TeraChem stdout."""
    for regex in FAILURE_REGEXPS:
        match = re.search(regex, string)
        if match:
            return match.group()

    return (
        "Could not extract failure message from TeraChem stdout. Look at the last "
        "lines of stdout for clues."
    )


def parse_gradient(string: str) -> List[List[float]]:
    """Parse gradient from TeraChem stdout."""
    # This will match all floats after the dE/dX dE/dY dE/dZ header and stop at the
    # terminating ---- line
    regex = r"(?<=dE\/dX\s{12}dE\/dY\s{12}dE\/dZ\n)[\d\.\-\s]+(?=\n-{2,})"
    gradient_string = _search(regex, string).group()

    # split string and cast to floats
    values = [float(val) for val in gradient_string.split()]

    # arrange into N x 3 gradient
    gradient = []
    for i in range(0, len(values), 3):
        gradient.append(values[i : i + 3])
    return gradient


def parse_hessian(string: str) -> List[List[float]]:
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

    return hessian


def parse_natoms(string: str) -> int:
    """Parse number of atoms value from TeraChem stdout"""
    regex = r"Total atoms:\s*(\d+)"
    return int(_search(regex, string).group(1))


def parse_nmo(string: str) -> int:
    """Parse the number of molecular orbitals TeraChem stdout"""
    regex = r"Total orbitals:\s*(\d+)"
    return int(_search(regex, string).group(1))


def parse_total_charge(string: str) -> float:
    """Parse total charge from TeraChem stdout"""
    regex = r"Total charge:\s*(\d+)"
    return float(_search(regex, string).group(1))


def parse_spin_multiplicity(string: str) -> int:
    """Parse spin multiplicity from TeraChem stdout"""
    regex = r"Spin multiplicity:\s*(\d+)"
    return int(_search(regex, string).group(1))
