"""
Utility functions for file system operations.

This module provides helper functions for creating file system items, type checking,
and converting between different file system representations.

.. versionadded:: 2.3.0
"""

from .. import (
    exception as _ex,
    globalType as _tt,
)

from . import classes as _classes
from ..enums import ErrorMode, ItemType, UnExistsMode
from ..path import Path

from . import classes as _classes  # pylint: disable=cyclic-import


def isDir(target: "_classes.FileSystemItemBase") -> " _tt.TypeIs[_classes.Directory]":
    """Check if target is a directory.

    Args:
        target (_classes.FileSystemItemBase): The file system item to check.

    Returns:
        bool: True if target is a directory, False otherwise.
    """
    return target.itemType == _classes.ItemType.DIR


def isFile(target: "_classes.FileSystemItemBase") -> " _tt.TypeIs[_classes.File]":
    """Check if target is a file.

    Args:
        target (_classes.FileSystemItemBase): The file system item to check.

    Returns:
        bool: True if target is a file, False otherwise.
    """
    return target.itemType == _classes.ItemType.FILE


def createItem(
    path: _tt.Pathable,
    unExistsMode: UnExistsMode = UnExistsMode.WARN,
    errorMode: ErrorMode = ErrorMode.WARN,
    toAbsolute: bool = False,
    exceptType: _tt.Union[ItemType, None] = None,
) -> "_classes.FileSystemItem":
    """Create a file system item based on the given path.

    Automatically detects whether the path points to a file or directory and creates
    the appropriate object. If the path doesn't exist, behavior is controlled by
    unExistsMode parameter.

    Args:
        path (Pathable): Path to the file or directory.
        unExistsMode (UnExistsMode, optional): Behavior when path doesn't exist. Defaults to WARN.
        errorMode (ErrorMode, optional): Error handling mode. Defaults to WARN.
        toAbsolute (bool, optional): Convert path to absolute. Defaults to False.
        exceptType (ItemType, optional): Expected item type (FILE or DIR). Defaults to None.

    Returns:
        _classes.FileSystemItem: File or Directory object based on the path type.
    """
    path = Path(path)
    if path.exists():
        if path.is_file():
            return _classes.File(path, unExistsMode, errorMode, toAbsolute)
        if path.is_dir():
            return _classes.Directory(path, unExistsMode, errorMode, toAbsolute)
        _ex.unintended(
            f"Path {path} is not a file or directory",
            errorMode,
            errorClass=_ex.PathTypeError,
            warnClass=_ex.PathTypeWarning,
        )
    return (_classes.Directory if exceptType == ItemType.DIR else _classes.File)(
        path, unExistsMode, errorMode, toAbsolute, exceptType=exceptType
    )


def toFileSystemItem(fr: "_classes.FileSystemItemLike") -> "_classes.FileSystemItem":
    """Convert FileSystemItemLike to FileSystemItem.

    Args:
        fr (_classes.FileSystemItemLike): Object to convert (_classes.FileSystemItemLike).

    Returns:
        _classes.FileSystemItem: FileSystemItem object.

    .. versionadded:: 2.2.0
    """
    if isinstance(fr, _classes.FileSystemItemBase):
        return fr
    return createItem(fr)
