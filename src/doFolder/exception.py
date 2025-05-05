"""
This module contains the exceptions and warnings used in the doFolder package.
It will be imported in other modules as _ex
"""

# pylint: disable=unused-import
import sys
from enum import Enum
from warnings import warn

# use exceptiongroup if available, else use ExceptionGroup from the standard library
if sys.version_info >= (3, 11):
    from exceptiongroup import ExceptionGroup  # pylint: disable=redefined-builtin


class OpenDirectoryError(RuntimeError):
    """
    The exception raised when the program try opening a directory as a file.
    """


class PathNotExistsError(RuntimeError):
    """
    The exception raised when the program try to access a path that does not exist.
    You can use UnExistsMode to change the operation of the program when the path does not exist
    """


class PathIsNotDirError(RuntimeError):
    """
    The exception raised when the program try to access a path that is not a directory.
    You can use UnExistsMode to change the operation of the program when the path is not a directory
    """


# pylint: disable=unused-import


class PathNotExistsWarning(RuntimeWarning):
    """
    The warning raised when the program try to access a path that does not exist.
    You can use UnExistsMode to change the operation of the program when the path does not exist
    """


class PathIsNotDirWarning(RuntimeWarning):
    """
    The warning raised when the program try to access a path that is not a directory.
    You can use UnExistsMode to change the operation of the program when the path is not a directory
    """


class ErrorMode(Enum):
    """
    The enum class for the error mode.
    """

    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"


def unintended(
    content: str,
    mode: ErrorMode = ErrorMode.WARN,
    warnClass=RuntimeWarning,
    errorClass=RuntimeError,
):
    """
    Handles unintended situations by raising warnings, errors,
    or ignoring them based on the specified mode.

    Args:
        content (str): The message describing the unintended situation.
        mode (ErrorMode, optional): Specifies how to handle the situation.
            - ErrorMode.WARN: Issues a warning (default).
            - ErrorMode.ERROR: Raises an exception.
            - ErrorMode.IGNORE: Ignores the situation.
        warnClass (type, optional): The class of the warning to be issued.
                                        Defaults to RuntimeWarning.
        errorClass (type, optional): The class of the exception to be raised.
                                            Defaults to RuntimeError.

    Raises:
        errorClass: If mode is set to ErrorMode.ERROR,
            raises an exception of the specified errorClass.
    """
    if mode == ErrorMode.WARN:
        warn(content, category=warnClass)
    elif mode == ErrorMode.ERROR:
        raise errorClass(content)
    elif mode == ErrorMode.IGNORE:
        pass
