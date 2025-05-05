"""
This module ensures the support for the static type system in different versions

It is generally named _tt in other modules
"""

# pylint: disable=unused-import
from abc import ABC
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
    TypeIs
)


if sys.version_info >= (3, 10):
    from collections.abc import Callable
else:
    from typing import Callable

EventType = Literal["CREATED", "DELETED", "MODIFIED"]

Pathable = Union[str, Path]
RelativePathable = Union[str, Path, Iterable[str]]
