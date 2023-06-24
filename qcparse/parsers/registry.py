from collections import defaultdict
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel

from qcio import CalcType


class ParserSpec(BaseModel):
    """Information about a parser function.

    Attributes:
        parser: The parser function.
        filetype: The filetype that the parser is for.
        required: Whether the parser is required to be successful for the parsing to
            be considered successful. If True and the parser fails a MatchNotFoundError
            will be raised. If False and the parser fails the value will be ignored.
        calc_types: The calculation types that the parser work on.
    """

    parser: Callable
    filetype: str
    required: bool
    input_data: bool = False
    calc_types: List[CalcType]


class ParserRegistry(BaseModel):
    """Registry for parser functions."""

    registry: Dict[str, List[ParserSpec]] = defaultdict(list)

    def register(
        self,
        program: str,
        parser: Callable,
        filetype: str,
        required: bool,
        input_data: bool,
        only: Optional[List[CalcType]],
    ) -> None:
        """Register a new parser function.

        Args:
            program: The program that the parser is for.
            parser: The parser function.
            filetype: The filetype that the parser is for.
            required: Whether the parser is required to be successful for the parsing to
                be considered successful. If True and the parser fails a MatchNotFoundError
                will be raised. If False and the parser fails the value will be ignored.
            only: The calculation types that the parser is for. If None the
                parser will be registered for all calculation types.
        """
        parser_info = ParserSpec(
            parser=parser,
            filetype=filetype,
            required=required,
            input_data=input_data,
            # If only not passed then register for all calculation types
            calc_types=only or [CalcType.energy, CalcType.gradient, CalcType.hessian],
        )
        self.registry[program].append(parser_info)

    def get_parsers(
        self,
        program: str,
        filetype: Optional[str] = None,
        output_only: bool = False,
        calc_type: Optional[CalcType] = None,
    ) -> List[ParserSpec]:
        """Get all parser functions for a given program.

        Args:
            program: The program to get parsers for.
            filetype: If given only return parsers for this filetype.
            output_only: If True return only parsers for output data.
            calc_type: Filter parsers for a given calculation type.

        Returns:
            List of ParserSpec objects.

        """
        try:
            parsers: List[ParserSpec] = self.registry[program]
        except KeyError:
            raise KeyError(f"No parsers registered for program '{program}'.")

        if filetype:
            parsers = [p_spec for p_spec in parsers if p_spec.filetype == filetype]

        if output_only:
            parsers = [p_spec for p_spec in parsers if not p_spec.input_data]

        if calc_type:
            parsers = [p_spec for p_spec in parsers if calc_type in p_spec.calc_types]
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
