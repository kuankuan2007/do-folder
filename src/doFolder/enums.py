"""
This module defines some enums used throughout the library.
"""
from enum import Enum
class ErrorMode(Enum):
    """
    Enum representing modes for handling errors or warnings.
    """

    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"


class UnExistsMode(Enum):
    """
    Enum representing the behavior when a path does not exist.
    """

    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"
    CREATE = "create"


class ItemType(Enum):
    """
    Enum representing the type of a file system item.
    """

    FILE = "file"
    DIR = "dir"
