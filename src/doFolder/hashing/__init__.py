"""
This module provides comprehensive functionality for calculating cryptographic hashes
of files and byte content with support for caching, chunked reading, and multithreaded
processing.

The module is designed to handle both small and large files efficiently, automatically
choosing between in-memory and streaming approaches based on file size thresholds.

It provides the underlying support for the File.hash method.

.. versionadded:: 2.2.3

.. versionchanged:: 2.3.0
    hashing is now a subpackage, instead of submodule.
"""

# pylint: disable=cyclic-import
from .cache import (
    FileHashCacheManagerBase,
    MemoryFileHashManager,
    NullFileHashManager,
    LfuMemoryFileHashManager,
)
from .calculate import calc, multipleFileHash, fileHash, unsupport
from .calculator import FileHashCalculator, ThreadedFileHashCalculator
from .util import (
    FileHashResult,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_FILE_IO_MIN_SIZE,
    DEFAULT_HASH_ALGORITHM,
    DEFAULT_THREAD_NUM,
    Algorithm,
    MultipleHashResult,
    Algorithms,
    normalizeAlgorithms,
    ReCalcHashMode,
)
from .executor import FutureWithProgress

__all__ = [
    # Cache managers
    "FileHashCacheManagerBase",
    "MemoryFileHashManager",
    "NullFileHashManager",
    "LfuMemoryFileHashManager",
    # Core calculation functions
    "calc",
    "fileHash",
    "multipleFileHash",
    "unsupport",
    # Calculator classes
    "FileHashCalculator",
    "ThreadedFileHashCalculator",
    # Data types and results
    "FileHashResult",
    "MultipleHashResult",
    "Algorithm",
    "Algorithms",
    # Configuration constants
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_FILE_IO_MIN_SIZE",
    "DEFAULT_HASH_ALGORITHM",
    "DEFAULT_THREAD_NUM",
    # Utility functions
    "normalizeAlgorithms",
    # Enums
    "ReCalcHashMode",
]
