"""
This module defines custom exceptions, warnings, and utilities for handling
unexpected situations in the doFolder package.
"""

# pylint: disable=unused-import
import sys
from enum import Enum
from warnings import warn

# use exceptiongroup if available, else use ExceptionGroup from the standard library
if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pylint: disable=redefined-builtin


class OpenDirectoryError(RuntimeError):
    """
    Raised when attempting to open a directory as if it were a file.
    """


class PathNotExistsError(RuntimeError):
    """
    Raised when attempting to access a path that does not exist.
    Use `UnExistsMode` to configure the behavior for non-existent paths.
    """


class PathAreadyExistsError(RuntimeError):
    """
    Raised when attempting to create a path that already exists.
    Use `UnExistsMode` to configure the behavior for existing paths.
    """


class PathTypeError(RuntimeError):
    """
    Raised when a path is not of the expected type (e.g., file vs directory).
    """


# pylint: disable=unused-import


class PathNotExistsWarning(RuntimeWarning):
    """
    Warning issued when attempting to access a path that does not exist.
    Use `UnExistsMode` to configure the behavior for non-existent paths.
    """


class PathAreadyExistsWarning(RuntimeWarning):
    """
    Warning issued when attempting to create a path that already exists.
    Use `UnExistsMode` to configure the behavior for existing paths.
    """


class PathTypeWarning(RuntimeWarning):
    """
    Warning issued when a path is not of the expected type (e.g., file vs directory).
    """


class ErrorMode(Enum):
    """
    Enum representing modes for handling errors or warnings.

    Attributes:
        WARN: Issue a warning.
        ERROR: Raise an exception.
        IGNORE: Ignore the situation.
    """
    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"


def unintended(
    content: str,
    mode: ErrorMode = ErrorMode.WARN,
    *,
    warnClass=RuntimeWarning,
    errorClass=RuntimeError,
):
    """
    Handle unintended situations by issuing warnings, raising exceptions,
    or ignoring them based on the specified mode.

    Args:
        content (str): A message describing the unintended situation.
        mode (ErrorMode, optional): Specifies how to handle the situation.
            - `ErrorMode.WARN`: Issue a warning (default).
            - `ErrorMode.ERROR`: Raise an exception.
            - `ErrorMode.IGNORE`: Ignore the situation.
        warnClass (type, optional): The warning class to use. Defaults to `RuntimeWarning`.
        errorClass (type, optional): The exception class to use. Defaults to `RuntimeError`.

    Raises:
        errorClass: If `mode` is set to `ErrorMode.ERROR`, raises an exception
                    of the specified `errorClass`.
    """
    if mode == ErrorMode.WARN:
        warn(content, category=warnClass)
    elif mode == ErrorMode.ERROR:
        raise errorClass(content)
    elif mode == ErrorMode.IGNORE:
        pass
