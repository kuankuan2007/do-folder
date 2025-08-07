"""
This module defines custom exceptions, warnings, and utilities for handling
file system path-related errors and unexpected situations in the doFolder package.
Provides comprehensive error handling with configurable behavior modes.
"""

# pylint: disable=unused-import
import sys
from warnings import warn
from .enums import ErrorMode

# use exceptiongroup if available, else use ExceptionGroup from the standard library
if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pylint: disable=redefined-builtin


class OpenDirectoryError(RuntimeError):
    """
    Raised when attempting to open a directory as if it were a file.
    This exception occurs when file operations are performed on directory paths,
    indicating an incorrect assumption about the path type.
    """


class PathNotExistsError(RuntimeError):
    """
    Raised when attempting to access a file system path that does not exist.
    Use `UnExistsMode` enum to configure the behavior for non-existent paths.
    This error ensures proper handling of missing files or directories.
    """


class PathAreadyExistsError(RuntimeError):
    """
    Raised when attempting to create a file system path that already exists.
    Use `UnExistsMode` enum to configure the behavior for existing paths.
    Prevents accidental overwrites and ensures controlled path creation.
    """


class PathTypeError(RuntimeError):
    """
    Raised when a file system path is not of the expected type (file vs directory).
    This exception indicates a mismatch between the expected and actual path type,
    helping to prevent operations on incorrect path types.
    """


# pylint: disable=unused-import


class PathNotExistsWarning(RuntimeWarning):
    """
    Warning issued when attempting to access a file system path that does not exist.
    Use `UnExistsMode` enum to configure the behavior for non-existent paths.
    Provides non-fatal notification of missing files or directories.
    """


class PathAreadyExistsWarning(RuntimeWarning):
    """
    Warning issued when attempting to create a file system path that already exists.
    Use `UnExistsMode` enum to configure the behavior for existing paths.
    Provides non-fatal notification of path creation conflicts.
    """


class PathTypeWarning(RuntimeWarning):
    """
    Warning issued when a file system path is not of the expected type (file vs directory).
    Provides non-fatal notification of path type mismatches without stopping execution.
    Useful for debugging and monitoring path type assumptions.
    """





def unintended(
    content: str,
    mode: ErrorMode = ErrorMode.WARN,
    *,
    warnClass=RuntimeWarning,
    errorClass=RuntimeError,
):
    """
    Handle unintended or exceptional situations with configurable behavior modes.
    Provides flexible error handling by allowing warnings, exceptions, or silent ignoring.

    This utility function enables consistent error handling across the doFolder package
    by centralizing the logic for different response modes to unexpected conditions.

    Args:
        content (str): A descriptive message explaining the unintended situation.
        mode (ErrorMode, optional): Specifies how to handle the situation:
            - `ErrorMode.WARN`: Issue a warning and continue execution (default).
            - `ErrorMode.ERROR`: Raise an exception and halt execution.
            - `ErrorMode.IGNORE`: Silently ignore the situation and continue.
        warnClass (type, optional): The warning class to use when mode is WARN. 
            Defaults to `RuntimeWarning`.
        errorClass (type, optional): The exception class to raise when mode is ERROR. 
            Defaults to `RuntimeError`.

    Raises:
        errorClass: If `mode` is set to `ErrorMode.ERROR`, raises an exception
                    of the specified `errorClass` with the provided content message.

    Example:
        >>> unintended("File not found", ErrorMode.WARN)  # Issues a warning
        >>> unintended("Critical error", ErrorMode.ERROR)  # Raises RuntimeError
        >>> unintended("Minor issue", ErrorMode.IGNORE)   # Does nothing
    """
    if mode == ErrorMode.WARN:
        warn(content, category=warnClass)
    elif mode == ErrorMode.ERROR:
        raise errorClass(content)
    elif mode == ErrorMode.IGNORE:
        pass
