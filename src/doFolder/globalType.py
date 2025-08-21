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
from pathlib import Path
import abc


# Import typing utilities from typing_extensions for better compatibility
# across Python versions. typing_extensions provides backports of newer
# typing features to older Python versions.
from types import TracebackType

from typing_extensions import (
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
    Generic,
    Type,
)

# Import custom enums used in type definitions
from .enums import ErrorMode, UnExistsMode, ItemType, CompareModeFlag, CompareMode
from . import env as _env

# Handle version-specific imports for Callable
# In Python 3.10+, Callable is available from collections.abc
# For older versions, it must be imported from typing
if _env.PYTHON_VERSION_INFO >= (3, 10):
    from collections.abc import Callable
else:
    from typing import Callable

#: Type for filesystem paths (str or Path object)
Pathable = Union[str, Path]

#: Type for relative paths (str, Path, or path components)
RelativePathable = Union[str, Path, Iterable[str]]

#: Type for comparison mode specifications
CompareModeItem = Union[CompareModeFlag, CompareMode]
