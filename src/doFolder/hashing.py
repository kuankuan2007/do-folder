"""
This module provides comprehensive functionality for calculating cryptographic hashes
of files and byte content with support for caching, chunked reading, and multithreaded
processing.

The module is designed to handle both small and large files efficiently, automatically
choosing between in-memory and streaming approaches based on file size thresholds.

It provides the underlying support for the File.hash method.

.. versionadded:: 2.2.3
"""

# pylint: disable=too-many-lines

import hashlib
import time
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
from collections import OrderedDict as _OrderedDict
from . import globalType as _tt
from .enums import ReCalcHashMode

from . import fileSystem as _fs  # pylint: disable=cyclic-import


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


MultipleHashResult = _tt.Dict[Algorithm, FileHashResult]


def _calc(
    content: _tt.Iterable[bytes], algorithm: _Algorithms
) -> _tt.Dict[Algorithm, str]:
    """
    Internal function to calculate hash from an iterable of byte chunks.

    This is the core hash calculation function that processes content in chunks,
    making it memory-efficient for large datasets. It uses Python's hashlib
    to support multiple hash algorithms.

    Args:
        content (Iterable[bytes]): An iterable yielding byte chunks to hash.
            Each chunk should be a bytes object.
        algorithm (str, optional): Hash algorithm name supported by hashlib
            (e.g., 'sha256', 'md5', 'sha1', 'sha512'). Defaults to 'sha256'.

    Returns:
        str: The calculated hash as a lowercase hexadecimal string.

    Raises:
        ValueError: If the specified algorithm is not supported by hashlib.

    Note:
        This feature is specifically designed for internal use.
        It gradually processes the content to ensure that the memory usage remains
            within a reasonable range regardless of how the total amount of content changes
    """
    hashObjs = (hashlib.new(i) for i in algorithm)
    for chunk in content:
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
) -> _tt.Dict[str, str]:
    """
    Calculate the hash of arbitrary content (bytes or file-like object).

    This is the main public interface for hashing content that is not necessarily
    a file. It handles both in-memory content (bytes) and streaming content
    (file-like objects) uniformly.

    Args:
        content (Union[BinaryIO, bytes]): The content to hash. Can be:
            - bytes, bytearray, or memoryview objects
            - Any file-like object with a read() method (e.g., open files, BytesIO)
        algorithm (str, optional): Hash algorithm name. Must be supported by hashlib.
            Common options: 'sha256', 'sha1', 'md5', 'sha512'. Defaults to 'sha256'.
        chunkSize (int, optional): Size of chunks when reading from file-like objects.
            Larger chunks may be more efficient for large files but use more memory.
            Defaults to 16KB.

    Returns:
        str: The calculated hash as a lowercase hexadecimal string.

    Raises:
        ValueError: If the specified hash algorithm is not supported.
        IOError: If reading from a file-like object fails.

    Example:
        >>> calc(b"hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'

        >>> with open("file.txt", "rb") as f:
        ...     hash_value = calc(f, algorithm="md5")
    """
    return _calc(_toIterable(content, chunkSize), normalizeAlgorithms(algorithm))


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

    Returns:
        Iterable[FileHashResult]: An iterable yielding FileHashResult objects,
            one for each specified algorithm. Each result contains:
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
            results = list(multipleFileHash(file, "sha256"))
            sha256_result = results[0]

            # Multiple algorithms in one pass
            results = list(multipleFileHash(file, ["sha256", "md5", "sha1"]))
            for result in results:
                print(f"{result.algorithm}: {result.hash}")

            # Using with different algorithms
            algorithms = ["sha256", "blake2b", "sha512"]
            results = {r.algorithm: r.hash for r in multipleFileHash(file, algorithms)}

    Performance Notes:
        - More efficient than multiple calls to fileHash() for the same file
        - All algorithms process the same data stream simultaneously
        - File is read only once regardless of the number of algorithms
        - Memory usage scales with the number of algorithms (one hasher per algorithm)
        - Calculation time is roughly the sum of individual algorithm times

    Note:
        While this function accepts a single algorithm string for compatibility,
        if you only need one hash, consider using fileHash() instead as it returns
        a single FileHashResult rather than an iterable.
    """
    calcTime = time.time()
    res = calc(_fileContent(file, fileIOMinSize), algorithms, chunkSize)

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
    return multipleFileHash(file, (algorithm,), chunkSize, fileIOMinSize)[algorithm]


class FileHashCacheManagerBase(_tt.abc.ABC):
    """
    Abstract base class for file hash cache management systems.

    This class defines the interface for implementing custom cache managers that can
    store and retrieve FileHashResult objects. It provides the foundation for
    building persistent or specialized caching solutions beyond the default
    in-memory cache used by FileHashCalculator.

    Implementing classes can provide various storage backends such as:
    - Database-backed caching for persistence across program runs
    - Redis or other external cache systems for distributed applications
    - File-based caching for single-machine persistence
    - Memory-mapped file caching for large datasets

    The interface is designed to be simple and focused, requiring only two
    core operations: retrieving cached results and storing new results.

    Note:
        This is an abstract base class and cannot be instantiated directly.
        Subclasses must implement the get() and set() methods to provide
        actual caching functionality.

    .. versionadded:: 2.2.4
    """

    def __init__(self) -> None:
        """
        Initialize the cache manager base class.

        This constructor performs any basic initialization needed by the base class.
        Subclasses should call super().__init__() in their constructors to ensure
        proper initialization of the base class components.

        Note:
            The base implementation is minimal and serves primarily as a placeholder
            for potential future base class functionality.
        """

    def get(self, file: "_fs.File", algorithm: str) -> _tt.Union[FileHashResult, None]:
        """
        Retrieve a cached hash result for the specified file.

        This method should look up and return any previously cached hash result
        for the given file. The implementation should handle cache validation
        logic, such as checking if the cached result is still valid based on
        file modification times or other criteria.

        Args:
            file (File): The file object to look up in the cache. The implementation
                can use any file attributes (path, modification time, size, etc.)
                as cache keys or validation criteria.

        Returns:
            FileHashResult or None: The cached hash result if found and valid,
                None if no valid cached result exists. Returning None indicates
                that a new hash calculation should be performed.

        Implementation Guidelines:
            - Use file.path as the primary cache key
            - Consider file.state.st_mtime for cache validation
            - Handle cases where cached data may be corrupted or incomplete
            - Return None for any uncertain cases to trigger recalculation
            - Optimize for fast lookup since this method may be called frequently

        Note:
            This is an abstract method that must be implemented by subclasses.
            The base class implementation raises NotImplementedError.
        """

    def set(self, file: "_fs.File", result: FileHashResult) -> None:
        """
        Store a hash result in the cache for future retrieval.

        This method should persistently store the provided hash result so it can
        be retrieved later via the get() method. The implementation should handle
        any necessary serialization, storage optimization, and error handling.

        Args:
            file (File): The file object that was hashed. This provides context
                for the cache entry, including path and metadata that may be
                useful for cache organization or validation.
            result (FileHashResult): The complete hash result to store. This
                includes the hash value, algorithm used, file path, modification
                time, and calculation timestamp.

        Implementation Guidelines:
            - Use file.path or result.path as the cache key
            - Store all relevant fields from the FileHashResult
            - Handle storage errors gracefully (logging, fallback strategies)
            - Consider implementing cache size limits or expiration policies
            - Ensure thread-safety if the cache will be used concurrently
            - Optimize for write performance since caching should not significantly
              slow down hash calculations

        Raises:
            The method should handle storage errors internally when possible,
            but may raise exceptions for critical failures that should halt
            the application (e.g., disk full, permission denied).

        Note:
            This is an abstract method that must be implemented by subclasses.
            The base class implementation raises NotImplementedError.
        """

    @_tt.overload
    def getKey(self, target: "_fs.File", algorithm: str) -> _tt.Tuple[str, str]: ...

    @_tt.overload
    def getKey(self, target: "_fs.Path", algorithm: str) -> _tt.Tuple[str, str]: ...

    @_tt.overload
    def getKey(self, target: FileHashResult) -> _tt.Tuple[str, str]: ...

    def getKey(self, target, algorithm=None):
        """
        Generate a cache key tuple from target object and algorithm.

        This method creates a standardized cache key tuple that uniquely identifies
        a file hash entry based on the target object and algorithm. The key is used
        internally by cache managers to store and retrieve hash results efficiently.

        Args:
            target (Union[FileHashResult, FileSystemItem, Any]): The target object
                to generate a key for. Can be:
                - FileHashResult: Uses the result's path and algorithm
                - FileSystemItem (File, Path, etc.): Uses the item's path with provided algorithm
                - Any other object: Converts to string and uses with provided algorithm
            algorithm (str, optional): Hash algorithm name. Required when target is not
                a FileHashResult. Ignored when target is a FileHashResult (uses result's
                algorithm instead).

        Returns:
            Tuple[str, str]: A tuple containing (path_string, algorithm_string) that
                serves as a unique cache key. The path is always converted to string
                for consistent key generation across different path-like objects.

        Raises:
            AssertionError: If algorithm is not provided when target is not a FileHashResult.

        Note:
            This method is primarily intended for internal use by cache managers
            to maintain consistent key generation across different input types.
            The returned tuple format ensures stable dictionary keys for caching.
        """
        if isinstance(target, FileHashResult):
            return str(target.path), target.algorithm

        assert algorithm, "algorithm is required when target is not FileHashResult"

        if isinstance(target, _fs.FileSystemItem):
            return str(target.path), algorithm
        return str(target), algorithm


class MemoryFileHashManager(FileHashCacheManagerBase):
    """
    Simple in-memory cache manager for file hash results.

    This implementation provides basic caching functionality using a Python dictionary
    to store hash results in memory. The cache persists for the lifetime of the
    MemoryFileHashManager instance but is not persistent across program runs.

    This is the default cache manager when caching is enabled and provides good
    performance for most use cases where memory usage is not a primary concern.

    Note:
        The cache grows without bounds, so for applications processing many files,
        consider using LfuMemoryFileHashManager instead to limit memory usage.

    .. versionadded:: 2.2.4
    """

    _cache: _tt.Dict[_tt.Tuple[str, str], FileHashResult]

    def __init__(self):
        self._cache = {}

    def get(self, file: "_fs.File", algorithm=str):
        return self._cache.get(self.getKey(file, algorithm))

    def set(self, file: "_fs.File", result: FileHashResult):
        self._cache[self.getKey(result)] = result


class NullFileHashManager(FileHashCacheManagerBase):
    """
    No-operation cache manager that disables caching entirely.

    This implementation provides a null object pattern for situations where
    caching is not desired. All cache operations are no-ops:
    - get() always returns None (cache miss)
    - set() discards the provided result

    Use this manager when you want to disable caching but still use the
    FileHashCalculator interface, or for testing scenarios where cache
    behavior should be eliminated.

    This manager has zero memory overhead and provides consistent performance
    characteristics since no cache lookups or storage operations are performed.

    .. versionadded:: 2.2.4
    """

    def get(self, file: "_fs.File", algorithm=str):
        return None

    def set(self, file: "_fs.File", result: FileHashResult):
        pass


class LfuMemoryFileHashManager(FileHashCacheManagerBase):
    """
    LRU (Least Recently Used) memory cache manager with size limits.

    This implementation provides memory-bounded caching using an OrderedDict to track
    access patterns. When the cache exceeds the specified maximum size, the least
    recently used entries are automatically evicted to maintain the size limit.

    The cache uses LRU eviction policy:
    - Recently accessed items are moved to the end of the cache
    - When size limit is exceeded, items from the beginning are removed
    - Both get() and set() operations update the access order

    This manager is ideal for long-running applications that process many files
    where memory usage needs to be controlled while maintaining good cache hit rates.

    Args:
        maxSize (int): Maximum number of hash results to keep in cache.
            When exceeded, least recently used entries are evicted.

    Note:
        Despite the class name suggesting LFU (Least Frequently Used), this
        implementation actually uses LRU (Least Recently Used) eviction policy.

    .. versionadded:: 2.2.4
    """

    _cache: "_OrderedDict[_tt.Tuple[str,str], FileHashResult]"
    maxSize: int

    def __init__(self, maxSize: int):
        self._cache = _OrderedDict()
        self.maxSize = maxSize

    def get(self, file: "_fs.File", algorithm=str):
        key = self.getKey(file, algorithm)
        res = self._cache.get(key)
        if res:
            self._cache.move_to_end(key)
        return res

    def set(self, file: "_fs.File", result: FileHashResult):
        key = self.getKey(result)
        self._cache[key] = result
        self._cache.move_to_end(key)
        if len(self._cache) > self.maxSize:
            self._cache.popitem(last=False)


_DefaultNoneFileHashManager = NullFileHashManager()


@dataclass
class FileHashCalculator:
    """
    Advanced file hash calculator with intelligent caching and optimization.

    This class provides a sophisticated interface for calculating file hashes with
    built-in caching capabilities, configurable recalculation policies, and performance
    optimizations. It's designed for scenarios where multiple files need to be hashed
    and where avoiding redundant calculations is important.

    The caching system uses file modification times and configurable policies to
    determine when cached results are still valid, significantly improving performance
    when processing file sets repeatedly. Cache operations are delegated to a
    pluggable cache manager system.

    Attributes:
        useCache (bool): **DEPRECATED** - Use cacheManager parameter instead.
            Enable/disable result caching. When enabled, calculated
            hashes are stored and reused based on the recalculation mode. This
            attribute is kept for backward compatibility and affects the default
            cache manager selection when cacheManager is not provided.

            .. deprecated:: 2.2.3
               Use cacheManager parameter instead. Pass MemoryFileHashManager()
               for caching or NullFileHashManager() to disable caching.

        reCalcHashMode (ReCalcHashMode): Policy for when to recalculate cached hashes:
            - TIMETAG: Recalculate if file was modified after last hash calculation
            - ALWAYS: Always recalculate, ignore cache (cache still stores results)
            - NEVER: Always use cached results if available
        chunkSize (int): Size of chunks for reading files. Affects memory usage
            and I/O performance for large files.
        fileIOMinSize (int): Size threshold for switching between memory-based
            and streaming file access.
        algorithm (str): Default hash algorithm for all calculations.
        cacheManager (FileHashCacheManagerBase): Cache manager instance that handles
            all cache operations. If not provided, defaults to MemoryFileHashManager
            when useCache is True, or NullFileHashManager when useCache is False.

    Example:
        Basic usage with default caching::

            calculator = FileHashCalculator(
                algorithm="sha256",
                useCache=True,
                reCalcHashMode=ReCalcHashMode.TIMETAG
            )

            # First calculation - computed and cached
            result1 = calculator.get(file1)

            # Second calculation - uses cache if file unchanged
            result2 = calculator.get(file1)

        Using custom cache manager::

            calculator = FileHashCalculator(
                cacheManager=LfuMemoryFileHashManager(maxSize=1000),
                reCalcHashMode=ReCalcHashMode.TIMETAG
            )

        Performance tuning for large files::

            calculator = FileHashCalculator(
                chunkSize=1024 * 64,  # 64KB chunks
                fileIOMinSize=1024 * 1024,  # 1MB threshold
                algorithm="blake2b"  # Fast algorithm
            )

    Note:
        The default cache manager stores results in memory and is not persistent
        across program runs. For long-running applications processing many files,
        consider using LfuMemoryFileHashManager or implementing a custom persistent
        cache manager.
    """

    useCache: bool = field(
        default=True, metadata={"deprecated": "Use cacheManager instead."}
    )
    reCalcHashMode: ReCalcHashMode = ReCalcHashMode.TIMETAG
    chunkSize: int = DEFAULT_CHUNK_SIZE
    fileIOMinSize: int = DEFAULT_FILE_IO_MIN_SIZE
    algorithm: str = DEFAULT_HASH_ALGORITHM
    cacheManager: FileHashCacheManagerBase = field(default=_DefaultNoneFileHashManager)

    def __post_init__(self):
        """Initialize cache manager if not provided."""
        if self.cacheManager is _DefaultNoneFileHashManager and self.useCache:
            self.cacheManager = MemoryFileHashManager()

    def get(
        self, file: "_fs.File", algorithm: _tt.Optional[str] = None
    ) -> FileHashResult:
        """
        Get the hash of a file, using cache when possible.

        This is the main method for retrieving file hashes. It first checks the cache
        for a valid result according to the current recalculation mode, and only
        performs a new calculation if necessary.

        Args:
            file (File): The file to hash.

        Returns:
            FileHashResult: Complete hash result with metadata.

        Note:
            Cache behavior depends on the reCalcHashMode setting:
            - TIMETAG: Uses cache if file hasn't been modified
            - ALWAYS: Ignores cache, always calculates
            - NEVER: Always uses cache if available
        """
        _algorithm = algorithm or self.algorithm
        return self.multipleGet(file, (_algorithm,))[_algorithm]

    def multipleGet(
        self, file: "_fs.File", algorithms: Algorithms
    ) -> MultipleHashResult:
        """
        Get multiple hash results for a file, using cache when possible.

        Efficiently retrieves hash results for multiple algorithms, leveraging cache
        for available results and calculating only missing ones.

        Args:
            file (File): The file to hash.
            algorithms (Union[str, Iterable[str]]): Algorithm(s) to compute hashes for.

        Returns:
            Dict[str, FileHashResult]: Mapping of algorithm names to hash results.
        """
        _algorithms = normalizeAlgorithms(algorithms)
        cacheResults = tuple(self.findCache(file, i) for i in _algorithms)
        if all(cacheResults):
            return dict(zip(_algorithms, _tt.cast(tuple[FileHashResult], cacheResults)))
        return self.multipleCalc(file, algorithms)

    def findCache(
        self, file: "_fs.File", algorithm: _tt.Optional[str] = None
    ) -> _tt.Union[FileHashResult, None]:
        """
        Locate and validate a cached hash result for the given file.

        This method searches the cache for a hash result and validates
        its currency according to the current recalculation mode. It combines
        cache lookup with validation in a single operation.

        Args:
            file (File): The file to look up in the cache.

        Returns:
            FileHashResult or None: The cached result if valid, None if no valid
            cache entry exists (either missing or invalidated by recalc mode).

        Note:
            Uses the configured cacheManager to retrieve cached results.
        """
        algorithm = algorithm or self.algorithm
        res = self.cacheManager.get(  # pylint: disable=assignment-from-none
            file, algorithm
        )

        if self.validateCache(file, res):
            return res
        return None

    def validateCache(
        self, file: "_fs.File", res: _tt.Union[FileHashResult, None]
    ) -> bool:
        """
        Validate whether a cached hash result is still current and usable.

        This method implements the core cache validation logic based on the
        configured recalculation mode. It determines whether a cached result
        should be trusted or if a new calculation is needed.

        Args:
            file (File): The file whose cache entry is being validated.
            res (FileHashResult or None): The cached result to validate,
                or None if no cached result exists.

        Returns:
            bool: True if the cached result is valid and should be used,
                False if a new calculation is needed.

        Validation Rules:
            - TIMETAG mode: Valid if cached mtime >= current file mtime
            - ALWAYS mode: Never valid (always recalculate)
            - NEVER mode: Always valid if result exists
            - None result: Always invalid

        Raises:
            ValueError: If reCalcHashMode is set to an invalid/unknown value.
        """

        if res is None:
            return False

        if self.reCalcHashMode == ReCalcHashMode.TIMETAG:
            return res.mtime >= file.state.st_mtime
        if self.reCalcHashMode == ReCalcHashMode.ALWAYS:
            return False
        if self.reCalcHashMode == ReCalcHashMode.NEVER:
            return True

        raise ValueError("Invalid reCalcHashMode")

    def calc(
        self, file: "_fs.File", algorithm: _tt.Optional[str] = None
    ) -> FileHashResult:
        """
        Calculate the hash of a file and optionally cache the result.

        This method performs the actual hash calculation using the calculator's
        configured parameters (algorithm, chunk size, etc.) and stores the result
        in the cache using the cacheManager.

        Args:
            file (File): The file to calculate the hash for.

        Returns:
            FileHashResult: Complete hash result with metadata.

        Note:
            The result is automatically stored using the cacheManager.
        """

        _algorithm = algorithm or self.algorithm
        return self.multipleCalc(file, (_algorithm,))[_algorithm]

    def multipleCalc(
        self, file: "_fs.File", algorithms: Algorithms
    ) -> MultipleHashResult:
        """
        Calculate multiple hashes for a file and cache all results.

        Performs hash calculations for multiple algorithms and stores each
        result in the cache for future use.

        Args:
            file (File): The file to calculate hashes for.
            algorithms (Union[str, Iterable[str]]): Algorithm(s) to compute hashes for.

        Returns:
            Dict[str, FileHashResult]: Mapping of algorithm names to hash results.
        """
        res = multipleFileHash(
            file,
            algorithms=algorithms,
            chunkSize=self.chunkSize,
            fileIOMinSize=self.fileIOMinSize,
        )
        for i in res.values():
            self.cacheManager.set(file, i)
        return res


@dataclass
class ThreadedFileHashCalculator(FileHashCalculator):
    """
    Multithreaded file hash calculator with automatic resource management.

    This class extends FileHashCalculator with multithreading capabilities, allowing
    multiple files to be hashed concurrently. It's particularly beneficial when
    processing large numbers of files or when I/O latency is high, as it can
    overlap computation and I/O operations.

    The class implements the context manager protocol (__enter__/__exit__) for
    automatic thread pool lifecycle management, ensuring proper resource cleanup
    when used with the 'with' statement.

    The threading model uses a ThreadPoolExecutor to manage worker threads, with
    intelligent cache checking to avoid unnecessary thread overhead for cache hits.

    Attributes:
        threadNum (int): Number of worker threads in the thread pool. More threads
            can improve performance for I/O-bound workloads but may cause resource
            contention. Defaults to 4.
        threadPool (ThreadPoolExecutor): Internal thread pool for parallel execution.
            Automatically initialized after dataclass construction.

    Threading Behavior:
        - Cache hits are resolved immediately without using threads
        - Cache misses are submitted to the thread pool for parallel processing
        - Each thread performs independent file I/O and hash calculation
        - Results are returned as Future objects for asynchronous handling

    Context Manager Usage:
        Recommended usage with automatic cleanup::

            with ThreadedFileHashCalculator(threadNum=8) as calculator:
                # Submit all files for processing
                futures = [calculator.threadedGet(file) for file in file_list]

                # Collect results within the with block
                results = [future.result() for future in futures]

                # Process results
                for result in results:
                    print(f"{result.path}: {result.hash}")
            # Thread pool automatically shut down here

        Manual management (if needed)::

            calculator = ThreadedFileHashCalculator()
            try:
                futures = [calculator.threadedGet(file) for file in file_list]
                results = [future.result() for future in futures]
            finally:
                calculator.threadPool.shutdown(wait=False)

    Example:
        Processing multiple files concurrently::

            with ThreadedFileHashCalculator(
                threadNum=8,  # Use 8 worker threads
                algorithm="blake2b",
                useCache=True
            ) as calculator:
                # Submit all files for processing
                futures = [calculator.threadedGet(file) for file in file_list]

                # Collect results as they complete
                for future in futures:
                    result = future.result()
                    print(f"{result.path}: {result.hash}")

        Processing with error handling::

            with ThreadedFileHashCalculator() as calculator:
                futures = []
                for file in file_list:
                    futures.append(calculator.threadedGet(file))

                for future in futures:
                    try:
                        result = future.result()
                        print(f"Success: {result.path} -> {result.hash}")
                    except Exception as e:
                        print(f"Error processing file: {e}")

    Performance Notes:
        - Optimal thread count depends on system characteristics and file sizes
        - For CPU-bound workloads (fast storage), fewer threads may be better
        - For I/O-bound workloads (network storage), more threads can help
        - Very small files may not benefit from threading due to overhead
        - Use context manager (with statement) for automatic resource cleanup

    Resource Management:
        The context manager automatically shuts down the thread pool with wait=False
        when exiting the 'with' block. This means:
        - No new tasks will be accepted after exit
        - Currently running tasks may continue briefly
        - The program continues immediately without waiting

        If you need to ensure all tasks complete, collect all Future results
        within the 'with' block or manually call shutdown(wait=True).
    """

    threadNum: int = DEFAULT_THREAD_NUM
    threadPool: ThreadPoolExecutor = field(init=False)

    def __post_init__(self):
        """
        Initialize cache manager and thread pool after dataclass construction.

        This method is automatically called after the dataclass __init__ to set up
        both the cache manager (from parent class) and the ThreadPoolExecutor
        with the specified number of worker threads.
        """
        # Initialize cache manager from parent class
        super().__post_init__()
        # Initialize thread pool
        self.threadPool = ThreadPoolExecutor(max_workers=self.threadNum)

    def __enter__(self) -> "ThreadedFileHashCalculator":
        """
        Context manager entry point.

        This method allows the ThreadedFileHashCalculator to be used with the 'with'
        statement for automatic resource management. The thread pool is already
        initialized in __post_init__, so this method simply returns self.

        Returns:
            ThreadedFileHashCalculator: The calculator instance for use in the with block.

        Example:
            with ThreadedFileHashCalculator() as calculator:
                futures = [calculator.threadedGet(file) for file in files]
                results = [future.result() for future in futures]
            # Thread pool is automatically shut down here
        """
        return self

    def __exit__(
        self, exc_type, exc_val, exc_tb  # pylint: disable=unused-argument, invalid-name
    ) -> None:
        """
        Context manager exit point with automatic thread pool shutdown.

        This method is called when exiting the 'with' block and automatically shuts
        down the thread pool without waiting for running tasks to complete. This
        provides clean resource cleanup while allowing the program to continue
        immediately.

        Args:
            exc_type: Exception type if an exception occurred in the with block.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.

        Note:
            The thread pool is shut down with wait=False, meaning:
            - No new tasks will be accepted
            - Currently running tasks may continue briefly in the background
            - The method returns immediately without waiting for task completion
            - This is suitable when you don't need to wait for all results

        Warning:
            If you need to ensure all submitted tasks complete before proceeding,
            call threadPool.shutdown(wait=True) manually before exiting the with block,
            or collect all Future results within the with block.
        """
        self.threadPool.shutdown(wait=False)

    def threadedGet(
        self, file: "_fs.File", algorithm: _tt.Optional[Algorithm] = None
    ) -> "Future[FileHashResult]":
        """
        Get the hash of a file using background thread processing.

        This method provides asynchronous hash calculation by checking the cache
        first and only submitting uncached work to the thread pool. Cache hits
        are resolved immediately with a completed Future to maintain consistent
        return types while avoiding unnecessary thread overhead.

        Args:
            file (File): The file to hash.

        Returns:
            Future[FileHashResult]: A Future object that will contain the hash result.
                - For cache hits: A completed Future with the cached result
                - For cache misses: A Future representing the ongoing calculation

        Usage:
            The returned Future can be used with standard concurrent.futures patterns::

                # Get Future immediately
                future = calculator.threadedGet(file)

                # Block until result is available
                result = future.result()

                # Check if calculation is complete
                if future.done():
                    result = future.result()

                # Add callback for when complete
                future.add_done_callback(lambda f: print(f.result().hash))

        Note:
            Cache validation follows the same rules as the synchronous get() method,
            but the actual calculation (if needed) happens in a background thread.
        """
        algorithm = algorithm or self.algorithm
        cacheResult = self.findCache(file)
        if cacheResult is not None:
            res = Future()
            res.set_result(cacheResult)
            return res
        return self.threadPool.submit(self.calc, file, algorithm)

    def threadedMultipleGet(
        self, file: "_fs.File", algorithms: Algorithms
    ) -> "Future[MultipleHashResult]":
        """
        Get multiple hash results for a file using background thread processing.

        Provides asynchronous calculation of multiple hash algorithms by checking
        the cache first and only submitting uncached work to the thread pool.

        Args:
            file (File): The file to hash.
            algorithms (Union[str, Iterable[str]]): Algorithm(s) to compute hashes for.

        Returns:
            Future[Dict[str, FileHashResult]]: A Future containing the mapping of
                algorithm names to hash results.
                - For complete cache hits: A completed Future with cached results
                - For cache misses: A Future representing the ongoing calculation

        Note:
            Cache validation follows the same rules as the synchronous multipleGet() method,
            but the actual calculation (if needed) happens in a background thread.
        """
        _algorithms = normalizeAlgorithms(algorithms)
        cacheResults = tuple(self.findCache(file, i) for i in _algorithms)
        if all(cacheResults):
            res = Future()
            res.set_result(dict(zip(_algorithms, cacheResults)))
            return res
        return self.threadPool.submit(self.multipleCalc, file, _algorithms)
