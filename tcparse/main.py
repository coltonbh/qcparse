from pathlib import Path
from typing import Union

from qcelemental.models import AtomicResult


def parse_directory(outfile: Union[Path, str] = Path("tc.out")) -> AtomicResult:
    """Parse a TeraChem output directory

    Args:
        outfile: Name of the file containing stdout

    Returns:
        AtomicResult object encapsulating the data from the TeraChem output directory.

    # NOTE:
        - I may not need a "directory" or the geom_file name because this is contained
            in the terachem output file itself as "XYZ coordinates"
    """
    pass
