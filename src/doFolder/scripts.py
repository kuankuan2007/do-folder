"""
Script entry points for the doFolder package.

This module provides the main entry points for executing doFolder commands
from the command line or programmatically.
"""

import os

from .cli import compareCli, mainCli, hashCli, util
from . import __pkginfo__




def _callCli(cli, *args, **kwargs):
    """
    Execute a CLI function and exit with its return code.

    Args:
        cli: A callable CLI function that returns an integer exit code.

    Note:
        This function calls sys.exit() and will terminate the program.
    """
    os._exit(cli(*args, **kwargs))


def doCompare():
    """
    Entry point for the folder comparison functionality.

    This function serves as the entry point for the `do-compare` command,
    which allows users to compare two filesystem items (files or directories).
    """
    _callCli(compareCli)


def main():
    """
    the __main__ entry point for the doFolder CLI application.
    """

    _callCli(
        mainCli,
        prog=(
            util.getBestInvocationForThisPython() + " -m " + __pkginfo__.__package__
            if __pkginfo__.__package__
            else "do-folder"
        ),
    )


def doFolder():
    """
    Main entry point for the doFolder CLI application.

    This is the primary entry point that handles all doFolder subcommands.
    It routes to the appropriate subcommand handler based on user input.
    """
    _callCli(mainCli)


def doHash():
    """Entry point for hash calculation CLI command."""
    _callCli(hashCli)
