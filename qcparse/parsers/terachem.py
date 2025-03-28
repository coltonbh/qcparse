"""Parsers for TeraChem output files."""

import re
from enum import Enum
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

from qcconst import constants
from qcio import (
    CalcType,
    ProgramInput,
    ProgramOutput,
    Provenance,
    SinglePointResults,
    Structure,
)

from qcparse.exceptions import MatchNotFoundError

from ..registry import register
from .utils import re_finditer, re_search


class TeraChemFileType(str, Enum):
    """TeraChem filetypes."""

    STDOUT = "stdout"
    DIRECTORY = "directory"


def iter_files(
    stdout: Optional[str], directory: Optional[Union[Path, str]]
) -> Generator[Tuple[TeraChemFileType, Union[str, bytes]], None, None]:
    """
    Iterate over the files in a TeraChem output directory.

    If stdout is provided, yields a tuple for it.

    If directory is provided, iterates over the directory to yield files according to
    program-specific logic.

    Args:
        stdout: The contents of the TeraChem stdout file.
        directory: The path to the directory containing the TeraChem output files.

    Yields:
        (FileType, contents) tuples for a program's output.
    """
    if stdout is not None:
        yield TeraChemFileType.STDOUT, stdout


@register(filetype=TeraChemFileType.STDOUT, target="energy")
def parse_energy(contents: str) -> float:
    """Parse the final energy from TeraChem stdout.

    NOTE:
        - Works on frequency files containing many energy values because re.search()
          returns the first result.
    """
    regex = r"FINAL ENERGY: (-?\d+(?:\.\d+)?)"
    return float(re_search(regex, contents).group(1))


@register(
    filetype=TeraChemFileType.STDOUT,
    calctypes=[CalcType.gradient, CalcType.hessian],
    target="gradient",
)
def parse_gradient(contents: str) -> list[list[float]]:
    """Parse the first gradient from TeraChem stdout.

    Returns:
        A single gradient as a list of 3-element lists.

    Raises:
        MatchNotFoundError: If no gradient data is found.
    """
    gradients = parse_gradients(contents)
    return gradients[0]


def parse_gradients(contents: str) -> list[list[list[float]]]:
    """Parse gradients from TeraChem stdout.

    Args:
        contents: The contents of the TeraChem stdout file.

    Returns:
        A list of gradients. Each gradient is a list of 3-element lists,
        where each 3-element list represents the gradient for one atom.

    Raises:
        MatchNotFoundError: If no gradient data is found.
    """
    # Match all floats after the dE/dX dE/dY dE/dZ header
    # until a terminating line (e.g., '--' or '-=') is encountered.
    regex = r"(?<=dE\/dX\s{12}dE\/dY\s{12}dE\/dZ\n)[\d\.\-\s]+(?=\n(?:--|-=))"
    matches = re_finditer(regex, contents)

    gradients = []
    for match in matches:
        # Convert the found numbers to floats.
        values = [float(val) for val in match.group(0).split()]
        # Group the values into chunks of 3 (for x, y, z).
        gradient = [values[i : i + 3] for i in range(0, len(values), 3)]
        gradients.append(gradient)

    return gradients


@register(
    filetype=TeraChemFileType.STDOUT, calctypes=[CalcType.hessian], target="hessian"
)
def parse_hessian(contents: str) -> list[list[float]]:
    """Parse Hessian Matrix from TeraChem stdout.

    Returns:
        A square matrix representing the Hessian, as a list of lists of floats.

    Raises:
        MatchNotFoundError: If no Hessian data is found.

    Notes:
        This function searches the entire document N times for all regex matches where
        N is the number of atoms. This makes the function's code easy to reason about.
        If performance becomes an issues for VERY large Hessians (unlikely) you can
        accelerate this function by parsing all Hessian floats in one pass, like the
        parse_gradient function above, and then doing the math to figure out how to
        properly sequence those values to form the Hessian matrix given TeraChem's
        six-column format for printing out Hessian matrix entries.
    """
    # requires .format(int). {{}} values are to escape {15|2} for .format()
    regex = r"(?:\s+{}\s)((?:\s-?\d\.\d{{15}}e[+-]\d{{2}})+)"
    hessian = []

    count = 1
    # Use a loop to collect each row based on the row number.
    while matches := re.findall(regex.format(count), contents):
        row = []
        for match in matches:
            row.extend([float(val) for val in match.split()])
        hessian.append(row)
        count += 1

    if not hessian:
        raise MatchNotFoundError(regex, contents)

    # Verify that the Hessian is a square matrix.
    for i, row in enumerate(hessian):
        if len(row) != len(hessian):
            raise ValueError(
                f"Hessian matrix is not square: row {i} has {len(row)} elements, expected {len(hessian)}."
            )

    return hessian


@register(filetype=TeraChemFileType.STDOUT, target=("extras", "program_version"))
def parse_version(contents: str) -> str:
    """Parse version contents plus git commit from TeraChem stdout.

    Matches format of 'terachem --version' on command line.

    Example:
        'v1.9-2022.03-dev [4daa16dd21e78d64be5415f7663c3d7c2785203c]'
    """
    return f"{parse_terachem_version(contents)} [{parse_version_control_details(contents)}]"


