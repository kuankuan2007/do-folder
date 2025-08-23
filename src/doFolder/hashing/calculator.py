"""
Advanced file hash calculators with caching and multithreading capabilities.

This module provides FileHashCalculator and ThreadedFileHashCalculator classes
that offer intelligent caching, configurable recalculation policies, and
parallel processing for efficient batch file hashing operations.

.. versionadded:: 2.3.0
"""

from dataclasses import dataclass, field

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
    _tt,
    _fs,
    ReCalcHashMode,
)

from . import calculate, cache
from .executor import (
    ThreadPoolExecutorWithProgress,
    ProgressController,
    FutureWithProgress,
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
        cacheManager (cache.FileHashCacheManagerBase): Cache manager instance that handles
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
    cacheManager: cache.FileHashCacheManagerBase = field(
        default=cache.DefaultNoneFileHashManager
    )

    def __post_init__(self):
        """Initialize cache manager if not provided."""
        if self.cacheManager is cache.DefaultNoneFileHashManager and self.useCache:
            self.cacheManager = cache.MemoryFileHashManager()

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
        self,
        file: "_fs.File",
        algorithm: _tt.Optional[str] = None,
        progress: _tt.Optional[ProgressController] = None,
    ) -> FileHashResult:
        """
        Calculate the hash of a file and optionally cache the result.

        This method performs the actual hash calculation using the calculator's
        configured parameters (algorithm, chunk size, etc.) and stores the result
        in the cache using the cacheManager.

        Args:
            file (File): The file to calculate the hash for.
            algorithm (str, optional): Hash algorithm to use. If None, uses the
                calculator's default algorithm.
            progress (ProgressController, optional): Progress controller for tracking
                calculation progress. Can be used to monitor progress or cancel
                the operation.

                .. versionadded:: 2.3.0

        Returns:
            FileHashResult: Complete hash result with metadata.

        Note:
            The result is automatically stored using the cacheManager.
        """

        _algorithm = algorithm or self.algorithm
        return self.multipleCalc(file, (_algorithm,), progress)[_algorithm]

    def multipleCalc(
        self,
        file: "_fs.File",
        algorithms: Algorithms,
        progress: _tt.Optional[ProgressController] = None,
    ) -> MultipleHashResult:
        """
        Calculate multiple hashes for a file and cache all results.

        Performs hash calculations for multiple algorithms and stores each
        result in the cache for future use.

        Args:
            file (File): The file to calculate hashes for.
            algorithms (Union[str, Iterable[str]]): Algorithm(s) to compute hashes for.
            progress (ProgressController, optional): Progress controller for tracking
                calculation progress. Can be used to monitor progress or cancel
                the operation.

                .. versionadded:: 2.3.0

        Returns:
            Dict[str, FileHashResult]: Mapping of algorithm names to hash results.
        """
        res = calculate.multipleFileHash(
            file,
            algorithms=algorithms,
            chunkSize=self.chunkSize,
            fileIOMinSize=self.fileIOMinSize,
            progress=progress,
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
    threadPool: ThreadPoolExecutorWithProgress = field(init=False)

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
        self.threadPool = ThreadPoolExecutorWithProgress(max_workers=self.threadNum)

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
    ) -> "FutureWithProgress[FileHashResult]":
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
            res = FutureWithProgress()
            res.set_result(cacheResult)
            return res
        return self.threadPool.submit(self.calc, file, algorithm)

    def threadedMultipleGet(
        self, file: "_fs.File", algorithms: Algorithms
    ) -> "FutureWithProgress[MultipleHashResult]":
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
            res = FutureWithProgress()
            res.set_result(dict(zip(_algorithms, cacheResults)))
            return res
        return self.threadPool.submit(self.multipleCalc, file, _algorithms)
