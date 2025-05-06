"""
doFolder - A Python library for file and directory management.
~~~~~~

example:
    >>> import doFolder
    >>> a = Directory("./") # create a Directory object for the current directory
    >>> a.create("test3", CreateType.FILE) # create a file named test3 in the current directory
    >>> a.create("test4", CreateType.DIR) # create a directory named test4 in the current directory
    >>> a.["test3"].content = "123456".encode("utf-8") # write content to the file test3
    ...

:copyright: (c) 2023-2025 by kuankuan2007.
:license: MulanPSL-2.0, see LICENSE for more details.
"""

from .fileSystem import File, Directory, ItemType, UnExistsMode, Folder, createItem, isDir
from .path import Path

__all__ = [
    "File",
    "Directory",
    "ItemType",
    "UnExistsMode",
    "Path",
    "Folder",
    "createItem",
]
