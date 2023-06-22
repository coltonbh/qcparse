import importlib
import inspect
from functools import wraps

from .registry import parser_registry

__all__ = ["parser"]


def parser(filetype: str, must_succeed: bool = True):
    """Decorator to register a function as a parser for program output filetype.

    Args:
        filetype: The filetype to register the function as a parser for.
        must_succeed: Whether the parser is required to be successful for the parsing
            to be considered successful. If True and the parser fails a
            MatchNotFoundError will be raised. If False and the parser fails the value
            will be ignored.
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
                f"'{filetype}' to the SupportedFileTypes Enum in '{module}' or change "
                f"the parser wrapper to the correct filetype."
            )

        # Register the function in the global registry
        parser_registry.register(program_name, filetype, must_succeed, func)

        @wraps(func)
        def wrapper(stdout: str):
            # Call the original function
            return func(stdout)

        return wrapper

    return decorator
