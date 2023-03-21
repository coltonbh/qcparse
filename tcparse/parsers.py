import re

from .exceptions import MatchNotFoundError


def parse_final_energy(input: str) -> float:
    """Parse the final energy from TeraChem stdout

    Args:
        input: TeraChem stdout string

    Returns:
        The final energy of the molecule

    Raises:
        MatchNotFoundError: If no match is found
    """
    regex = r"FINAL ENERGY: (-?\d+(?:\.\d+)?)"
    match = re.search(regex, input)
    if not match:
        raise MatchNotFoundError(
            f"Could not locate final energy in string {input} using regex: '{regex}'"
        )
    return float(match.group(1))
