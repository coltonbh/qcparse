"""Top level functions for the tcparse library"""

import functools
import warnings
from importlib import import_module
from pathlib import Path
from typing import List, Union

from qcio import ProgramInput, SinglePointResults

from .exceptions import EncoderError, MatchNotFoundError, ParserError
from .models import NativeInput, ParserSpec, registry, single_point_results_namespace
from .parsers import *  # noqa: F403 Ensure all parsers get registered
from .utils import get_file_contents

__all__ = ["parse", "parse_results", "encode", "registry"]


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
        ParserError: If no parsers are registered for the filetype of the program.
        MatchNotFoundError: If a required parser fails to parse its data.
    """
    parsers = import_module(f"qcparse.parsers.{program}")

    # Check that filetype is supported by the program's parsers
    if filetype not in parsers.SUPPORTED_FILETYPES:
        raise ParserError(f"filetype '{filetype}' not supported by {program} parsers.")

    file_content = get_file_contents(data_or_path)

    # Get the calctype if filetype is 'stdout'
    if filetype == "stdout":
        calctype = parsers.parse_calctype(file_content)

    # Get all the parsers for the program, filetype, and calctype
    parser_specs: List[ParserSpec] = registry.get_parsers(program, filetype, calctype)

    # Create a SinglePointResult namespace object to collect the parsed data
    data_collector = single_point_results_namespace()

    # Apply parsers to the file content.
    for ps in parser_specs:
        try:
            ps.parser(file_content, data_collector)
        except MatchNotFoundError:  # Raised if the parser can't find its data
            if ps.required:
                raise

    return SinglePointResults(**data_collector.dict())


@functools.wraps(parse)
def parse_results(*args, **kwargs):
    warnings.warn(
        "The function 'parse_results' is deprecated and will be removed in a future "
        "version. Use 'parse' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return parse(*args, **kwargs)


def encode(inp_data: ProgramInput, program: str) -> NativeInput:
    """Encode a ProgramInput object to a NativeInput object.

    Args:
        inp_data: The ProgramInput object to encode.
        program: The program for which to encode the input.

    Returns:
        A NativeInput object with the encoded input.

    Raises:
        EncoderError: If the calctype is not supported by the program's encoder.
    """
    # Check that calctype is supported by the encoder
    encoder = import_module(f"qcparse.encoders.{program}")
    if inp_data.calctype not in encoder.SUPPORTED_CALCTYPES:
        raise EncoderError(f"Calctype '{inp_data.calctype}' not supported by encoder.")

    return encoder.encode(inp_data)
