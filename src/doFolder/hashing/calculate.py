"""
Core cryptographic hash calculation functions for files and byte content.

This module provides the fundamental hash calculation functionality with support
for multiple algorithms, chunked processing, and both memory and streaming I/O modes.

.. versionadded:: 2.3.0
"""

import hashlib
import time

from .util import (
    _tt,
    _fs,
    Algorithm,
    Algorithms,
    _Algorithms,
    normalizeAlgorithms,
    FileHashResult,
    MultipleHashResult,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_FILE_IO_MIN_SIZE,
    DEFAULT_HASH_ALGORITHM,
)
from .executor import ProgressController

def unsupport(algorithms: _tt.Iterable[Algorithm]):
    """Check for unsupported hash algorithms.
    
    Args:
        algorithms: Iterable of algorithm names to check.
        
    Returns:
        Tuple of unsupported algorithm names.
    """
    return tuple(i for i in algorithms if i not in hashlib.algorithms_available)

def _calc(
    content: _tt.Iterable[bytes],
    algorithm: _Algorithms,
    progress: _tt.Optional[ProgressController] = None,
) -> dict[Algorithm, str]:
    """
    Internal function to calculate hash from an iterable of byte chunks.

    This is the core hash calculation function that processes content in chunks,
    making it memory-efficient for large datasets. It uses Python's hashlib
    to support multiple hash algorithms.

    Args:
        content (Iterable[bytes]): An iterable yielding byte chunks to hash.
            Each chunk should be a bytes object.
        algorithm (Iterable[str]): Hash algorithm names supported by hashlib
            (e.g., 'sha256', 'md5', 'sha1', 'sha512').
        progress (ProgressController, optional): Progress controller for tracking
            calculation progress. Updates progress based on bytes processed.

            .. versionadded:: 2.3.0

    Returns:
        Dict[str, str]: Mapping of algorithm names to calculated hashes as
            lowercase hexadecimal strings.

    Raises:
        ValueError: If any specified algorithm is not supported by hashlib.

    Note:
        This feature is specifically designed for internal use.
        It gradually processes the content to ensure that the memory usage remains
            within a reasonable range regardless of how the total amount of content changes
    """

    hashObjs = tuple(hashlib.new(i) for i in algorithm)
    for chunk in content:
        if progress is not None:
            progress.updateProgress(add=len(chunk))
        for hashObj in hashObjs:
            hashObj.update(chunk)

    return {i: hashObj.hexdigest() for i, hashObj in zip(algorithm, hashObjs)}


def _toIterable(
    content: _tt.Union[bytes, _tt.BinaryIO], chunkSize: int = DEFAULT_CHUNK_SIZE
) -> _tt.Iterable[bytes]:
    """
    Convert various content types to an iterable of byte chunks.

    This internal utility function normalizes different input types (bytes, file-like objects)
    into a consistent iterable format for hash calculation. For bytes-like objects, it yields
    the content as-is. For file-like objects, it reads the content in chunks.

    Args:
        content (Union[bytes, BinaryIO]): The content to convert. Can be bytes,
            bytearray, memoryview, or any file-like object with a read() method.
        chunkSize (int, optional): Size of chunks to read from file-like objects.
            Defaults to DEFAULT_CHUNK_SIZE (16KB).

    Yields:
        bytes: Successive chunks of the content as bytes objects.

    Note:
        For small byte objects, yields the entire content in one chunk.
        For file-like objects, reads until EOF, yielding chunks of specified size.
    """
    if isinstance(content, (bytes, bytearray, memoryview)):
        yield bytes(content)
    else:
        while True:
            chunk = content.read(chunkSize)
            if not chunk:
                break
            yield chunk


