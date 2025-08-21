"""
Python runtime environment information module for doFolder.

This module provides essential Python runtime environment information and constants
used throughout the doFolder library. It exposes Python version details, interpreter
path, and runtime features like GIL (Global Interpreter Lock) status for compatibility
checking and environment-aware operations.
"""

# pylint: disable=unused-import, no-name-in-module
import sys as _sys

#: Python version information as a named tuple (major, minor, micro, releaselevel, serial)
PYTHON_VERSION_INFO = _sys.version_info

#: Complete Python version string including build info and compiler details
PYTHON_VERSION_STR = _sys.version

#: Path to the Python executable currently running
PYTHON_EXECUTABLE = _sys.executable

#: Whether the Global Interpreter Lock (GIL) is disabled in this Python build
PYTHON_GIL_DISABLED = (
    not _sys._is_gil_enabled()  # pylint: disable=protected-access # type: ignore
    if hasattr(_sys, "_is_gil_enabled")
    else False
)
