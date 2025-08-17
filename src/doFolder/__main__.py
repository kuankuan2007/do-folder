"""
Main entry point when doFolder is executed as a module.

This module is executed when the package is run directly with:
    python -m doFolder [arguments]

It imports and calls the main function from the scripts module.
"""

from .scripts import main

main()
