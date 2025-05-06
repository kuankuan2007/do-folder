"""
This module provides utility functions for handling and formatting paths 
within the doFolder package.
"""

# pylint: disable=unused-import

from pathlib import Path
from . import globalType as _tt


def relativePathableFormat(
    path: _tt.RelativePathable, relativeTo: Path
) -> _tt.Tuple[str, ...]:
    """
    Converts a given path into a tuple representation relative to a base path.

    This function accepts a path in various formats (e.g., string, Path object, 
    or an iterable) and converts it into a tuple of strings representing the 
    relative path components. If the input path is already a tuple, it is returned 
    as-is. If the path is absolute, it is made relative to the provided base path.

    Args:
        path (_tt.RelativePathable): The input path to be formatted. It can be:
            - A string representing a path.
            - A `Path` object.
            - An iterable of path components.
        relativeTo (Path): The base path to which the input path will be made relative. 
            This must be an absolute path if the input path is absolute.

    Returns:
        _tt.Tuple[str, ...]: A tuple of strings representing the relative path components.

    Raises:
        ValueError: If the input path is invalid, empty, or cannot be made relative 
            to the base path.
        TypeError: If the input path cannot be converted into a tuple.

    Examples:
        >>> from pathlib import Path
        >>> relativePathableFormat("subdir/file.txt", Path("/base"))
        ('subdir', 'file.txt')

        >>> relativePathableFormat(Path("/base/subdir/file.txt"), Path("/base"))
        ('subdir', 'file.txt')

        >>> relativePathableFormat(("subdir", "file.txt"), Path("/base"))
        ('subdir', 'file.txt')
    """
    if isinstance(path, tuple):
        return path

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
