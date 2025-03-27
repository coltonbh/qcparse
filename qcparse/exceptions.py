class BaseError(Exception):
    """Base qcparse exceptions"""


class DecoderError(BaseError):
    """Exception raised when a decoder error occurs"""


class ParserError(BaseError):
    """Base exception for parsers"""


class MatchNotFoundError(ParserError):
    """Exception raised when a parsing match is not found"""

    def __init__(self, regex: str, string: str):
        self.regex = regex
        self.string = string
        super().__init__(
            f"Could not locate match for regex: '{regex}' in string: '{string}'"
        )


class RegistryError(BaseError):
    """Exception raised when a registry error occurs"""


class EncoderError(BaseError):
    """Exception raised when a encoder error occurs"""


class DataCollectorError(BaseError):
    """Exception raised when a data collector error occurs"""
