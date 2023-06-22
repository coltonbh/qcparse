import importlib
import inspect
from functools import wraps
from typing import List, Optional

from qcio import Drivers

from .registry import registry

__all__ = ["parser"]


def parser(
    filetype: str,
    *,
    required: bool = True,
    input_data: bool = False,
    only_drivers: Optional[List[Drivers]] = None,
):
    """Decorator to register a function as a parser for program output filetype.

    Args:
        filetype: The filetype the parser operates on.
        required: If True and the parser fails a MatchNotFoundError will be raised.
            If False and the parser fails the value will be ignored.
        input_data: Whether the parser is for input data, such as method, basis, or a
            molecular structure, instead of computed output data. If True the parser
            will be not be called if a SinglePointInput object is passed as input_data
            to the top-level parse function.
        only_drivers: The drivers that the parser is for. If None the parser will be
            registered for all drivers.
    """

    def decorator(func):
        # Get the current module name. Should match program name.
        module = inspect.getmodule(func).__name__
        program_name = module.split(".")[-1]

        # Dynamically import the relevant Enum module
        supported_file_types = importlib.import_module(f"{module}").SupportedFileTypes

        # Check if filetype is a member of the relevant Enum
        if filetype not in supported_file_types.__members__:
            raise ValueError(
                f"Program '{program_name}' does not support the filetype '{filetype}' "
                f"defined in the decorator around '{func.__name__}'. Ether add "
                f"'{filetype}' to the FileTypes Enum in '{module}' or change "
                f"the parser wrapper to the correct filetype."
            )

        # Register the function in the global registry
        registry.register(
            program_name,
            filetype,
            required,
            func,
            only_drivers,
            input_data,
        )

        @wraps(func)
        def wrapper(stdout: str):
            # Call the original function
            return func(stdout)

        return wrapper

    return decorator
