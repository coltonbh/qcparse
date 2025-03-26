import re
from enum import Enum
from pathlib import Path
from typing import Any, Generator, Optional, Tuple, Union

import numpy as np
from qcio import (
    CalcType,
    OptimizationResults,
    ProgramInput,
    ProgramOutput,
    Provenance,
    SinglePointResults,
    Structure,
    constants,
)

from .utils import regex_search, register


class FileType(str, Enum):
    """CREST filetypes.

    Maps file types to their names as written in the CREST output directory (except
    for STDOUT and DIRECTORY).
    """

    STDOUT = "stdout"
    DIRECTORY = "directory"
    NUMHESS = "numhess1"
    G98 = "g98.out"
    ENGRAD = "crest.engrad"
    OPTLOG = "crestopt.log"


def iter_files(
    stdout: Optional[str], directory: Optional[Union[Path, str]]
) -> Generator[Tuple[FileType, Union[str, bytes]], None, None]:
    """
    Iterate over the files in a CREST output directory.

    If stdout is provided, yields a tuple for it.

    If directory is provided, iterates over the directory to yield files according to
    program-specific logic.

    Args:
        stdout: The contents of the CREST stdout file.
        directory: The path to the directory containing the CREST output files.

    Yields:
        (FileType, contents) tuples for a program's output.
    """
    if stdout is not None:
        yield FileType.STDOUT, stdout

    if directory is not None:
        for file in directory.iterdir():
            if file.is_file():
                if file.name == FileType.G98.value:
                    yield FileType.G98, file.read_text()
                elif file.name == FileType.NUMHESS.value:
                    yield FileType.NUMHESS, file.read_text()
                elif file.name == FileType.ENGRAD.value:
                    yield FileType.ENGRAD, file.read_text()
                elif file.name == FileType.OPTLOG.value:
                    yield FileType.OPTLOG, file.read_text()


@register(filetype=FileType.STDOUT, target=("extras", "program_version"))
def parse_version(string: str) -> str:
    """Parse version string from CREST stdout.

    Matches format of 'crest --version' on command line.
    """
    regex = r"Version (\d+\.\d+\.\d+),"
    match = regex_search(regex, string)
    return match.group(1)


@register(filetype=FileType.DIRECTORY, calctypes=[CalcType.conformer_search])
def parse_conformers(
    directory: Union[Path, str], stdout: Optional[str], input_data: ProgramInput
) -> dict[str, Any]:
    """Parse the conformers from the output directory of a CREST conformer search calculation.

    Args:
        stdout: The contents of the CREST stdout file (not used).
        directory: Path to the directory containing the CREST output files.
        input_data: The input object used for the calculation

    Returns:
        The parsed conformers and their energies as a dictionary.
    """
    directory = Path(directory)
    conformers = Structure.open_multi(
        directory / "crest_conformers.xyz",
        charge=input_data.structure.charge,
        multiplicity=input_data.structure.multiplicity,
    )

    # CREST places the energy as the only value in the comment line
    conf_energies = [
        float(conf.extras[Structure._xyz_comment_key][0]) for conf in conformers
    ]

    # Add identifiers to the conformers if topo is unchanged
    _add_identifiers_to_structures(conformers, input_data)

    return {
        "conformers": conformers,
        "conformer_energies": np.array(conf_energies),
    }


@register(filetype=FileType.DIRECTORY, calctypes=[CalcType.conformer_search])
def parse_rotamers(
    directory: Union[Path, str], stdout: Optional[str], input_data: ProgramInput
) -> dict[str, Any]:
    """Parse the rotamers from the output directory of a CREST conformer search calculation.

    Args:
        stdout: The contents of the CREST stdout file (not used).
        directory: Path to the directory containing the CREST output files.
        input_data: The input object used for the calculation

    Returns:
        The parsed rotamers and their energies as a dictionary.
    """
    directory = Path(directory)
    rotamers = Structure.open_multi(
        directory / "crest_rotamers.xyz",
        charge=input_data.structure.charge,
        multiplicity=input_data.structure.multiplicity,
    )

    # CREST places the energy as the only value in the comment line
    conf_energies = [
        float(conf.extras[Structure._xyz_comment_key][0]) for conf in rotamers
    ]

    # Add identifiers to the rotamers if topo is unchanged
    _add_identifiers_to_structures(rotamers, input_data)

    return {
        "rotamers": rotamers,
        "rotamer_energies": np.array(conf_energies),
    }


