"""
This module provides utility functions about path for doFolder package.
"""

# pylint: disable=unused-import

from pathlib import Path
from . import globalType as _tt


def relativePathableFormat(
    path: _tt.RelativePathable, relativeTo: Path
) -> _tt.Tuple[str, ...]:
    """
    Formats a given path into a tuple representation relative to another path.

    Args:
        path (_tt.RelativePathable): The input path, which can be a string,
            a Path object, or an iterable representing a path.
        relativeTo (Path): The base path to which the input path will be made relative.

    Returns:
        _tt.Tuple[str, ...]: A tuple of strings representing the relative path.

    Raises:
        ValueError: If the path is invalid or cannot be made relative to the base path.
        TypeError: If the path cannot be converted into a tuple.
    """
    _path = path
    if isinstance(_path, str):
        _path = relativeTo / _path

    if isinstance(_path, Path):
        if _path.is_absolute():
            if not relativeTo.is_absolute():
                raise ValueError(
                    f"The path {path} is absolute, but the base path {relativeTo} is not."
                )
            _path = _path.relative_to(relativeTo)

        _path = _path.parts
    else:
        try:
            _path = tuple(_path)
        except:
            raise TypeError(f"Invalid relative path {path}") from None
    if len(_path) == 0:
        raise ValueError(f"Invalid relative path {path}")

    return _path
