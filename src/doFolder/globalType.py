# pylint: disable=unused-import

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
    Self
)
from .path import Path
from abc import ABC

import sys

if sys.version_info >= (3, 10):
    from collections.abc import Callable
else:
    from typing import Callable

EVENT_TYPE = Literal["CREATED", "DELETED", "MODIFIED"]

Pathable = Union[str, Path]
