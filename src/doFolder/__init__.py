"""
doFolder - A One Stop File System Management Library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

doFolder is a powerful, intuitive, and cross-platform file system management library
that provides a high-level, object-oriented interface for working with files and
directories. It simplifies common file operations such as creating, moving, copying,
deleting, and comparing files and directories while offering advanced features like
hashing, content manipulation, and directory tree operations.

Key Features:
    * **Object-oriented Design**: Work with files and directories as Python objects
    * **Cross-platform Compatibility**: Seamlessly works on Windows, macOS, and Linux
    * **Advanced Path Handling**: Built on Python's pathlib for robust path management
    * **File Operations**: Create, move, copy, delete, and modify files and directories
    * **Content Management**: Read and write file content with encoding support
    * **Directory Tree Operations**: Navigate and manipulate directory structures
    * **File Comparison**: Compare files and directories with various comparison modes
    * **Hash Support**: Generate and verify file hashes for integrity checking
    * **Error Handling**: Comprehensive error modes for different use cases
    * **Type Safety**: Full type hints for better IDE support and code reliability

Quick Start:
    >>> import doFolder
    >>>
    >>> # Create directory and file objects
    >>> project_dir = doFolder.Directory("./my_project")
    >>> config_file = doFolder.File("./my_project/config.json")
    >>>
    >>> # Create a new file in the directory
    >>> new_file = project_dir.create("readme.txt", doFolder.ItemType.FILE)
    >>>
    >>> # Write content to the file
    >>> new_file.content = "Hello, World!".encode("utf-8")
    >>>
    >>> # Create a subdirectory
    >>> sub_dir = project_dir.create("data", doFolder.ItemType.DIR)
    >>>
    >>> # Copy and move files
    >>> backup_file = new_file.copy("./backup/")
    >>> new_file.move("./archive/")

Main Classes:
    * **File**: Represents a file in the file system with methods for content
      manipulation, copying, moving, and deletion.
    * **Directory**: Represents a directory with methods for creating, listing,
      and managing contained files and subdirectories.
    * **Path**: Enhanced path handling with additional utility methods.

Enums and Types:
    * **ItemType**: Enumeration for file system item types (FILE, DIR).
    * **UnExistsMode**: Defines behavior when a path doesn't exist (WARN, ERROR,
      IGNORE, CREATE).

Utility Functions:
    * **createItem()**: Factory function to create File or Directory objects
      based on path type.
    * **isDir()**: Type guard to check if an item is a directory.

Advanced Features:
    * **File Comparison**: The `compare` module provides comprehensive comparison
      capabilities for files and directories.
    * **Hash Operations**: Built-in support for file hashing and verification.
    * **Flexible Error Handling**: Configurable error modes for different
      scenarios.
    * **Path Utilities**: Advanced path manipulation and formatting functions.

:copyright: (c) 2023-2025 by kuankuan2007.
:license: MulanPSL-2.0, see LICENSE for more details.
"""

# Core file system classes and utilities
from .fileSystem import (
    File,  # Class for file operations and management
    Directory,  # Class for directory operations and management
    ItemType,  # Enum defining file system item types (FILE, DIR)
    UnExistsMode,  # Enum defining behavior when paths don't exist
    Folder,  # Backward-compatible alias for Directory
    createItem,  # Factory function to create File or Directory objects
    isDir,  # Type guard to check if an object is a Directory
)

# Enhanced path handling
from .path import Path  # Extended Path class with additional utilities

# File and directory comparison module
from . import compare  # Comprehensive comparison utilities

# Package metadata
from .__pkginfo__ import __version__  # Package version information


__all__ = [
    # Core classes for file system operations
    "File",  # File object for managing individual files
    "Directory",  # Directory object for managing directories
    "Folder",  # Alias for Directory (backward compatibility)
    # Enums and type definitions
    "ItemType",  # Enumeration for file system item types
    "UnExistsMode",  # Behavior mode when paths don't exist
    # Path utilities
    "Path",  # Enhanced path handling class
    # Utility functions
    "createItem",  # Factory function to create File/Directory objects
    "isDir",  # Type guard function to check if item is directory
    # Modules
    "compare",  # File and directory comparison utilities
    # Package metadata
    "__version__",  # Package version string
]
