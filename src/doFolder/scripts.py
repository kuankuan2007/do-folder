"""
Script entry points for the doFolder package.

This module provides the main entry points for executing doFolder commands
from the command line or programmatically.
"""

import sys
from .cli import compareCli, mainCli, hashCli


def _callCli(cli):
    """
    Execute a CLI function and exit with its return code.

    Args:
        cli: A callable CLI function that returns an integer exit code.

    Note:
        This function calls sys.exit() and will terminate the program.
    """
    sys.exit(cli())


def doCompare():
    """
    Entry point for the folder comparison functionality.

    This function serves as the entry point for the `do-compare` command,
    which allows users to compare two filesystem items (files or directories).
    """
    _callCli(compareCli)


def main():
    """
    Main entry point for the doFolder CLI application.

    This is the primary entry point that handles all doFolder subcommands.
    It routes to the appropriate subcommand handler based on user input.
    """
    _callCli(mainCli)


def doHash():
    _callCli(hashCli)
