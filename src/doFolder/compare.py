"""
Advanced file system comparison module for doFolder.

This module provides comprehensive comparison capabilities for files and directories, supporting
multiple comparison strategies including content comparison, timestamp validation, and size verification.
It enables deep recursive directory comparison and provides detailed difference reporting through
structured data classes. The module optimizes performance through configurable comparison modes
and chunked file reading for large files.

Key Features:
    - Multi-mode file comparison (content, size, timestamp)
    - Recursive directory structure comparison
    - Detailed difference detection and classification
    - Memory-efficient chunked file content comparison
    - Flexible comparison strategy configuration
    - Hierarchical difference reporting with flattening support

.. versionadded:: 2.2.0
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
    Represents a detected difference between two file system paths during comparison operations.
    
    This class serves as the base structure for reporting discrepancies found during file system
    comparisons. It encapsulates the paths being compared and the specific type of difference
    detected, providing a standardized way to represent comparison results throughout the library.
    """

    path1: _tt.Path
    path2: _tt.Path
    diffType: DifferenceType

    def toFlat(self) -> "_tt.Tuple[Difference,...]":
        """Converts the difference structure to a flat tuple representation.
        
        This method provides a uniform interface for flattening difference hierarchies,
        enabling consistent processing of both simple differences and complex directory
        difference trees. For basic Difference objects, returns a single-element tuple.
        
        Returns:
            _tt.Tuple[Difference,...]: A tuple containing this difference instance.
        """
        return (self,)


@dataclass
class DirectoryDifference(Difference):
    """
    Specialized difference class for directory comparisons with hierarchical sub-differences.
    
    This class extends the base Difference class to handle complex directory comparison results
    where differences may exist at multiple levels within the directory structure. It maintains
    a collection of sub-differences representing discrepancies found in contained files and
    subdirectories, enabling comprehensive directory tree analysis and reporting.
    """

    sub: _tt.Tuple["Difference", ...] = field(default_factory=tuple)

    def toFlat(self) -> "_tt.Tuple[Difference,...]":
        """Recursively flattens the directory difference hierarchy into a linear tuple.
        
        This method traverses the entire sub-difference tree and converts it into a flat
        structure, making it easier to process all differences sequentially. The method
        includes the current directory difference followed by all flattened sub-differences
        in depth-first order.
        
        Returns:
            _tt.Tuple[Difference,...]: A flattened tuple containing this difference and all sub-differences.
        """
        res=(self, )
        for i in self.sub:
            res += i.toFlat()
        return res


# Optimal chunk size for file content comparison operations
# Balances memory usage with I/O efficiency for large file comparisons
COMPARE_CHUNK_SIZE = 1024 * 128


