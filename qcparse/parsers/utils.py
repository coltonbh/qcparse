import logging
import re

from qcparse.exceptions import MatchNotFoundError

logger = logging.getLogger(__name__)


def re_search(regex: str, contents: str, flags: int = 0) -> re.Match:
    """
    Search for a regex pattern in a string and return the first match.

    Raises:
        MatchNotFoundError if no match is found.
    """
    match = re.search(regex, contents, flags)
    if not match:
        raise MatchNotFoundError(regex, contents)
    return match


def re_finditer(regex: str, contents: str, flags: int = 0) -> list[re.Match]:
    """
    Search for a regex pattern in a string and return all match objects.

    Raises:
        MatchNotFoundError if no matches are found.
    """
    matches = list(re.finditer(regex, contents, flags))
    if not matches:
        raise MatchNotFoundError(regex, contents)
    return matches
