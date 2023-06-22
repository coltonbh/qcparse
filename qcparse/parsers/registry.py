from collections import defaultdict
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel

from qcio import Drivers


class ParserSpec(BaseModel):
    """Information about a parser function.

    Attributes:
        filetype: The filetype that the parser is for.
        required: Whether the parser is required to be successful for the parsing to
            be considered successful. If True and the parser fails a MatchNotFoundError
            will be raised. If False and the parser fails the value will be ignored.
        parser: The parser function.
        only_drivers: The drivers that the parser is for. If None the parser will be
            registered for all drivers.
    """

    filetype: str
    required: bool
    parser: Callable
    input_data: bool = False
    only_drivers: List[Drivers] = []


class ParserRegistry(BaseModel):
    """Registry for parser functions."""

    registry: Dict[str, List[ParserSpec]] = defaultdict(list)

    def register(
        self,
        program: str,
        filetype: str,
        required: bool,
        parser: Callable,
        only_drivers: Optional[List[Drivers]] = None,
        input_data: bool = False,
    ) -> None:
        """Register a new parser function.

        Args:
            program: The program that the parser is for.
            filetype: The filetype that the parser is for.
            required: Whether the parser is required to be successful for the parsing to
                be considered successful. If True and the parser fails a MatchNotFoundError
                will be raised. If False and the parser fails the value will be ignored.
            parser: The parser function.
            only_drivers: The drivers that the parser is for. If None the parser will be
                registered for all drivers.
        """
        parser_info = ParserSpec(
            filetype=filetype,
            required=required,
            parser=parser,
            only_drivers=only_drivers,
            input_data=input_data,
        )
        self.registry[program].append(parser_info)

    def get_parsers(
        self,
        program: str,
        filetype: Optional[str] = None,
        input_data: bool = True,
        only_drivers: Optional[Drivers] = None,
    ) -> List[ParserSpec]:
        """Get all parser functions for a given program.

        Args:
            program: The program to get parsers for.
            filetype: If given only return parsers for this filetype.
            input_data: If False only return parsers for output data. If True return
                all parsers.
            driver: If given only return parsers compatible with this driver.

        Returns:
            List of ParserInfo objects.

        """
        try:
            parsers = self.registry[program]
        except KeyError:
            raise KeyError(f"No parsers registered for program '{program}'.")
        if filetype:
            parsers = [p_spec for p_spec in parsers if p_spec.filetype == filetype]
        if not input_data:  # Output data only
            parsers = [p_spec for p_spec in parsers if not p_spec.input_data]
        if only_drivers:
            parsers = [p_spec for p_spec in parsers if driver in p_spec.only_drivers]
        return parsers

    def supported_programs(self) -> List[str]:
        """Get all programs with registered parsers.

        Returns:
            List of program names.
        """
        return list(self.registry.keys())

    def supported_filetypes(self, program: str) -> List[str]:
        """Get all filetypes for a given program.

        Args:
            program: The program to get filetypes for.

        Returns:
            List of filetypes.
        """
        return [str(parser_info.filetype) for parser_info in self.get_parsers(program)]


registry = ParserRegistry()
