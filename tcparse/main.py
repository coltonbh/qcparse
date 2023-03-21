from pathlib import Path
from typing import Union

from qcelemental.models import AtomicResult


def parse_directory(
    directory: Union[Path, str], stdout_file: str = "tc.out", geom_file="geom.xyz"
) -> AtomicResult:
    """Parse a TeraChem output directory

    Args:
        directory: Path to the directory containing output files
        stdout_file: Name of the file containing stdout
        geom_file: Name of the file containing the geometry coordinates of the molecule

    Returns:
        AtomicResult object encapsulating the data from the TeraChem output directory.
    """
    pass
