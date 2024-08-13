from pathlib import Path
from typing import List, Optional, Union

import numpy as np
from qcio import ConformerSearchResults, Structure

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
) -> List[Structure]:
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
