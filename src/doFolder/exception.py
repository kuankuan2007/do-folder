# pylint: disable=unused-import
import sys

from exceptiongroup import ExceptionGroup  # pylint: disable=redefined-builtin

class OpenDirectoryError(RuntimeError):
    pass

class PathNotExistsError(RuntimeError):
    pass
