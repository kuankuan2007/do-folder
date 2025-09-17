"""
Script entry points for the doFolder package.

This module provides the main entry points for executing doFolder commands
from the command line or programmatically.
"""

import os
import sys
import shutil

from .cli import compareCli, mainCli, hashCli
from . import __pkginfo__


def _getBestInvocationForThisPython() -> str:
    """
    Try to figure out the best way to invoke the current Python.

    This function was copied from the `pip` package. It attempts to
    determine the most appropriate command to invoke the current Python

    Thank you to the team that maintains pip. Your code is very useful.
    """
    exe = sys.executable
    exeName = os.path.basename(exe)

    foundExecutable = shutil.which(exeName)
    if foundExecutable and os.path.samefile(foundExecutable, exe):
        return exeName

    return exe


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
            _getBestInvocationForThisPython() + " -m " + __pkginfo__.__package__
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
