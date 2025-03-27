"""Simple data models to support parsing of QM program output files."""

from collections import defaultdict
from typing import Any, Callable, Optional, Tuple, Union

from pydantic import BaseModel, model_validator
from qcio import CalcType

from .exceptions import DataCollectorError, RegistryError


class ParserSpec(BaseModel):
    """Information about a parser function.

    Attributes:
        parser: The parser function.
        filetype: The filetype that the parser is for.
        required: Whether the parser is required to be successful for the parsing to
            be considered successful. If True and the parser fails a MatchNotFoundError
            will be raised. If False and the parser fails the value will be ignored.
        calctypes: The calculation types that the parser work on.
        target: The location on the data collector where the parser's output should be placed.
    """

    parser: Callable
    filetype: str
    required: bool
    calctypes: list[CalcType]
    target: Optional[Union[str, Tuple[str, ...]]] = None


class ParserRegistry(BaseModel):
    """Registry for parser functions."""

    registry: dict[str, list[ParserSpec]] = defaultdict(list)

    def register(self, program: str, parser_spec: ParserSpec) -> None:
        """Register a new parser function. Enforce that no two parsers for the same program use the same target.

        Args:
            program: The program that the parser is for.
            parser_spec: ParserSpec objects containing the parser function and
                information about the parser.
        """
        # Ensure all non-directory parsers have a target
        if parser_spec.target is None and not parser_spec.filetype == "directory":
            raise RegistryError(
                f"Parser '{parser_spec.parser.__name__}' for program '{program}' must "
                "have a target if it is not a directory parser."
            )

        # Ensure that the target is unique for the program and filetype
        for registered_spec in self.registry.get(program, []):
            if (
                parser_spec.target is not None  # not directory parser
                and registered_spec.target == parser_spec.target  # Same target
                and set(parser_spec.calctypes)
                & set(registered_spec.calctypes)  # Shared
            ):
                raise RegistryError(
                    f"Duplicate parser target '{parser_spec.target}' and calctype "
                    f"'{set(parser_spec.calctypes)& set(registered_spec.calctypes)}' "
                    f"registered for program '{program}'."
                )
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
            filetype: Filter parsers for this filetype.
            calctype: Filter parsers for this calctype.

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
            {str(parser_info.filetype) for parser_info in self.get_parsers(program)}
        )


registry = ParserRegistry()


class DataCollector(dict):
    """A dictionary for collecting data from parsers."""

    def add_data(self, target: Union[str, Tuple[str, ...]], value: Any) -> None:
        """
        Assign a value into the DataCollector at the specified target.

        If target is a string, the value is assigned to that key.
        If target is a tuple, the method navigates through nested dictionaries,
        creating them as needed, and assigns the value at the final key.
        """
        keys = target if isinstance(target, tuple) else (target,)
        d = self
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        if keys[-1] in d:
            raise DataCollectorError(
                f"Target '{keys}' already exists in DataCollector. You cannot add the same target twice."
            )
        d[keys[-1]] = value


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
