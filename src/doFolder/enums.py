"""
Enumeration definitions for doFolder file system operations and configurations.

This module defines comprehensive enums that control behavior across the doFolder library,
including error handling modes, file system item types, comparison strategies, and hash recalculation policies.
"""

from enum import Enum, Flag, auto


class ErrorMode(Enum):
    """
    Defines how the library handles error conditions during file system operations.
    Controls whether operations should raise exceptions, emit warnings, or silently ignore issues.
    """

    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"


class UnExistsMode(Enum):
    """
    Specifies behavior when attempting to operate on non-existent file system paths.
    Determines whether to create missing paths, raise errors, emit warnings, or ignore the condition.
    """

    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"
    CREATE = "create"


class ItemType(Enum):
    """
    Distinguishes between file system item types for creation and type checking operations.
    Used throughout the library to specify whether operations target files or directories.
    """

    FILE = "file"
    DIR = "dir"


class CompareModeFlag(Flag):
    """
    Individual comparison criteria flags that can be combined using bitwise operations.
    These flags form the building blocks for comprehensive file and directory comparison strategies.
    """

    TIMETAG = auto()
    CONTENT = auto()
    SIZE = auto()


class CompareMode(Enum):
    """
    Predefined comparison strategies for file and directory comparison operations.
    Combines individual comparison flags to provide commonly used comparison modes with optimized performance.
    """

    TIMETAG = CompareModeFlag.TIMETAG
    CONTENT = CompareModeFlag.CONTENT
    SIZE = CompareModeFlag.SIZE
    TIMETAG_AND_SIZE = TIMETAG | SIZE
    IGNORE = CompareModeFlag(0)


class DifferenceType(Enum):
    """
    Categorizes the types of differences detected during file system item comparisons.
    Used by comparison operations to classify and report specific types of discrepancies between items.
    """

    FILE_DIFFERENCE = "file_difference"
    DIRECTORY_DIFFERENCE = "directory_difference"
    NOT_EXISTS = "not_exists"
    ITEM_TYPE_DIFFERENCE = "item_type_difference"

class ReCalcHashMode(Enum):
    """
    Controls when file hash values should be recalculated during hash-based operations.
    Optimizes performance by determining hash computation frequency based on file modification timestamps.
    """

    TIMETAG = "TIME_TAG"
    NEVER = "NEVER"
    ALWAYS = "ALWAYS"