def calc(
    content: _tt.Union[_tt.BinaryIO, bytes],
    algorithm: Algorithms = DEFAULT_HASH_ALGORITHM,
    chunkSize: int = DEFAULT_CHUNK_SIZE,
    progress: _tt.Optional[ProgressController] = None,
) -> dict[str, str]:
    """
    Calculate the hash of arbitrary content (bytes or file-like object).

    This is the main public interface for hashing content that is not necessarily
    a file. It handles both in-memory content (bytes) and streaming content
    (file-like objects) uniformly.

    Args:
        content (Union[BinaryIO, bytes]): The content to hash. Can be:
            - bytes, bytearray, or memoryview objects
            - Any file-like object with a read() method (e.g., open files, BytesIO)
        algorithm (Union[str, Iterable[str]], optional): Hash algorithm name(s).
            Must be supported by hashlib. Common options: 'sha256', 'sha1', 'md5',
            'sha512'. Defaults to 'sha256'.
        chunkSize (int, optional): Size of chunks when reading from file-like objects.
            Larger chunks may be more efficient for large files but use more memory.
            Defaults to 16KB.
        progress (ProgressController, optional): Progress controller for tracking
            calculation progress. Updates progress based on bytes processed.

            .. versionadded:: 2.3.0

    Returns:
        Dict[str, str]: Mapping of algorithm names to calculated hashes as
            lowercase hexadecimal strings.

    Raises:
        ValueError: If any specified hash algorithm is not supported.
        IOError: If reading from a file-like object fails.

    Example:
        >>> calc(b"hello world")
        {'sha256': 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'}

        >>> with open("file.txt", "rb") as f:
        ...     hash_values = calc(f, algorithm=["sha256", "md5"])
    """
    return _calc(
        _toIterable(content, chunkSize), normalizeAlgorithms(algorithm), progress
    )


def _fileContent(
    file: "_fs.File", fileIOMinSize: int = DEFAULT_FILE_IO_MIN_SIZE
) -> _tt.Union[_tt.BinaryIO, bytes]:
    """
    Optimize file content access based on file size.

    This internal function implements an optimization strategy for file access:
    - Small files (below threshold): Read entire content into memory
    - Large files (above threshold): Return file I/O object for streaming

    This approach balances memory usage with I/O efficiency, avoiding loading
    large files entirely into memory while providing fast access for small files.

    Args:
        file (File): The file object to get content from.
        fileIOMinSize (int, optional): Size threshold in bytes. Files larger than
            this will use streaming I/O, smaller files will be read into memory.
            Defaults to 64KB.

    Returns:
        Union[BinaryIO, bytes]: Either the file's binary content as bytes
            (for small files) or a file I/O object (for large files).

    Note:
        The returned file I/O object should be used immediately as it may
        represent an open file handle that needs proper resource management.
    """
    if file.state.st_size > fileIOMinSize:
        return file.io()
    return file.content


