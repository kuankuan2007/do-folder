"""
Main CLI entry point for the doFolder package.

This module provides the unified command-line interface that routes
to various subcommand implementations.
"""

from .. import globalType as _tt
from . import util
from .compare import compareCli
from .hash import hashCli

#: Dictionary mapping subcommand names to their corresponding CLI functions
SUBCOMMANDS = {"compare": compareCli, "hash": hashCli}


def mainCli(arguments: _tt.Optional[_tt.Sequence[str]] = None, prog=None) -> int:
    """
    The unified entry point for the doFolder CLI application.

    This function serves as the main dispatcher for all doFolder subcommands.
    It parses the command line arguments and routes execution to the appropriate
    subcommand handler.

    Returns:
        int: Exit code from the executed subcommand (0 for success, non-zero for failure).

    Raises:
        SystemExit: When an unknown subcommand is provided or parsing fails.

    Example:
        This function is typically called when users run:
        - `do-folder compare path1 path2`
        - `python -m doFolder compare path1 path2`
    """
    parser = util.argparse.ArgumentParser(prog=prog)
    util.addVersionInfo(parser)
    parser.add_argument(
        "subcommand", help="something to do", choices=list(SUBCOMMANDS.keys())
    )

    parser.add_argument(
        "args", nargs=util.argparse.REMAINDER, help="arguments for the subcommand"
    )
    args = parser.parse_args(arguments)

    if args.subcommand not in SUBCOMMANDS:
        parser.error(f"Unknown subcommand: {args.subcommand}")

    return SUBCOMMANDS[args.subcommand](
        args.args, prog=prog + " " + args.subcommand if prog else None
    )
