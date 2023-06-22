class BaseError(Exception):
    """Base tcparse exceptions"""


class MatchNotFoundError(BaseError):
    """Exception raised when a parsing match is not found"""
