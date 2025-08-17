"""
Main CLI entry point for the doFolder package.

This module provides the unified command-line interface that routes
to various subcommand implementations.
"""

from . import util, compare

#: Dictionary mapping subcommand names to their corresponding CLI functions
SUBCOMMANDS = {"compare": compare.compareCli}


def mainCli():
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
    parser = util.argparse.ArgumentParser()
    util.addVersionInfo(parser)
    parser.add_argument("subcommand", help="something to do", choices=["compare"])

    parser.add_argument(
        "args", nargs=util.argparse.REMAINDER, help="arguments for the subcommand"
    )
    args = parser.parse_args()

    if args.subcommand not in SUBCOMMANDS:
        parser.error(f"Unknown subcommand: {args.subcommand}")

    return SUBCOMMANDS[args.subcommand](args.args)
