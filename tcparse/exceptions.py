class BaseException(Exception):
    """Base tcparse exceptions"""


class MatchNotFoundError(BaseException):
    """Exception raised when a parsing match is not found"""