def multipleFileHash(
    file: "_fs.File",
    algorithms: Algorithms = DEFAULT_HASH_ALGORITHM,
    chunkSize: int = DEFAULT_CHUNK_SIZE,
    fileIOMinSize: int = DEFAULT_FILE_IO_MIN_SIZE,
    progress: _tt.Optional[ProgressController] = None,
) -> MultipleHashResult:
    """
    Calculate multiple cryptographic hashes of a file efficiently in a single pass.

    This function computes multiple hash algorithms for a single file in one I/O
    operation, making it more efficient than calling fileHash() multiple times.
    It reads the file content once and applies all specified algorithms simultaneously,
    returning an iterable of FileHashResult objects for each algorithm.

    This approach is particularly beneficial when you need the same file hashed with
    multiple algorithms (e.g., for security verification, compatibility with different
    systems, or comprehensive file integrity checking).

    Args:
        file (File): The file object to hash. Must be a valid file from the
            fileSystem module with accessible content and metadata.
        algorithms (Union[str, Iterable[str]], optional): Hash algorithm(s) to use.
            Can be a single algorithm name (str) or an iterable of algorithm names.
            Each algorithm must be supported by Python's hashlib (e.g., 'sha256',
            'md5', 'sha1', 'sha512', 'blake2b'). Defaults to 'sha256'.
        chunkSize (int, optional): Size of chunks for reading large files.
            Larger chunks may improve I/O performance but use more memory.
            Defaults to 16KB.
        fileIOMinSize (int, optional): File size threshold for I/O optimization.
            Files larger than this use streaming I/O, smaller ones are read
            entirely into memory. Defaults to 64KB.
        progress (ProgressController, optional): Progress controller for tracking
            calculation progress. Updates progress based on bytes processed.
            Allows monitoring progress and potentially canceling the operation.

            .. versionadded:: 2.3.0

    Returns:
        Dict[str, FileHashResult]: A mapping of algorithm names to FileHashResult
            objects. Each result contains:
            - hash: The calculated hash as hexadecimal string
            - algorithm: The specific algorithm used for this result
            - path: The file's path
            - mtime: File modification time when hashed
            - calcTime: Timestamp of hash calculation (same for all results)

    Raises:
        ValueError: If any specified hash algorithm is not supported by hashlib.
        IOError: If the file cannot be read.
        OSError: If file metadata cannot be accessed.

    Example:
        Calculate multiple hashes for a single file::

            # Single algorithm (equivalent to fileHash)
            results = multipleFileHash(file, "sha256")
            sha256_result = results["sha256"]

            # Multiple algorithms in one pass
            results = multipleFileHash(file, ["sha256", "md5", "sha1"])
            for algorithm, result in results.items():
                print(f"{algorithm}: {result.hash}")

            # Using with different algorithms
            algorithms = ["sha256", "blake2b", "sha512"]
            results = multipleFileHash(file, algorithms)

    Performance Notes:
        - More efficient than multiple calls to fileHash() for the same file
        - All algorithms process the same data stream simultaneously
        - File is read only once regardless of the number of algorithms
        - Memory usage scales with the number of algorithms (one hasher per algorithm)
        - Calculation time is roughly the sum of individual algorithm times

    Note:
        While this function accepts a single algorithm string for compatibility,
        if you only need one hash, consider using fileHash() instead as it returns
        a single FileHashResult rather than a dictionary.
    """
    calcTime = time.time()
    if progress is not None:
        progress.updateProgress(total=file.state.st_size)
    res = calc(_fileContent(file, fileIOMinSize), algorithms, chunkSize, progress)

    return {
        al: FileHashResult(
            hash=re,
            algorithm=al,
            path=file.path,
            mtime=file.state.st_mtime,
            calcTime=calcTime,
        )
        for al, re in res.items()
    }


def fileHash(
    file: "_fs.File",
    algorithm: Algorithm = DEFAULT_HASH_ALGORITHM,
    chunkSize: int = DEFAULT_CHUNK_SIZE,
    fileIOMinSize: int = DEFAULT_FILE_IO_MIN_SIZE,
    progress: _tt.Optional[ProgressController] = None,
) -> FileHashResult:
    """
    Calculate the cryptographic hash of a file with comprehensive metadata.

    This is the primary function for hashing files, providing a complete
    FileHashResult with hash value, algorithm info, file path, and timing data.
    The function automatically optimizes I/O based on file size and handles
    both small and large files efficiently.

    Args:
        file (File): The file object to hash. Must be a valid file from the
            fileSystem module with accessible content and metadata.
        algorithm (str, optional): Cryptographic hash algorithm to use.
            Must be supported by Python's hashlib (e.g., 'sha256', 'md5', 'sha1',
            'sha512', 'blake2b'). Defaults to 'sha256'.
        chunkSize (int, optional): Size of chunks for reading large files.
            Larger chunks may improve I/O performance but use more memory.
            Defaults to 16KB.
        fileIOMinSize (int, optional): File size threshold for I/O optimization.
            Files larger than this use streaming I/O, smaller ones are read
            entirely into memory. Defaults to 64KB.
        progress (ProgressController, optional): Progress controller for tracking
            calculation progress. Updates progress based on bytes processed.
            Allows monitoring progress and potentially canceling the operation.

            .. versionadded:: 2.3.0

    Returns:
        FileHashResult: A complete result object containing:
            - hash: The calculated hash as hexadecimal string
            - algorithm: The algorithm used
            - path: The file's path
            - mtime: File modification time when hashed
            - calcTime: Timestamp of hash calculation

    Raises:
        ValueError: If the hash algorithm is not supported.
        IOError: If the file cannot be read.
        OSError: If file metadata cannot be accessed.

    Note:
        It is an interface specifically designed for File.hash
            to replace the hash calculation code originally implemented within File.hash
        The returned FileHashResult can be used with caching systems to avoid
        recalculating hashes for unchanged files.
    """
    return multipleFileHash(
        file, (algorithm,), chunkSize, fileIOMinSize, progress
    )[algorithm]