def _add_identifiers_to_structures(
    structures: list[Structure], input_data: ProgramInput
) -> None:
    """Add identifiers to a list of Structure objects if the 'topo' is unchanged."""
    if input_data.keywords.get("topo", True):
        ids = input_data.structure.identifiers.model_dump()
        for struct in structures:
            struct.add_identifiers(**ids)


@register(
    filetype=FileType.ENGRAD,
    calctypes=[CalcType.energy, CalcType.gradient],
    target="energy",
)
def parse_energy(contents: str) -> float:
    """Parse the output of a CREST energy and gradient calculation.

    Args:
        contents: The text of the output file.

    Returns:
        The parsed energy as a float.
    """
    energy_regex = r"# Energy \( Eh \)\n#*\n\s*([-\d.]+)"
    return float(regex_search(energy_regex, contents).group(1))


@register(
    filetype=FileType.ENGRAD,
    calctypes=[CalcType.energy, CalcType.gradient],
    target="gradient",
)
def parse_gradient(contents: str) -> float:
    """Parse the output of a CREST energy and gradient calculation.

    Args:
        contents: The text of the output file.

    Returns:
        The parsed gradient as a Nx3 list of lists of floats.
    """
    gradient_regex = r"# Gradient \( Eh/a0 \)\n#\s*\n((?:\s*[-\d.]+\n)+)"
    vals = [float(x) for x in regex_search(gradient_regex, contents).group(1).split()]
    # Group the values into chunks of 3 (for x, y, z).
    return [vals[i : i + 3] for i in range(0, len(vals), 3)]


@register(filetype=FileType.STDOUT, calctypes=[CalcType.hessian], target="energy")
def parse_energy_numhess(contents: str) -> SinglePointResults:
    """Parse the initial singlepoint calculation energy from stdout.

    Args:
        contents: The text of the stdout file.

    Returns:
        The parsed energy.
    """
    energy_regex = r"Energy\s=\s*([-+]?\d+\.\d+)\s*Eh"
    return float(regex_search(energy_regex, contents).group(1))


@register(filetype=FileType.NUMHESS, calctypes=[CalcType.hessian], target="hessian")
def parse_numhess1(contents: str) -> list[list[float]]:
    """Parse the numerical Hessian from the CREST numhess1 file.

    Args:
        contents: The text of the numhess1 file.

    Returns:
        The parsed Hessian as a list of lists of floats.
    """
    float_regex = r"[-]?\d*\.\d+|\d+"
    numbers = re.findall(float_regex, contents)
    return np.array(numbers, dtype=float)

def parse_numhess_dir(
    directory: Union[Path, str],
    filename: str = "numhess1",
    stdout: Optional[str] = None,
) -> SinglePointResults:
    """Parse the output directory of a CREST numerical Hessian calculation.

    Args:
        directory: Path to the directory containing the CREST output files.
        filename: The name of the file containing the numerical Hessian results.
            Default is 'numhess1'.

    Returns:
        The parsed numerical Hessian results as a SinglePointResults object.
    """
    # Parse the Hessian matrix
    numhess_data = (Path(directory) / filename).read_text()
    float_regex = r"[-+]?\d*\.\d+|\d+"
    numbers = re.findall(float_regex, numhess_data)
    array = np.array(numbers, dtype=float)
    spr_dict: dict[str, Any] = {"hessian": array}

    # Parse the frequency data from g98.out
    g98_text = (Path(directory) / "g98.out").read_text()
    parsed_g98 = parse_g98(g98_text)
    spr_dict = {**spr_dict, **parsed_g98}

    # Parse the energy if available
    if stdout:
        energy_regex = r"Energy\s*=\s*([-+]?\d+\.\d+)\s*Eh"
        energy = float(regex_search(energy_regex, stdout).group(1))
        spr_dict["energy"] = energy
    return SinglePointResults(**spr_dict)


