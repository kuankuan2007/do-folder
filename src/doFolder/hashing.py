"""
This module provides functions to calculate hashes of files or byte content.

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


DEFAULT_HASH_ALGORITHM = "sha256"
DEFAULT_CHUNK_SIZE = 1024 * 16
DEFAULT_FILE_IO_MIN_SIZE = DEFAULT_CHUNK_SIZE * 4
DEFAULT_THREAD_NUM = 4


@dataclass
class FileHashResult:
    """The result of a file hash calculation."""

    hash: str
    algorithm: str
    path: "_fs.Path"
    mtime: float
    calcTime: float


def _calc(content: _tt.Iterable[bytes], algorithm: str = DEFAULT_HASH_ALGORITHM) -> str:
    """
    Calculate the hash of the given content using the specified algorithm.

    Args:
        content (Iterable[bytes]): The content to calculate the hash of.
        algorithm (str, optional): The algorithm to use for hashing. Defaults to 'sha256'.

    Returns:
        str: The hash of the content.
    """
    hashObj = hashlib.new(algorithm)
    for chunk in content:
        hashObj.update(chunk)
    return hashObj.hexdigest()


def _toIterable(
    content: _tt.Union[bytes, _tt.BinaryIO], chunkSize: int = DEFAULT_CHUNK_SIZE
) -> _tt.Iterable[bytes]:
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
    Calculate the hash of the given content.
    """
    return _calc(_toIterable(content, chunkSize), algorithm)


def _fileContent(
    file: "_fs.File", fileIOMinSize: int = DEFAULT_FILE_IO_MIN_SIZE
) -> _tt.Union[_tt.BinaryIO, bytes]:
    """Get the content of the file as bytes or a file object.

    Args:
        file (File): The file to get the content from.
        fileIOMinSize (int, optional): The minimum size of the file to use file IO instead of content. Defaults to DEFAULT_FILE_IO_MIN_SIZE.

    Returns:
        Union[BinaryIO, bytes]: The content of the file.
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
    Calculate the hash of a file using the specified algorithm.

    Args:
        file (File): The file to calculate the hash for.
        algorithm (str, optional): The hash algorithm to use. Defaults to DEFAULT_HASH_ALGORITHM.
        chunkSize (int, optional): The size of each chunk to read from the file. Defaults to DEFAULT_CHUNK_SIZE.
        fileIOMinSize (int, optional): The minimum size of the file to use file IO instead of content. Defaults to DEFAULT_FILE_IO_MIN_SIZE.

    Returns:
        FileHashResult: The hash result of the file.
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
    A class for calculating file hashes.

    Args:
        useCache (bool, optional): Whether to use a cache for faster lookups.
                Defaults to True.
        reCalcHashMode (ReCalcHashMode, optional): The mode for re-calculating the hash.
                Defaults to ReCalcHashMode.TIMETAG.
        chunkSize (int, optional): The size of each chunk to read from the file.
                Defaults to DEFAULT_CHUNK_SIZE.
        fileIOMinSize (int, optional): The minimum size of the file to use file IO instead of content.
                Defaults to DEFAULT_FILE_IO_MIN_SIZE.
        algorithm (str, optional): The hash algorithm to use.
                Defaults to DEFAULT_HASH_ALGORITHM.
    """

    useCache: bool = True
    reCalcHashMode: ReCalcHashMode = ReCalcHashMode.TIMETAG
    chunkSize: int = DEFAULT_CHUNK_SIZE
    fileIOMinSize: int = DEFAULT_FILE_IO_MIN_SIZE
    algorithm: str = DEFAULT_HASH_ALGORITHM
    cache: "dict[_fs.Path, FileHashResult]" = field(default_factory=dict)

    def get(self, file: "_fs.File") -> FileHashResult:
        """Get the hash of the given file."""
        cacheResult = self.findCache(file)
        if cacheResult is not None:
            return cacheResult
        return self.calc(file)

    def findCache(self, file: "_fs.File") -> _tt.Union[FileHashResult, None]:
        """Find a cached hash entry for the given file."""
        if not self.useCache:
            return None
        res = self.cache.get(file.path)

        if self.validateCache(file, res):
            return res
        return None

    def validateCache(
        self, file: "_fs.File", res: _tt.Union[FileHashResult, None]
    ) -> bool:
        """Validate the cache entry for the given file."""

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
        """Calculate the hash of the given file."""

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
    """A class for calculating file hashes in a threaded manner."""

    threadNum: int = DEFAULT_THREAD_NUM
    threadPool: ThreadPoolExecutor = field(init=False)

    def __post_init__(self):
        """Initialize the thread pool after dataclass initialization."""
        self.threadPool = ThreadPoolExecutor(max_workers=self.threadNum)

    def threadedGet(self, file: "_fs.File") -> Future[FileHashResult]:
        """Get the hash of the given file in a threaded manner."""
        cacheResult = self.findCache(file) if self.useCache else None
        if cacheResult is not None:
            res = Future()
            res.set_result(cacheResult)
            return res
        return self.threadPool.submit(self.calc, file)
