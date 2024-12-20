"""Simple data models to support parsing of QM program output files."""

from collections import defaultdict
from enum import Enum
from types import SimpleNamespace
from typing import Callable, Optional

from pydantic import BaseModel, model_validator
from qcio import CalcType

from .exceptions import RegistryError


class ParserSpec(BaseModel):
    """Information about a parser function.

    Attributes:
        parser: The parser function.
        filetype: The filetype that the parser is for.
        required: Whether the parser is required to be successful for the parsing to
            be considered successful. If True and the parser fails a MatchNotFoundError
            will be raised. If False and the parser fails the value will be ignored.
        calctypes: The calculation types that the parser work on.
    """

    parser: Callable
    filetype: str
    required: bool
    calctypes: list[CalcType]


class ParserRegistry(BaseModel):
    """Registry for parser functions."""

    registry: dict[str, list[ParserSpec]] = defaultdict(list)

    def register(self, program: str, parser_spec: ParserSpec) -> None:
        """Register a new parser function.

        Args:
            program: The program that the parser is for.
            parser_spec: ParserSpec objects containing the parser function and
                information about the parser.
        """
        self.registry[program].append(parser_spec)

    def get_parsers(
        self,
        program: str,
        filetype: Optional[str] = None,
        calctype: Optional[CalcType] = None,
    ) -> list[ParserSpec]:
        """Get all parser functions for a given program.

        Args:
            program: The program to get parsers for.
            filetype: If given only return parsers for this filetype.
            calctype: Filter parsers for a given calculation type.

        Returns:
            List of ParserSpec objects.
        """

        parser_specs: list[ParserSpec] = self.registry[program]
        if not parser_specs:
            raise RegistryError(f"No parsers registered for program '{program}'.")

        # Filter parsers by filetype and calctype
        if filetype:
            parser_specs = [ps for ps in parser_specs if ps.filetype == filetype]

        if calctype:
            parser_specs = [ps for ps in parser_specs if calctype in ps.calctypes]
        return parser_specs

    def supported_programs(self) -> list[str]:
        """Get all programs with registered parsers.

        Returns:
            List of program names.
        """
        return list(self.registry.keys())

    def supported_filetypes(self, program: str) -> list[str]:
        """Get all filetypes for a given program.

        Args:
            program: The program to get filetypes for.

        Returns:
            List of filetypes.
        """
        return list(
            {
                str(parser_info.filetype) for parser_info in self.get_parsers(program)
            }
        )


registry = ParserRegistry()


class ParsedDataCollector(SimpleNamespace):
    """A namespace that only allows attributes to be set once."""

    def __setattr__(self, name, value):
        """Only allow attributes to be set once on the object.

        This provides a sanity check on parsers to make sure they are not overwriting
        values that have already been set by another parser. There should only ever be
        one parser per value for a given program and filetype.

        >>> from qcparse.models import ParsedDataCollector
        >>> obj = ParsedDataCollector()
        >>> obj.value = 1
        >>> obj.value
        1
        >>> obj.value = 2
        AttributeError: This attribute has already been set by another parser and ...
        ...
        """
        if name in self.__dict__:
            raise AttributeError(
                f"The attribute '{name}' has already been set by another parser and "
                "cannot be set again."
            )
        super().__setattr__(name, value)

    def dict(self) -> dict:
        """Convert the namespace to a dictionary, including nested objects."""
        return {
            key: (
                value.dict()
                if isinstance(value, ParsedDataCollector)
                else (
                    [
                        item.dict() if isinstance(item, ParsedDataCollector) else item
                        for item in value
                    ]
                    if isinstance(value, list)
                    else value
                )
            )
            for key, value in vars(self).items()
        }


def single_point_results_namespace() -> ParsedDataCollector:
    """Create a namespace for a qcio.SinglePointResult."""
    output_obj = ParsedDataCollector()
    output_obj.extras = ParsedDataCollector()

    return output_obj


class FileType(str, Enum):
    """Enum of supported TeraChem filetypes."""

    stdout = "stdout"


class NativeInput(BaseModel):
    """Native input file data. Writing these files to disk should produce a valid input.

    Attributes:
        input_file: input file for the program
        geometry: xyz file or other geometry file required for the calculation
        geometry_filename: filename of the geometry file referenced in the input
    """

    input_file: str
    geometry_file: Optional[str] = None
    geometry_filename: Optional[str] = None

    @model_validator(mode="after")
    def ensure_geometry_filename(self):
        """Ensure that geometry_filename is set if geometry is set."""
        if self.geometry_file and not self.geometry_filename:
            raise ValueError(
                "geometry_filename must be set if geometry is set. "
                "Set geometry_filename to the name of the geometry file as referenced "
                "in the input file."
            )
        return self
