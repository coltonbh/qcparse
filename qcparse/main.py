"""Top level functions for the tcparse library"""

import functools
import warnings
from importlib import import_module
from pathlib import Path
from typing import List, Union

from qcio import SinglePointResults

from .exceptions import MatchNotFoundError
from .models import ParserSpec, registry, single_point_results_namespace
from .parsers import *  # noqa: F403 Ensure all parsers get registered
from .utils import get_file_contents

__all__ = ["parse", "parse_results", "registry"]


def parse(
    data_or_path: Union[str, bytes, Path],
    program: str,
    filetype: str = "stdout",
) -> SinglePointResults:
    """Parse a file using the parsers registered for the given program.

    Can expand function to return other Results objects in the future.

    Args:
        data_or_path: File contents (str or bytes) or path to the file to parse.
        program: The QC program that generated the output file.
            To see the available programs run:
            >>> from qcparse import registry
            >>> registry.supported_programs()
        filetype: The type of file to parse (e.g. 'stdout' for the log output).
            To see the available filetypes for a given program run
            >>> from qcparse import registry
            >>> registry.supported_filetypes('program_name')

    Returns:
        A SinglePointResults object containing the parsed data.

    Raises:
        MatchNotFoundError: If a required parser fails to parse its data.
    """
    file_content, _ = get_file_contents(data_or_path)

    # Create a SinglePointResult namespace object to collect the parsed data
    spr_namespace = single_point_results_namespace()

    # Get the calctype if filetype is 'stdout'
    if filetype == "stdout":
        parse_calctype = import_module(f"qcparse.parsers.{program}").parse_calctype
        calctype = parse_calctype(file_content)

    else:
        calctype = None

    # Get all the parsers for the program and filetype
    parser_specs: List[ParserSpec] = registry.get_parsers(program, filetype, calctype)

    # Apply parsers to the file content.
    for ps in parser_specs:
        try:
            # This will raise a MatchNotFound error if the parser can't find its data
            ps.parser(file_content, spr_namespace)
        except MatchNotFoundError:
            if ps.required:
                raise
            else:  # Parser didn't find anything, but it wasn't required
                pass

    return SinglePointResults(**spr_namespace.dict())


@functools.wraps(parse)
def parse_results(*args, **kwargs):
    warnings.warn(
        "The function 'parse_results' is deprecated and will be removed in a future "
        "version. Use 'parse' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return parse(*args, **kwargs)
