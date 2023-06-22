from collections import defaultdict
from typing import Callable, Dict, List

from pydantic import BaseModel


class ParserInfo(BaseModel):
    """Information about a parser function."""

    filetype: str
    required: bool
    parser: Callable


class ParserRegistry(BaseModel):
    """Registry for parser functions."""

    registry: Dict[str, List[ParserInfo]] = defaultdict(list)

    def register(
        self, program: str, filetype: str, required: bool, function: Callable
    ) -> None:
        """Register a new parser function.

        Args:
            program: The program that the parser is for.
            filetype: The filetype that the parser is for.
            required: Whether the parser is required to be successful for the parsing to
                be considered successful. If True and the parser fails a MatchNotFoundError
                will be raised. If False and the parser fails the value will be ignored.
            function: The parser function.
        """
        parser_info = ParserInfo(filetype=filetype, required=required, parser=function)
        self.registry[program].append(parser_info)

    def get_parsers(self, program: str) -> List[ParserInfo]:
        """Get all parser functions for a given program."""
        return self.registry.get(program, [])


parser_registry = ParserRegistry()
