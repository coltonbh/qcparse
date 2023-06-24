"""Simple data models to support parsing of QM program output files."""

from types import SimpleNamespace
from typing import Dict


class ParsedDataCollector(SimpleNamespace):
    """A namespace that only allows attributes to be set once."""

    def __setattr__(self, name, value):
        """Only allow attributes to be set once on the object.

        This provides a sanity check on parsers to make sure they are not overwriting
        values that have already been set by another parser. There should only ever be
        one parser for one value for a given program and filetype.

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

    def dict(self) -> Dict:
        """Convert the namespace to a dictionary, including nested objects."""
        if isinstance(self, ParsedDataCollector):
            return {
                key: value.dict() if isinstance(value, ParsedDataCollector) else value
                for key, value in vars(self).items()
            }
        elif isinstance(self, list):
            return [
                item.dict() if isinstance(item, ParsedDataCollector) else item
                for item in self
            ]
        else:
            return self


def single_point_data_collector() -> ParsedDataCollector:
    """Create a namespace for a single point result."""
    output_obj = ParsedDataCollector()
    # Input Objects
    output_obj.input_data = ParsedDataCollector()
    output_obj.input_data.program_args = ParsedDataCollector()
    output_obj.input_data.program_args.model = ParsedDataCollector()

    # Output Objects
    output_obj.computed = ParsedDataCollector()
    output_obj.provenance = ParsedDataCollector()
    output_obj.extras = ParsedDataCollector()

    # Scratch just for parsers
    output_obj.scratch = ParsedDataCollector()

    return output_obj