def _compareFileContent(
    item1: File, item2: File, chunkSize: int = COMPARE_CHUNK_SIZE
) -> bool:
    """Performs memory-efficient content comparison between two files using chunked reading.

    This function compares file contents by reading both files in configurable chunks,
    enabling comparison of large files without loading entire contents into memory.
    The comparison short-circuits on the first differing chunk or size mismatch,
    optimizing performance for files with early differences.

    Args:
        item1 (File): The first file to compare.
        item2 (File): The second file to compare.
        chunkSize (int): Size of each read operation in bytes for memory efficiency.

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


# Mapping of comparison flags to their corresponding comparison functions
# Enables efficient dispatch of comparison operations based on selected criteria
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
    """Normalizes comparison mode input to a standardized CompareModeFlag representation.

    This function handles the conversion between different comparison mode types,
    accepting both predefined CompareMode enums and raw CompareModeFlag values.
    It ensures consistent internal representation for comparison operations while
    providing user-friendly input flexibility.

    Args:
        mode (_tt.CompareModeItem): The comparison mode or flag to normalize.

    Returns:
        CompareModeFlag: The standardized comparison mode flag representation.

    Raises:
        ValueError: If the input mode is not a recognized comparison mode type.
    """
    if isinstance(mode, CompareMode):
        return mode.value
    if isinstance(mode, CompareModeFlag):
        return mode
    raise ValueError(f"Invalid compare mode: {mode}")


def _compareFile(item1: File, item2: File, compareMode: CompareModeFlag) -> bool:
    """Evaluates file equality using the specified combination of comparison criteria.

    This function applies multiple comparison strategies based on the provided mode flags,
    using bitwise operations to determine which comparison methods to execute. All
    specified comparison criteria must pass for the files to be considered equal.
    The function short-circuits on the first failed comparison for performance optimization.

    Args:
        item1 (File): The first file to compare.
        item2 (File): The second file to compare.
        compareMode (CompareModeFlag): Bitwise combination of comparison criteria flags.

    Returns:
        bool: True if the files satisfy all specified comparison criteria, False otherwise.
    """
    for flag, func in _COMPARE_MODE.items():
        if compareMode & flag:
            if not func(item1, item2):
                return False
    return True

def _compareDirectory(item1: Directory, item2: Directory, compareMode: CompareModeFlag):
    """Performs deep recursive comparison of two directory structures.
    
    This function compares directory contents by first validating that both directories
    contain the same set of items, then recursively comparing each corresponding item
    pair. The comparison process ensures structural equivalence and applies the specified
    comparison mode to all contained files and subdirectories.

    Args:
        item1 (Directory): The first directory to compare.
        item2 (Directory): The second directory to compare.
        compareMode (CompareModeFlag): Comparison criteria to apply recursively.

    Returns:
        bool: True if directories have identical structure and all contents match, False otherwise.
    """
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
    """Core comparison engine that dispatches to appropriate comparison methods based on item types.

    This function serves as the central comparison dispatcher, handling type validation,
    existence checking, and routing to specialized comparison functions for files or
    directories. It implements the primary comparison logic that underlies all public
    comparison operations in the module.

    Args:
        item1 (FileSystemItem): The first file system item to compare.
        item2 (FileSystemItem): The second file system item to compare.
        compareMode (CompareModeFlag): Bitwise combination of comparison criteria.

    Returns:
        bool: True if items exist, have compatible types, and satisfy comparison criteria.
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
    """High-level interface for comparing two file system items with flexible input types.

    This function provides the primary public API for file system comparisons, accepting
    various path-like inputs and converting them to appropriate file system objects.
    It supports multiple comparison strategies and provides sensible defaults for common
    use cases while maintaining flexibility for advanced scenarios.

    Args:
        item1 (FileSystemItemLike): First item, accepting File, Directory, or path-like objects.
        item2 (FileSystemItemLike): Second item, accepting File, Directory, or path-like objects.
        compareMode (_tt.CompareModeItem): Comparison strategy, defaults to timestamp and size validation.

    Returns:
        bool: True if items satisfy the specified comparison criteria, False otherwise.
    """
    return _compare(
        toFileSystemItem(item1),
        toFileSystemItem(item2),
        _toCompareModeFlag(compareMode),
    )


# Type alias for comparison result, representing either a detected difference or no difference
CompareResult = _tt.Union[Difference, None]


def _getDifference(
    item1: FileSystemItem, item2: FileSystemItem, compareMode: CompareModeFlag
) -> CompareResult:
    """Internal engine for detailed difference analysis between file system items.

    This function performs comprehensive difference detection, creating structured
    Difference objects that categorize and describe specific discrepancies found
    during comparison. For directories, it recursively analyzes the entire structure
    and creates hierarchical difference reports with detailed sub-difference tracking.

    Args:
        item1 (FileSystemItem): The first file system item to analyze.
        item2 (FileSystemItem): The second file system item to analyze.
        compareMode (CompareModeFlag): Comparison criteria flags for difference detection.

    Returns:
        CompareResult: Structured difference object, DirectoryDifference for directories, or None if identical.
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
    """Public API for comprehensive difference analysis between file system items.

    This function provides detailed difference reporting for file system comparisons,
    returning structured objects that describe the specific nature of discrepancies
    found. Unlike the simple boolean comparison function, this provides actionable
    information about what differs between the compared items, supporting detailed
    analysis and reporting workflows.

    Args:
        item1 (FileSystemItemLike): First item, accepting various path-like representations.
        item2 (FileSystemItemLike): Second item, accepting various path-like representations.
        compareMode (_tt.CompareModeItem): Comparison methodology, defaults to timestamp and size analysis.

    Returns:
        CompareResult: Detailed difference object, hierarchical DirectoryDifference, or None if identical.
    """
    return _getDifference(
        toFileSystemItem(item1),
        toFileSystemItem(item2),
        _toCompareModeFlag(compareMode),
    )
