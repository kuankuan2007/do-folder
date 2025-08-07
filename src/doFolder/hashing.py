"""
File and Content Hashing Module
===============================

This module provides comprehensive functionality for calculating cryptographic hashes
of files and byte content with support for caching, chunked reading, and multithreaded
processing.

The module is designed to handle both small and large files efficiently, automatically
choosing between in-memory and streaming approaches based on file size thresholds.

It provides the underlying support for the File.hash method.

.. versionadded:: 2.2.3
"""

import hashlib
import time
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
from . import globalType as _tt
from .enums import ReCalcHashMode

if _tt.TYPE_CHECKING:
    from . import fileSystem as _fs  # pylint: disable=cyclic-import


#: Default cryptographic hash algorithm used throughout the module
DEFAULT_HASH_ALGORITHM = "sha256"

#: Default chunk size (16KB) for reading files in chunks to optimize memory usage
DEFAULT_CHUNK_SIZE = 1024 * 16

#: Minimum file size threshold (64KB) to switch from content-based to streaming I/O
DEFAULT_FILE_IO_MIN_SIZE = DEFAULT_CHUNK_SIZE * 4

#: Default number of threads for parallel hash calculation
DEFAULT_THREAD_NUM = 4


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
    algorithm: str
    path: "_fs.Path"
    mtime: float
    calcTime: float


def _calc(content: _tt.Iterable[bytes], algorithm: str = DEFAULT_HASH_ALGORITHM) -> str:
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
    hashObj = hashlib.new(algorithm)
    for chunk in content:
        hashObj.update(chunk)
    return hashObj.hexdigest()


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
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    chunkSize: int = DEFAULT_CHUNK_SIZE,
) -> str:
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
    return _calc(_toIterable(content, chunkSize), algorithm)


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


def fileHash(
    file: "_fs.File",
    algorithm: str = DEFAULT_HASH_ALGORITHM,
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
    return FileHashResult(
        hash=calc(_fileContent(file, fileIOMinSize), algorithm, chunkSize),
        algorithm=algorithm,
        path=file.path,
        mtime=file.state.st_mtime,
        calcTime=time.time(),
    )


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
    when processing file sets repeatedly.
    
    Attributes:
        useCache (bool): Enable/disable result caching. When enabled, calculated
            hashes are stored and reused based on the recalculation mode.
        reCalcHashMode (ReCalcHashMode): Policy for when to recalculate cached hashes:
            - TIMETAG: Recalculate if file was modified after last hash calculation
            - ALWAYS: Always recalculate, ignore cache (cache still stores results)
            - NEVER: Always use cached results if available
        chunkSize (int): Size of chunks for reading files. Affects memory usage
            and I/O performance for large files.
        fileIOMinSize (int): Size threshold for switching between memory-based
            and streaming file access.
        algorithm (str): Default hash algorithm for all calculations.
        cache (dict): Internal cache storage mapping file paths to hash results.
    
    Example:
        Basic usage with caching::
        
            calculator = FileHashCalculator(
                algorithm="sha256",
                useCache=True,
                reCalcHashMode=ReCalcHashMode.TIMETAG
            )
            
            # First calculation - computed and cached
            result1 = calculator.get(file1)
            
            # Second calculation - uses cache if file unchanged
            result2 = calculator.get(file1)
        
        Performance tuning for large files::
        
            calculator = FileHashCalculator(
                chunkSize=1024 * 64,  # 64KB chunks
                fileIOMinSize=1024 * 1024,  # 1MB threshold
                algorithm="blake2b"  # Fast algorithm
            )
    
    Note:
        The cache is stored in memory and is not persistent across program runs.
        For long-running applications processing many files, consider the memory
        implications of the cache size.
    """

    useCache: bool = True
    reCalcHashMode: ReCalcHashMode = ReCalcHashMode.TIMETAG
    chunkSize: int = DEFAULT_CHUNK_SIZE
    fileIOMinSize: int = DEFAULT_FILE_IO_MIN_SIZE
    algorithm: str = DEFAULT_HASH_ALGORITHM
    cache: "dict[_fs.Path, FileHashResult]" = field(default_factory=dict)

    def get(self, file: "_fs.File") -> FileHashResult:
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
        cacheResult = self.findCache(file)
        if cacheResult is not None:
            return cacheResult
        return self.calc(file)

    def findCache(self, file: "_fs.File") -> _tt.Union[FileHashResult, None]:
        """
        Locate and validate a cached hash result for the given file.
        
        This method searches the internal cache for a hash result and validates
        its currency according to the current recalculation mode. It combines
        cache lookup with validation in a single operation.
        
        Args:
            file (File): The file to look up in the cache.
        
        Returns:
            FileHashResult or None: The cached result if valid, None if no valid
            cache entry exists (either missing or invalidated by recalc mode).
            
        Note:
            Returns None immediately if caching is disabled (useCache=False).
        """
        if not self.useCache:
            return None
        res = self.cache.get(file.path)

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

    def calc(self, file: "_fs.File") -> FileHashResult:
        """
        Calculate the hash of a file and optionally cache the result.
        
        This method performs the actual hash calculation using the calculator's
        configured parameters (algorithm, chunk size, etc.) and stores the result
        in the cache if caching is enabled.
        
        Args:
            file (File): The file to calculate the hash for.
        
        Returns:
            FileHashResult: Complete hash result with metadata.
            
        Note:
            The result is automatically stored in the cache if useCache is True,
            regardless of the recalculation mode.
        """

        res = fileHash(
            file,
            algorithm=self.algorithm,
            chunkSize=self.chunkSize,
            fileIOMinSize=self.fileIOMinSize,
        )

        if self.useCache:
            self.cache[file.path] = res
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
        Initialize the thread pool after dataclass construction.
        
        This method is automatically called after the dataclass __init__ to set up
        the ThreadPoolExecutor with the specified number of worker threads.
        """
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

    def __exit__(self, exc_type, exc_val, exc_tb) -> None: # pylint: disable=unused-argument, invalid-name
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

    def threadedGet(self, file: "_fs.File") -> "Future[FileHashResult]":
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
        cacheResult = self.findCache(file) if self.useCache else None
        if cacheResult is not None:
            res = Future()
            res.set_result(cacheResult)
            return res
        return self.threadPool.submit(self.calc, file)
