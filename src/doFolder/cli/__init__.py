"""
Command Line Interface (CLI) module for doFolder.

This package provides the command-line interface components for the doFolder
file system management tool. It includes subcommands for various operations
like comparing directories and files.

Available CLI Functions:
    - compareCli: Command-line interface for folder/file comparison
    - mainCli: Main CLI dispatcher for all subcommands
"""

from .compare import compareCli
from .main import mainCli
from .hash import hashCli

__all__ = [
    "compareCli",
    "mainCli",
    "hashCli",
]
