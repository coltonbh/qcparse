import re
from pathlib import Path
from typing import Union

from qcio import Molecule

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


def get_file_content(data_or_path: Union[str, bytes, Path]) -> Union[str, bytes]:
    """Return the file content from a path, str, or bytes."""
    file_content: Union[str, bytes]

    if isinstance(data_or_path, bytes):
        return data_or_path

    try:
        filepath = Path(data_or_path)
    except OSError:
        # String too long to be filepath
        file_content = str(data_or_path)
    else:
        if filepath.is_file():
            # Read the file contents
            file_content = filepath.read_bytes()
            try:
                file_content = file_content.decode("utf-8")
            except UnicodeDecodeError:
                pass
        else:
            file_content = str(data_or_path)

    return file_content
