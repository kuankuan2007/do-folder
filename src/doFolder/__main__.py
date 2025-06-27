"""
The union entry point for the doFolder CLI.
"""

import argparse
import sys

from .cli import compareCli

subcommands = {
    "compare": compareCli,
}


def main():
    """The union entry point for the doFolder CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("subcommand", help="something to do", choices=["compare"])
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="arguments for the subcommand"
    )
    args = parser.parse_args()
    if args.subcommand not in subcommands:
        parser.error(f"Unknown subcommand: {args.subcommand}")
    exitcode = subcommands[args.subcommand](*args.args)
    sys.exit(exitcode)


main()
