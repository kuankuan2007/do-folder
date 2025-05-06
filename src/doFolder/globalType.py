"""
This module provides type aliases and ensures compatibility with the static
type system across different Python versions.

It is commonly imported as `_tt` in other modules for type hinting purposes.
"""

# pylint: disable=unused-import
import abc
import sys
from pathlib import Path

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
)

if sys.version_info >= (3, 10):
    from collections.abc import Callable
else:
    from typing import Callable


Pathable = Union[str, Path]
"""
Represents a path that can be provided as either a string or a `Path` object.
"""

RelativePathable = Union[str, Path, Iterable[str]]
"""
Represents a path that can be relative and provided as:
- A string.
- A `Path` object.
- An iterable of strings representing path components.
"""
