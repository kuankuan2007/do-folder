"""File system operations module for doFolder.

This module provides comprehensive classes and functions for managing files and directories.
It includes the main FileSystemItemBase abstract class and its concrete implementations
File and Directory, along with utility functions for creating and identifying file system items.

Main classes:
- FileSystemItemBase: Abstract base class for all file system items
- File: Represents files with read/write/JSON operations
- Directory: Represents directories with creation/traversal operations

Main functions:
- createItem(): Factory function to create File or Directory objects
- isFile()/isDir(): Type checking functions

.. versionchanged:: 2.3.0
    fileSystem is now a subpackage, instead of submodule
"""

from .classes import File, Directory, FileSystemItem, FileSystemItemBase, Folder, FileSystemItemLike
from .tools import createItem, isFile, isDir, toFileSystemItem
from ..enums import ErrorMode, UnExistsMode, ItemType
from ..path import Path
