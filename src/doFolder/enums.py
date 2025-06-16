"""
This module defines some enums used throughout the library.
"""
from enum import Enum, Flag, auto


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


class CompareModeFlag(Flag):
    """
    Enum representing the mode for comparing items.
    """
    TIMETAG = auto()
    CONTENT = auto()
    SIZE = auto()


class CompareMode(Enum):
    """
    Enum representing the mode for comparing items.
    """

    TIMETAG = CompareModeFlag.TIMETAG
    CONTENT = CompareModeFlag.CONTENT
    SIZE = CompareModeFlag.SIZE
    TIMETAG_AND_SIZE = TIMETAG | SIZE
    IGNORE= CompareModeFlag(0)

class DifferenceType(Enum):
    """
    Enum representing the type of difference between two file system items.
    """
    FILE_DIFFERENCE = "file_difference"
    DIRECTORY_DIFFERENCE = "directory_difference"
    NOT_EXISTS = "not_exists"
    ITEM_TYPE_DIFFERENCE = "item_type_difference"