@register(filetype=TeraChemFileType.STDOUT, target="calcinfo_natoms")
def parse_natoms(contents: str) -> int:
    """Parse number of atoms value from TeraChem stdout.

    Returns:
        The number of atoms as an integer.

    Raises:
        MatchNotFoundError: If the regex does not match.
    """
    regex = r"Total atoms:\s*(\d+)"
    match = re_search(regex, contents)
    return int(match.group(1))


@register(filetype=TeraChemFileType.STDOUT, target="calcinfo_nmo")
def parse_nmo(contents: str) -> int:
    """Parse the number of molecular orbitals from TeraChem stdout.

    Returns:
        The number of molecular orbitals as an integer.

    Raises:
        MatchNotFoundError: If the regex does not match.
    """
    regex = r"Total orbitals:\s*(\d+)"
    match = re_search(regex, contents)
    return int(match.group(1))


@register(
    filetype=TeraChemFileType.DIRECTORY,
    calctypes=[CalcType.optimization],
    target="trajectory",
)
def parse_trajectory(
    directory: Union[Path, str],
    stdout: str,
    input_data: ProgramInput,
) -> List[ProgramOutput]:
    """Parse the output directory of a TeraChem optimization calculation into a trajectory.

    Args:
        directory: Path to the directory containing the TeraChem output files.
        stdout: The contents of the TeraChem stdout file.
        input_data: The input object used for the calculation.

    Returns:
        A list of ProgramOutput objects.
    """
    directory = Path(directory)

    # Parse the structures
    structures = Structure.open_multi(directory / "optim.xyz")

    # Parse the values from the stdout file
    from qcparse import decode

    parsed_results = decode("terachem", CalcType.energy, stdout=stdout)
    gradients = parse_gradients(stdout)

    # Create the trajectory
    trajectory: list[ProgramOutput] = []
    for structure, gradient in zip(structures, gradients):
        # Create input data object for each structure and gradient in the trajectory.
        input_data_obj = ProgramInput(
            calctype=CalcType.gradient,
            structure=structure,
            model=input_data.model,
            keywords=input_data.keywords,
        )
        # Create the results object for each structure and gradient in the trajectory.
        spr_data = parsed_results.model_dump()
        spr_data["energy"] = structure.extras[Structure._xyz_comment_key][0]
        spr_data["gradient"] = gradient
        results_obj = SinglePointResults(**spr_data)
        # Create the provenance object for each structure and gradient in the trajectory.
        prov = Provenance(
            program="terachem",
            program_version=parsed_results.extras["program_version"],
            scratch_dir=directory.parent,
        )
        # Create the ProgramOutput object for each structure and gradient in the trajectory.
        traj_entry: ProgramOutput = ProgramOutput(
            input_data=input_data_obj,
            success=True,
            results=results_obj,
            provenance=prov,
        )
        trajectory.append(traj_entry)

    return trajectory


def parse_version_control_details(contents: str) -> str:
    """Parse TeraChem git commit or Hg version from TeraChem stdout."""
    regex = r"(Git|Hg) Version: (\S*)"
    return re_search(regex, contents).group(2)


def parse_terachem_version(contents: str) -> str:
    """Parse TeraChem version from TeraChem stdout."""
    regex = r"TeraChem (v\S*)"
    return re_search(regex, contents).group(1)


def calculation_succeeded(contents: str) -> bool:
    """Determine from TeraChem stdout if a calculation completed successfully."""
    regex = r"Job finished:"
    if re.search(regex, contents):
        # If any match for a failure regex is found, the calculation failed
        return True
    return False


def parse_calctype(contents: str) -> CalcType:
    """Parse the calctype from TeraChem stdout."""
    calctypes = {
        r"SINGLE POINT ENERGY CALCULATIONS": CalcType.energy,
        r"SINGLE POINT GRADIENT CALCULATIONS": CalcType.gradient,
        r"FREQUENCY ANALYSIS": CalcType.hessian,
    }
    for regex, calctype in calctypes.items():
        match = re.search(regex, contents)
        if match:
            return calctype
    raise MatchNotFoundError(regex, contents)


def parse_excited_states(contents: str) -> list[dict]:
    """Parse the excited state information from a TDDFT TeraChem stdout.

    Args:
        contents: The contents of the TeraChem TDDFT stdout file.
    Returns:
        A list of dictionaries containing the excited state information.
    Raises:
        MatchNotFoundError: If no excited state data is found.
    Notes:
        Converts the excitation energy from eV to Hartree.
    """
    regex = (
        r"^\s*(?:\d+)\s+(?P<energy>-?\d+\.\d+)\s+"
        r"(?P<exc_energy>-?\d+\.\d+)\s+"
        r"(?P<osc_strength>-?\d+\.\d+)\s+"
        r"(?P<s_squared>-?\d+\.\d+)\s+"
        r"(?P<max_ci_coeff>-?\d+\.\d+)\s+"
        r"(?P<excitation>\d+\s+->\s+\d+\s+:\s+\w+\s+->\s+\w+)$"
    )
    matches = re_finditer(regex, contents, re.MULTILINE)

    # Create a list of dictionaries for each excited state
    excited_states = []
    for match in matches:
        excited_state = match.groupdict()
        # Convert numeric values to floats
        for key, value in excited_state.items():
            if key != "excitation":  # Keep the excitation string as is
                excited_state[key] = float(value)

        # Convert the excitation energy to Hartree
        excited_state["exc_energy"] *= constants.EV_TO_HARTREE  # type: ignore
        excited_states.append(excited_state)

    return excited_states
