from qcio import Molecule
import re
from qcparse.exceptions import MatchNotFoundError

hydrogen_atom = Molecule(symbols=["H"], geometry=[[0, 0, 0]])


def regex_search(regex: str, string: str) -> re.Match:
    """Function for matching a regex to a string.

    Will match and return the first match found or raise MatchNotFoundError
    if no match is found.

    Args:
        regex: A regular expression string.
        string: The string to match on.

    Returns:
        The re.Match object, if a match is found.

    Raises:
        MatchNotFoundError if no match found.
    """
    match = re.search(regex, string)
    if not match:
        raise MatchNotFoundError(regex, string)
    return match
