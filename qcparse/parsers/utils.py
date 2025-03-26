import importlib
import inspect
import logging
import re
from enum import Enum
from typing import List, Optional, Tuple, Union

from qcio import CalcType

from qcparse.exceptions import MatchNotFoundError
from qcparse.models import ParserSpec, registry

logger = logging.getLogger(__name__)


def register(
    filetype: Enum,
    *,
    calctypes: Optional[List[CalcType]] = None,
    required: bool = True,
    target: Optional[Union[str, Tuple[str, ...]]] = None,
):
    """Decorator to register a function as a parser.

    Args:
        filetype: The filetype the parser operates on.
        calctypes: A list of calculation types on which this parser should operate. If None, it applies to all CalcTypes.
        required: If True and the parser fails a MatchNotFoundError will be raised.
            If False and the parser fails the value will be ignored.
        target: Where on the data collector to assign the parsed result.
    """
    if target is None:
        assert (
            filetype == "directory"
        ), "target must be provided for non-directory filetypes"

    def decorator(func):
        # Get the current module name. Should match program name.
        module = inspect.getmodule(func).__name__
        program_name = module.split(".")[-1]

        # Dynamically import the relevant FileType Enum from the module
        supported_file_types = importlib.import_module(f"{module}").FileType

        # Check if filetype is a member of the relevant Enum
        if filetype not in [member for member in supported_file_types]:
            raise ValueError(
                f"Program '{program_name}' does not support the filetype '{filetype}' "
                f"defined in the decorator around '{func.__name__}'. Ether add "
                f"'{filetype}' to the FileType Enum in '{module}' or change "
                f"the parser wrapper to the correct filetype."
            )
        # Create ParserSpec
        spec = ParserSpec(
            parser=func,
            filetype=filetype,
            required=required,
            calctypes=calctypes if calctypes is not None else list(CalcType),
            target=target,
        )

        # Register the function in the global registry
        registry.register(program_name, spec)

        return func

    return decorator


def regex_search(regex: str, string: str) -> re.Match:
    """Function for matching a regex to a string.

    Will match and return the first match found or raise MatchNotFoundError
    if no match is found.

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
        raise MatchNotFoundError(regex, string)
    return match
