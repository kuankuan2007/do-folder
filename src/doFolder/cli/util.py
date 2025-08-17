"""
Utility functions and constants for the doFolder CLI module.

This module provides common utilities used across different CLI components,
including version information handling and argument parser configuration.
"""

import argparse

from .. import env as _env, __pkginfo__ as _pkginfo

#: Short version string containing package name and version
VERSION_STRING = f"{_pkginfo.__pkgname__} {_pkginfo.__version__}"

#: Full version string including Python version and executable path
FULL_VERSION_STRING = f"{_pkginfo.__pkgname__} {_pkginfo.__version__} From Python {_env.PYTHON_VERSION_STR}({_env.PYTHON_EXECUTABLE})"


def addVersionInfo(parser: argparse.ArgumentParser):
    """
    Add version information arguments to an ArgumentParser.
    
    This function adds two version-related arguments:
    - `-v, --version`: Shows short version information
    - `-vv, --full-version`: Shows detailed version information including Python details
    
    Args:
        parser (argparse.ArgumentParser): The argument parser to add version info to.
        
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> addVersionInfo(parser)
        >>> # Parser now has -v/--version and -vv/--full-version arguments
    """
    parser.add_argument("-v", "--version", action="version", version=VERSION_STRING)
    parser.add_argument(
        "-vv", "--full-version", action="version", version=FULL_VERSION_STRING
    )
