"""
This module provides functions to compare paths and path parts.
We use locale-aware string comparison to ensure that path parts are compared correctly
"""

from functools import cmp_to_key
from locale import strcoll


from . import globalType as _tt


def cmpPath(path1: _tt.Path, path2: _tt.Path):
    """Compares two paths based on their parts."""
    return cmpPathParts(path1.parts, path2.parts)


def cmpPathParts(path1: tuple[str, ...], path2: tuple[str, ...]):
    """Compares two path parts."""
    for i in range(min(len(path1), len(path2))):
        if not (i == len(path1) - 1) ^ (i == len(path2) - 1):
            res = strcoll(path1[i], path2[i])
            if res != 0:
                return res
        elif i == len(path1) - 1:

            return -1
        elif i == len(path2) - 1:

            return 1

    return len(path1) - len(path2)


KeyPath = cmp_to_key(cmpPath)
KeyPathParts = cmp_to_key(cmpPathParts)
