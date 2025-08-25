"""
Utility types, constants, and data structures for the hashing package.

This module defines common data types like FileHashResult, default configuration
constants, and utility functions used throughout the hashing subsystem.

.. versionadded:: 2.3.0
"""

# pylint: disable=unused-import

from dataclasses import dataclass
from .. import globalType as _tt, fileSystem as _fs
from ..enums import ReCalcHashMode, TaskStatus


#: Default cryptographic hash algorithm used throughout the module
DEFAULT_HASH_ALGORITHM = "sha256"

#: Default chunk size (16KB) for reading files in chunks to optimize memory usage
DEFAULT_CHUNK_SIZE = 1024 * 16

#: Minimum file size threshold (64KB) to switch from content-based to streaming I/O
DEFAULT_FILE_IO_MIN_SIZE = DEFAULT_CHUNK_SIZE * 4

#: Default number of threads for parallel hash calculation
DEFAULT_THREAD_NUM = 4

Algorithm = str

Algorithms = _tt.Union[Algorithm, _tt.Iterable[Algorithm]]

_Algorithms = _tt.Iterable[Algorithm]  # pylint: disable=invalid-name


@dataclass
class FileHashResult:
    """
    Container for file hash calculation results.

    This dataclass encapsulates all relevant information about a file's hash calculation,
    including metadata about when the calculation was performed and the file's state
    at that time.

    Attributes:
        hash (str): The calculated hash value as a hexadecimal string.
        algorithm (str): The hash algorithm used (e.g., 'sha256', 'md5').
        path (Path): The file system path of the hashed file.
        mtime (float): File modification time (timestamp) when hash was calculated.
        calcTime (float): Timestamp when the hash calculation was performed.

    Note:
        The mtime attribute is crucial for cache validation, allowing the system
        to determine if a file has been modified since its hash was last calculated.
    """

    hash: str
    algorithm: Algorithm
    path: "_fs.Path"
    mtime: float
    calcTime: float


MultipleHashResult = dict[Algorithm, FileHashResult]


def normalizeAlgorithms(algorithms: Algorithms) -> _Algorithms:
    """
    Normalize algorithm input to a consistent iterable format.

    Converts single algorithm strings to tuples for uniform processing.

    Args:
        algorithms (Union[str, Iterable[str]]): Single algorithm or iterable of algorithms.

    Returns:
        Iterable[str]: Tuple of algorithm names for consistent iteration.
    """
    if isinstance(algorithms, Algorithm):
        return (algorithms,)
    return tuple(algorithms)
