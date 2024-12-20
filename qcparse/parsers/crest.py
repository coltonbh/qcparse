import re
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
from qcio import (
    CalcType,
    ConformerSearchResults,
    OptimizationResults,
    ProgramInput,
    ProgramOutput,
    Provenance,
    SinglePointResults,
    Structure,
)

from .utils import regex_search


def parse_version_string(string: str) -> str:
    """Parse version string from CREST stdout.

    Matches format of 'crest --version' on command line.
    """
    regex = r"Version (\d+\.\d+\.\d+),"
    match = regex_search(regex, string)
    return match.group(1)


def parse_structures(
    filename: Union[Path, str],
    charge: Optional[int] = None,
    multiplicity: Optional[int] = None,
) -> list[Structure]:
    """Parse Structures from a CREST multi-structure xyz file.

    CREST places an energy value in the comments line of each structure. This function
    collects all Structures and their energies from the file into AnnotatedStructure
    objects.

    Args:
        filename: The path to the multi-structure xyz file.
        charge: The charge of the structures.
        multiplicity: The multiplicity of the structures.

    Returns:
        A list of Structure objects.
    """
    try:
        structures = Structure.open(filename, charge=charge, multiplicity=multiplicity)
        if not isinstance(structures, list):  # single structure
            structures = [structures]
    except FileNotFoundError:
        structures = []  # No structures created
    return structures


def parse_conformer_search_dir(
    directory: Union[Path, str],
    *,
    charge: Optional[int] = None,
    multiplicity: Optional[int] = None,
    collect_rotamers: bool = True,
) -> ConformerSearchResults:
    """Parse the output directory of a CREST conformer search calculation.

    Args:
        directory: Path to the directory containing the CREST output files.
        charge: The charge of the structures.
        multiplicity: The multiplicity of the structures.
        collect_rotamers: Whether to parse rotamers as well as conformers.

    Returns:
        The parsed conformers, rotamers, and their energies as a ConformerSearchResults
        object.
    """
    directory = Path(directory)
    conformers = parse_structures(
        directory / "crest_conformers.xyz", charge=charge, multiplicity=multiplicity
    )

    # CREST places the energy as the only value in the comment line
    conf_energies = [conf.extras[Structure._xyz_comment_key][0] for conf in conformers]

    rotamers = []
    if collect_rotamers:
        rotamers = parse_structures(
            directory / "crest_rotamers.xyz", charge=charge, multiplicity=multiplicity
        )

    # CREST places the energy as the only value in the comment line
    rotamer_energies = [rot.extras[Structure._xyz_comment_key][0] for rot in rotamers]

    return ConformerSearchResults(
        conformers=conformers,
        conformer_energies=np.array(conf_energies),
        rotamers=rotamers,
        rotamer_energies=np.array(rotamer_energies),
    )


def parse_energy_grad(text: str) -> SinglePointResults:
    """Parse the output of a CREST energy and gradient calculation.

    Args:
        text: The text of the output file.

    Returns:
        The parsed energy and gradient as a SinglePointResults object.
    """
    # Parse the energy
    energy_regex = r"# Energy \( Eh \)\n#*\n\s*([-\d.]+)"
    gradient_regex = r"# Gradient \( Eh/a0 \)\n#\s*\n((?:\s*[-\d.]+\n)+)"

    energy = float(regex_search(energy_regex, text).group(1))
    gradient = np.array(
        [float(x) for x in regex_search(gradient_regex, text).group(1).split()]
    )
    return SinglePointResults(
        energy=energy,
        gradient=gradient,
    )


def parse_singlepoint_dir(
    directory: Union[Path, str], filename: str = "crest.engrad"
) -> SinglePointResults:
    """Parse the output directory of a CREST single point calculation.

    Args:
        directory: Path to the directory containing the CREST output files.
        filename: The name of the file containing the single point results.
            Default is 'crest.engrad'.

    Returns:
        The parsed single point results as a SinglePointResults object.
    """
    directory = Path(directory)
    text = (directory / filename).read_text()

    return parse_energy_grad(text)


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
    data = (Path(directory) / filename).read_text()
    float_regex = r"[-+]?\d*\.\d+|\d+"
    numbers = re.findall(float_regex, data)
    array = np.array(numbers, dtype=float)
    spr_dict: dict[str, Any] = {"hessian": array}
    if stdout:
        energy_regex = r"Energy\s*=\s*([-+]?\d+\.\d+)\s*Eh"
        energy = float(regex_search(energy_regex, stdout).group(1))
        spr_dict["energy"] = energy
    return SinglePointResults(**spr_dict)


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
    program_version = parse_version_string(stdout)

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
