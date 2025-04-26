"""

"""

# pylint: disable=unused-import
import sys

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
