"""
This module provides apis to compare file system items and determine differences between them.

.. versionadded:: 2.0.0
"""

from dataclasses import dataclass, field

from . import (
    globalType as _tt,
)

from .enums import CompareMode, CompareModeFlag, DifferenceType
from .fileSystem import (
    File,
    Directory,
    FileSystemItemLike,
    FileSystemItem,
    isDir,
    isFile,
    toFileSystemItem,
)


@dataclass
class Difference:
    """
    Represents a difference between two paths, including the type of difference.
    """

    path1: _tt.Path
    path2: _tt.Path
    diffType: DifferenceType

    def toFlat(self) -> "_tt.Tuple[Difference,...]":
        """Converts the differences from tree structure to a flat tuple.
        
        Returns:
            _tt.Tuple[Difference,...]: A tuple containing the difference.
        """
        return (self,)


@dataclass
class DirectoryDifference(Difference):
    """
    Represents a difference specifically for two directories 
    and can include further sub-differences.
    """

    sub: _tt.Tuple["Difference", ...] = field(default_factory=tuple)

    def toFlat(self) -> "_tt.Tuple[Difference,...]":
        res=(self, )
        for i in self.sub:
            res += i.toFlat()
        return res


COMPARE_CHUNK_SIZE = 1024 * 128


def _compareFileContent(
    item1: File, item2: File, chunkSize: int = COMPARE_CHUNK_SIZE
) -> bool:
    """Compares file contents in chunks.

    Args:
        item1 (File): The first file.
        item2 (File): The second file.
        chunkSize (int): The size of each read block.

    Returns:
        bool: True if both files have identical content, False otherwise.
    """
    if item1.state.st_size != item2.state.st_size:
        return False
    with item1.open("rb") as f1, item2.open("rb") as f2:
        while True:
            chunk1 = f1.read(chunkSize)
            chunk2 = f2.read(chunkSize)
            if chunk1 != chunk2:
                return False
            if not chunk1:
                return True


_COMPARE_MODE: _tt.Dict[CompareModeFlag, _tt.Callable[[File, File], bool]] = {
    CompareModeFlag.CONTENT: _compareFileContent,
    CompareModeFlag.SIZE: lambda item1, item2: (
        item1.state.st_size == item2.state.st_size
    ),
    CompareModeFlag.TIMETAG: lambda item1, item2: (
        item1.state.st_mtime == item2.state.st_mtime
    ),
}


def _toCompareModeFlag(mode: _tt.CompareModeItem) -> CompareModeFlag:
    """Converts a CompareMode or CompareModeFlag to a CompareModeFlag.

    Args:
        mode (_tt.CompareModeItem): The compare mode or flag.

    Returns:
        CompareModeFlag: The corresponding mode flag.

    Raises:
        ValueError: If the input mode is invalid.
    """
    if isinstance(mode, CompareMode):
        return mode.value
    if isinstance(mode, CompareModeFlag):
        return mode
    raise ValueError(f"Invalid compare mode: {mode}")


def _compareFile(item1: File, item2: File, compareMode: CompareModeFlag) -> bool:
    """Checks if two files match under the specified compare mode.

    Args:
        item1 (File): The first file.
        item2 (File): The second file.
        compareMode (CompareModeFlag): Combination of flags indicating how to compare.

    Returns:
        bool: True if the files match, False otherwise.
    """
    for flag, func in _COMPARE_MODE.items():
        if compareMode & flag:
            if not func(item1, item2):
                return False
    return True

def _compareDirectory(item1: Directory, item2: Directory, compareMode: CompareModeFlag):
    """Recursively compares two directories."""
    subItems1 = tuple(i.name for i in item1.iterdir())
    subItems2 = tuple(i.name for i in item2.iterdir())

    if subItems1 != subItems2:
        return False

    for i in subItems1:
        if not _compare(item1[i], item2[i], compareMode):
            return False
    return True
