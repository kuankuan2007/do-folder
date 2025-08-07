"""
Global Type Definitions and Aliases

This module provides type aliases and ensures compatibility with Python's static
type system across different Python versions. It is commonly imported as `_tt`
in other modules for type hinting purposes.

Key type aliases:
    - Pathable: str or Path objects for filesystem paths
    - RelativePathable: Relative paths (str, Path, or path components)
    - CompareModeItem: Comparison mode specifications

Uses typing_extensions for backward compatibility with older Python versions.
"""

# pylint: disable=unused-import, no-name-in-module
import abc
import sys
from pathlib import Path

# Import typing utilities from typing_extensions for better compatibility
# across Python versions. typing_extensions provides backports of newer
# typing features to older Python versions.
from typing_extensions import (
    List,
    Dict,
    Tuple,
    Set,
    Optional,
    Iterator,
    Iterable,
    Any,
    Union,
    Literal,
    overload,
    TypeAlias,
    IO,
    BinaryIO,
    cast,
    Never,
    NoReturn,
    TypeVar,
    Sequence,
    Self,
    TypeIs,
    Generator,
    TypedDict,
    TYPE_CHECKING,
)

# Import custom enums used in type definitions
from .enums import ErrorMode, UnExistsMode, ItemType, CompareModeFlag, CompareMode


# Handle version-specific imports for Callable
# In Python 3.10+, Callable is available from collections.abc
# For older versions, it must be imported from typing
if sys.version_info >= (3, 10):
    from collections.abc import Callable
else:
    from typing import Callable

#: Type for filesystem paths (str or Path object)
Pathable = Union[str, Path]

#: Type for relative paths (str, Path, or path components)
RelativePathable = Union[str, Path, Iterable[str]]

#: Type for comparison mode specifications
CompareModeItem = Union[CompareModeFlag, CompareMode]
