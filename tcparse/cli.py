import argparse
import json
import sys
from pathlib import Path

from .main import parse


def main():
    parser = argparse.ArgumentParser(
        description="Parse TeraChem stdout files into structured JSON and Python objects."
    )
    parser.add_argument("filename", help="path to the file")
    parser.add_argument(
        "--ignore_xyz",
        action="store_true",
        help="Ignore the XYZ file specified in TeraChem stdout. Use a proxy hydrogen atom instead.",
    )

    args = parser.parse_args()

    result = parse(Path(args.filename), ignore_xyz=args.ignore_xyz)
    # Hacking in pretty print since probably preferred for most users
    # Can update to result.json(indent=4) when this PR accepted
    # https://github.com/MolSSI/QCElemental/pull/307
    print(json.dumps(json.loads(result.json()), indent=4), file=sys.stdout)
