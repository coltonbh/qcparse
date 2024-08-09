from .utils import regex_search


def parse_version_string(string: str) -> str:
    """Parse version string from CREST stdout.

    Matches format of 'crest --version' on command line.
    """
    regex = r"Version (\d+\.\d+\.\d+),"
    match = regex_search(regex, string)
    return match.group(1)