def _compare(
    item1: FileSystemItem, item2: FileSystemItem, compareMode: CompareModeFlag
):
    """Recursively compares two file system items.

    Args:
        item1 (FileSystemItem): The first item.
        item2 (FileSystemItem): The second item.
        compareMode (CompareModeFlag): Combination of flags for comparison.

    Returns:
        bool: True if the items match, False otherwise.
    """
    if not item1.exists() or not item2.exists():
        return False
    if item1.path == item2.path:
        return True

    if isFile(item1) and isFile(item2):
        return _compareFile(item1, item2, compareMode)
    if isDir(item1) and isDir(item2):
        return _compareDirectory(item1, item2, compareMode)
    return False


def compare(
    item1: FileSystemItemLike,
    item2: FileSystemItemLike,
    compareMode: _tt.CompareModeItem = CompareMode.TIMETAG_AND_SIZE,
) -> bool:
    """Compares two file system items using a specified mode.

    Args:
        item1 (FileSystemItemLike): The first item or path-like object.
        item2 (FileSystemItemLike): The second item or path-like object.
        compareMode (_tt.CompareModeItem): The way to compare. Defaults to TIMETAG_AND_SIZE.

    Returns:
        bool: True if items match, False otherwise.
    """
    return _compare(
        toFileSystemItem(item1),
        toFileSystemItem(item2),
        _toCompareModeFlag(compareMode),
    )


CompareResult = _tt.Union[Difference, None]


def _getDifference(
    item1: FileSystemItem, item2: FileSystemItem, compareMode: CompareModeFlag
) -> CompareResult:
    """Determines the difference between two file system items.

    Args:
        item1 (FileSystemItem): The first item.
        item2 (FileSystemItem): The second item.
        compareMode (CompareModeFlag): Combination of flags for comparison.

    Returns:
        CompareResult: A Difference object, a DirectoryDifference object, or None.
    """
    if not item1.exists() or not item2.exists():
        return Difference(item1.path, item2.path, DifferenceType.NOT_EXISTS)
    if item1.path == item2.path:
        return None
    if isDir(item1) and isDir(item2):
        subItems1 = tuple(i.name for i in item1.iterdir())
        subItems2 = tuple(i.name for i in item2.iterdir())
        totalItem = set(subItems1 + subItems2)
        sub: _tt.List[Difference] = []
        for now in totalItem:
            if now not in subItems1 or now not in subItems2:
                sub.append(
                    Difference(
                        item1.path / now,
                        item2.path / now,
                        DifferenceType.NOT_EXISTS,
                    )
                )
            else:
                diff = _getDifference(item1[now], item2[now], compareMode)
                if diff is not None:
                    sub.append(diff)
        if not sub:
            return None
        return DirectoryDifference(
            item1.path, item2.path, DifferenceType.DIRECTORY_DIFFERENCE, tuple(sub)
        )
    if isFile(item1) and isFile(item2):
        return (
            None
            if _compareFile(item1, item2, compareMode)
            else Difference(item1.path, item2.path, DifferenceType.FILE_DIFFERENCE)
        )
    return Difference(item1.path, item2.path, DifferenceType.ITEM_TYPE_DIFFERENCE)


def getDifference(
    item1: "FileSystemItemLike",
    item2: "FileSystemItemLike",
    compareMode: _tt.CompareModeItem = CompareMode.TIMETAG_AND_SIZE,
) -> CompareResult:
    """Returns the differences found between two file system items.

    Args:
        item1 (FileSystemItemLike): The first item or path-like object.
        item2 (FileSystemItemLike): The second item or path-like object.
        compareMode (_tt.CompareModeItem): The comparison mode. Defaults to TIMETAG_AND_SIZE.

    Returns:
        CompareResult: A Difference object, a DirectoryDifference object, or None.
    """
    return _getDifference(
        toFileSystemItem(item1),
        toFileSystemItem(item2),
        _toCompareModeFlag(compareMode),
    )
