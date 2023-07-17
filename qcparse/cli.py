import argparse
import json
from pathlib import Path

from .main import parse_results


def main():
    parser = argparse.ArgumentParser(
        description="Parse Quantum Chemistry output files into structured JSON or "
        "Python objects."
    )
    parser.add_argument("program", help="Name of the program")
    parser.add_argument("filepath", help="Path to the file")
    parser.add_argument(
        "--filetype", help="Type of file. Defaults to 'stdout'", default="stdout"
    )

    args = parser.parse_args()

    computed_props = parse_results(Path(args.filepath), args.program, args.filetype)
    # Hacking in pretty print since probably preferred for most users
    # Can update to result.json(indent=4) when this PR accepted
    # https://github.com/MolSSI/QCElemental/pull/307
    print(json.dumps(computed_props.dict(), indent=4))