@register(filetype=FileType.G98, calctypes=[CalcType.hessian], target="hessian")
def parse_g98(text: str) -> dict[str, Any]:
    """Parse the Gaussian98 output text for frequencies and cartesian displacements.

    Args:
        text: The text of the Gaussian98 output file.

    Returns:
        The parsed frequencies and normal mode displacements as a dictionary.
    """
    # Break up the text into blocks, each of which contains the frequencies and
    # normal mode displacements for up to three modes
    block_re = re.compile(r"(Frequencies --.*?)(?=Frequencies --|$)", re.DOTALL)
    blocks = block_re.findall(text)
    freqs_wavenumber = []
    normal_modes_cartesian = []

    # Extract frequencies and normal mode displacements from each block
    for block in blocks:
        lines = block.split("\n")
        # Collect frequencies from the first line
        freqs = [float(x) for x in lines[0].split()[2:]]
        freqs_wavenumber.extend(freqs)

        # Collect Cartesian Displacements
        # Start with line 7 because this is where the displacements start
        displacements = lines[7:]
        mode_disp: list[list[list[float]]] = [[] for _ in freqs]

        for line in displacements:
            # Get all numbers in the line (as strings).
            regex = r"[-+]?\d*\.\d+|[-+]?\d+"
            tokens = re.findall(regex, line)
            # We expect at least 2 + 3*len(freqs) numbers. If not, skip this line
            # because it is a header line for the subsequent block.
            if len(tokens) < 2 + 3 * len(freqs):
                continue

            # The first two tokens are atom index and atomic number; the rest are displacements.
            disp_values = tokens[2 : 2 + 3 * len(freqs)]

            # For each mode, extract the x, y, z displacements
            for i in range(len(freqs)):
                base = 3 * i
                x, y, z = map(float, disp_values[base : base + 3])
                mode_disp[i].append([x, y, z])
        normal_modes_cartesian.extend(mode_disp)

    # Convert displacement from Angstrom to Bohr
    as_np_array = np.array(normal_modes_cartesian) * constants.ANGSTROM_TO_BOHR

    return {
        "freqs_wavenumber": freqs_wavenumber,
        "normal_modes_cartesian": as_np_array,
    }


def parse_optimization_dir(
    directory: Union[Path, str],
    *,
    inp_obj: ProgramInput,
    stdout: str,
) -> OptimizationResults:
    """Parse the output directory of a CREST optimization calculation.

    Args:
        directory: Path to the directory containing the CREST output files.
        inp_obj: The qcio ProgramInput object for the optimization.
        stdout: The stdout from CREST.

    Returns:
        The parsed optimization results as a OptimizationResults object.
    """
    # Read in the xyz file containing the trajectory
    directory = Path(directory)
    xyz_text = (directory / "crestopt.log").read_text()

    # Parse structures and energies from the xyz file
    structures = Structure.from_xyz_multi(
        xyz_text,
        charge=inp_obj.structure.charge,
        multiplicity=inp_obj.structure.multiplicity,
    )
    energies = [
        float(struct.extras[Structure._xyz_comment_key][1]) for struct in structures
    ]

    # Fake gradient for each step because CREST does not output it
    fake_gradient = np.zeros(len(inp_obj.structure.symbols) * 3)

    # Parse program version
    program_version = parse_version(stdout)

    # Collect final gradient if calculation succeeded
    try:
        final_spr = parse_singlepoint_dir(directory)
    except FileNotFoundError:
        # Calculation failed, so we don't have the final energy or gradient
        final_spr = SinglePointResults(gradient=fake_gradient)

    # Create the optimization trajectory
    trajectory: list[ProgramOutput] = [
        ProgramOutput(
            input_data=ProgramInput(
                calctype=CalcType.gradient,
                structure=struct,
                model=inp_obj.model,
            ),
            success=True,
            results=SinglePointResults(energy=energy, gradient=fake_gradient),
            provenance=Provenance(
                program="crest",
                program_version=program_version,
            ),
        )
        for struct, energy in zip(structures, energies)
    ]

    # Fill in final gradient
    # https://github.com/crest-lab/crest/issues/354
    trajectory[-1].results.gradient[:] = final_spr.gradient

    return OptimizationResults(
        trajectory=trajectory,
    )
