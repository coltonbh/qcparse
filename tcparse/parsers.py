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
    """Parse the method from TeraChem stdout"""
    regex = r"Using basis set: (\S+)"
    return _search(regex, string).group(1)


def parse_version(string: str) -> str:
    """Parse TeraChem version"""
    regex = r"TeraChem (v\S*)"
    return _search(regex, string).group(1)


def calculation_succeeded(string: str) -> bool:
    """Determine if a calculation competed successfully"""
    regex = r"DIE called at line number"
    if re.search(regex, string):
        return False
    return True


def parse_failure_text(string: str) -> str:
    """Parse the failure printed by TeraChem"""
    regex = r"DIE called at line number .*"
    return _search(regex, string).group()


def parse_gradient(string: str) -> List[List[float]]:
    """Parse out a the gradient"""
    # Would be nicer to use a regex that captures each float separately but got blocked
    # regex = r"(?<=dE\/dX\s{12}dE\/dY\s{12}dE\/dZ\n)(?:[^\n]*\n)*?(\s*[-]?\d+\.\d+)\s+([-]?\d+\.\d+)\s+([-]?\d+\.\d+)"

    # This will match all decimals after the dE/dX dE/dY dE/dZ header
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
    raise NotImplementedError("Implement me :)")


if __name__ == "__main__":
    with open("tests/data/caffeine.gradient.out") as f:
        string = f.read()

    gradient = parse_gradient(string)
