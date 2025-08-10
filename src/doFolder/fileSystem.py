"""File system operations module for doFolder.

This module provides comprehensive classes and functions for managing files and directories.
It includes the main FileSystemItemBase abstract class and its concrete implementations
File and Directory, along with utility functions for creating and identifying file system items.

Main classes:
- FileSystemItemBase: Abstract base class for all file system items
- File: Represents files with read/write/JSON operations
- Directory: Represents directories with creation/traversal operations

Main functions:
- createItem(): Factory function to create File or Directory objects
- isFile()/isDir(): Type checking functions
"""

import shutil as _shutil
import json as _json
import io as _io
from deprecated import deprecated as _deprecated

from .path import Path, relativePathableFormat
from .enums import ErrorMode, UnExistsMode, ItemType

from . import (
    exception as _ex,
    globalType as _tt,
    hashing as _hash
)  # pylint: disable=unused-import


def isDir(target: "FileSystemItemBase") -> " _tt.TypeIs[Directory]":
    """Check if target is a directory.

    Args:
        target (FileSystemItemBase): The file system item to check.

    Returns:
        bool: True if target is a directory, False otherwise.
    """
    return target.itemType == ItemType.DIR


def isFile(target: "FileSystemItemBase") -> " _tt.TypeIs[File]":
    """Check if target is a file.

    Args:
        target (FileSystemItemBase): The file system item to check.

    Returns:
        bool: True if target is a file, False otherwise.
    """
    return target.itemType == ItemType.FILE


def createItem(
    path: _tt.Pathable,
    unExistsMode: UnExistsMode = UnExistsMode.WARN,
    errorMode: ErrorMode = ErrorMode.WARN,
    toAbsolute: bool = False,
    exceptType: _tt.Union[ItemType, None] = None,
) -> "FileSystemItem":
    """Create a file system item based on the given path.

    Automatically detects whether the path points to a file or directory and creates
    the appropriate object. If the path doesn't exist, behavior is controlled by
    unExistsMode parameter.

    Args:
        path (Pathable): Path to the file or directory.
        unExistsMode (UnExistsMode, optional): Behavior when path doesn't exist. Defaults to WARN.
        errorMode (ErrorMode, optional): Error handling mode. Defaults to WARN.
        toAbsolute (bool, optional): Convert path to absolute. Defaults to False.
        exceptType (ItemType, optional): Expected item type (FILE or DIR). Defaults to None.

    Returns:
        FileSystemItem: File or Directory object based on the path type.
    """
    path = Path(path)
    if path.exists():
        if path.is_file():
            return File(path, unExistsMode, errorMode, toAbsolute)
        if path.is_dir():
            return Directory(path, unExistsMode, errorMode, toAbsolute)
        _ex.unintended(
            f"Path {path} is not a file or directory",
            errorMode,
            errorClass=_ex.PathTypeError,
            warnClass=_ex.PathTypeWarning,
        )
    return (Directory if exceptType == ItemType.DIR else File)(
        path, unExistsMode, errorMode, toAbsolute, exceptType=exceptType
    )


def toFileSystemItem(fr: "FileSystemItemLike") -> "FileSystemItem":
    """Convert FileSystemItemLike to FileSystemItem.

    Args:
        fr (FileSystemItemLike): Object to convert (path or FileSystemItem).

    Returns:
        FileSystemItem: FileSystemItem object.

    .. versionadded:: 2.2.0
    """
    if isinstance(fr, FileSystemItemBase):
        return fr
    return createItem(fr)


class FileSystemItemBase(_tt.abc.ABC):
    """Abstract base class for file and directory objects.

    Provides common functionality for both files and directories, including
    path management, existence checking, and basic operations.

    Attributes:
        path (Path): The path to the file or directory. :no-index:

    .. versionadded:: 2.1.0
    """

    path: Path

    @property
    @_tt.abc.abstractmethod
    def itemType(self) -> ItemType:
        """Get the item type.

        Returns:
            ItemType: FILE or DIR enum value.
        """
        raise NotImplementedError("itemType is not implemented")

    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        path: _tt.Pathable,
        unExistsMode: UnExistsMode = UnExistsMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
        toAbsolute: bool = False,
        exceptType: _tt.Union[ItemType, None] = None,
    ):
        """Initialize a file system item.

        Args:
            path (Pathable): Path to the file or directory.
            unExistsMode (UnExistsMode, optional): Behavior when path doesn't exist. Defaults to WARN.
            errorMode (ErrorMode, optional): Error handling mode. Defaults to WARN.
            toAbsolute (bool, optional): Convert path to absolute. Defaults to False.
            exceptType (ItemType, optional): Expected item type. Defaults to None.
        """
        if exceptType is not None and self.itemType != exceptType:
            _ex.unintended(
                f"FileSystemItem {self.__class__.__name__} is not {exceptType}",
                errorMode,
                errorClass=_ex.PathTypeError,
                warnClass=_ex.PathTypeWarning,
            )
        if not isinstance(path, Path):
            path = Path(path)
        self.path = path if toAbsolute else path.absolute()
        self.checkExists(unExistsMode)

    def checkExists(self, unExistsMode) -> None:
        """Verify path existence and handle according to unExistsMode.

        Args:
            unExistsMode (UnExistsMode): Behavior when path doesn't exist.

        Raises:
            PathNotExistsError: If path doesn't exist and unExistsMode is ERROR.
            ValueError: If unExistsMode is invalid.
        """
        if self.exists():
            return

        if unExistsMode == UnExistsMode.WARN:
            _ex.warn(
                f"Path does not exist: {self.path}",
                _ex.PathNotExistsWarning,
            )
        elif unExistsMode == UnExistsMode.ERROR:
            raise _ex.PathNotExistsError(f"Path does not exist: {self.path}")
        elif unExistsMode == UnExistsMode.IGNORE:
            pass
        elif unExistsMode == UnExistsMode.CREATE:
            self.createSelf()
        else:
            raise ValueError(f"Invalid unExistsMode: {unExistsMode}")

    def checkItemType(self, itemType: ItemType) -> bool:
        """Check if item type matches expected type.

        Args:
            itemType (ItemType): Expected item type.

        Returns:
            bool: True if types match, False otherwise.
        """
        return self.itemType == itemType

    def torch(self):
        """Create the file system item if it doesn't exist.

        .. versionadded:: 2.2.0
        """
        self.createSelf()

    @_tt.abc.abstractmethod
    def createSelf(self) -> None:
        """Create the file system item."""
        raise NotImplementedError("createSelf is not implemented")

    def exists(self) -> bool:
        """Check if item exists.

        Returns:
            bool: True if item exists, False otherwise.
        """
        return self.path.exists()

    @property
    def name(self) -> str:
        """Get item name.

        Returns:
            str: Name of the file or directory.
        """
        return self.path.name

    @property
    def extension(self) -> str:
        """Get file extension.

        Returns:
            str: File extension (suffix).
        """
        return self.path.suffix

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path}>"

    def isFile(self):
        """Check if this object is a File.

        .. versionchanged:: 2.2.3 
            This method determines the object type rather than the actual path type.
        """
        return isFile(self)

    def isDir(self):
        """Check if this object is a Directory.

        .. versionchanged:: 2.2.3 
            This method determines the object type rather than the actual path type.
        """
        return isDir(self)

    @property
    def state(self):
        """Get file/directory state information.

        Returns:
            os.stat_result: os.stat_result object with file statistics.
        """
        return self.path.stat()

    def parent(self) -> "Directory":
        """Get parent directory.

        Returns:
            Directory: Directory object of the parent.
        """
        return Directory(self.path.parent, unExistsMode=UnExistsMode.IGNORE)

    @_tt.abc.abstractmethod
    def move(self, target: _tt.Pathable) -> None:
        """Move item to target path.

        Args:
            target (Pathable): Target path to move to.
        """
        raise NotImplementedError("move is not implemented")

    @_tt.abc.abstractmethod
    def copy(self, target: _tt.Pathable) -> None:
        """Copy item to target path.

        Args:
            target (Pathable): Target path to copy to.
        """
        raise NotImplementedError("copy is not implemented")

    @_tt.abc.abstractmethod
    def delete(self) -> None:
        """Delete the item."""
        raise NotImplementedError("delete is not implemented")


class File(FileSystemItemBase):
    """Represents a file in the file system.

    Provides comprehensive file operations including reading, writing, copying,
    moving, deleting, and content management with various formats (text, binary, JSON).

    .. versionchanged:: 2.1.0
        File is now a subclass of FileSystemItemBase rather than the base class.
    """

    @property
    def itemType(self) -> ItemType:
        """Get item type.

        Returns:
            ItemType: Always returns ItemType.FILE.
        """
        return ItemType.FILE

    def createSelf(self) -> None:
        """Create the file if it doesn't exist."""
        self.path.touch()

    def open(self, *args, **kwargs):
        """Open file with specified mode and options.

        Args:
            *args: Positional arguments for open().
            **kwargs: Keyword arguments for open().

        Returns:
            file: File object for reading/writing.
        """
        return self.path.open(*args, **kwargs)  # pylint: disable=unspecified-encoding

    def io(self, mode:str="r"):
        """Create a FileIO object for the file.

        Args:
            mode (str, optional): File open mode. Defaults to "r".

        Returns:
            FileIO: FileIO object for the file.
        
        .. versionadded:: 2.2.3
        """
        return _io.FileIO(self.path,mode)
    @property
    def content(self) -> _tt.Union[bytes, _tt.NoReturn]:
        """Get file content as bytes.

        Returns:
            bytes: File content as bytes.
        """
        with self.open("rb") as file:
            return _tt.cast(bytes, file.read())

    @content.setter
    def content(self, content: bytes) -> None:
        """Set file content.

        Args:
            content (bytes): Content to write as bytes.
        """
        with self.open("wb") as file:
            file.write(_tt.cast(_tt.Any, content))

    def delete(self) -> None:
        """Delete the file."""
        self.path.unlink()

    def copy(self, target: _tt.Pathable) -> None:
        """Copy file to target path.

        Args:
            target (Pathable): Target path to copy to.
        """
        _shutil.copy2(self.path, target)

    def move(self, target: _tt.Pathable) -> None:
        """Move file to target path.

        Args:
            target (Pathable): Target path to move to.
        """
        target = Path(target)
        _shutil.move(self.path, target)
        self.path = target

    def hash(self, algorithm: str = 'sha256') -> str:
        """Calculate file content hash.

        Args:
            algorithm (str, optional): Hash algorithm to use. Defaults to "sha256".

        Returns:
            str: Hash value as hexadecimal string.

        .. versionchanged:: 2.2.3
            Uses doFolder.hashing module instead of hashlib directly.
        """
        return _hash.fileHash(self, algorithm).hash

    def loadAsJson(self, encoding: str = "utf-8", **kw) -> _tt.Any:
        """Load file content as JSON.

        Args:
            encoding (str, optional): Text encoding to use. Defaults to "utf-8".
            **kw: Additional arguments for json.load().

        Returns:
            Any: Parsed JSON data.

        .. versionadded:: 2.0.3
        """
        with self.open("r", encoding=encoding) as file:
            return _json.load(file, **kw)

    def saveAsJson(  # pylint: disable=too-many-arguments
        self,
        data: _tt.Any,
        encoding: str = "utf-8",
        *,
        skipkeys=False,
        ensure_ascii=True,
        check_circular=True,
        allow_nan=True,
        cls=None,
        indent=None,
        separators=None,
        default=None,
        sort_keys=False,
        **kw: _tt.Any,
    ) -> None:
        """Save data as JSON to file.

        Args:
            data (Any): Data to save as JSON.
            encoding (str, optional): Text encoding to use. Defaults to "utf-8".
            skipkeys (bool, optional): Skip non-serializable keys. Defaults to False.
            ensure_ascii (bool, optional): Ensure ASCII encoding. Defaults to True.
            check_circular (bool, optional): Check for circular references. Defaults to True.
            allow_nan (bool, optional): Allow NaN values. Defaults to True.
            cls (type, optional): Custom JSON encoder class. Defaults to None.
            indent (int, optional): Indentation level. Defaults to None.
            separators (tuple, optional): Custom separators tuple. Defaults to None.
            default (callable, optional): Custom serialization function. Defaults to None.
            sort_keys (bool, optional): Sort keys in output. Defaults to False.
            **kw: Additional arguments for json.dump().

        .. versionadded:: 2.0.3
        """
        with self.open("w", encoding=encoding) as file:
            _json.dump(
                data,
                file,
                skipkeys=skipkeys,
                ensure_ascii=ensure_ascii,
                check_circular=check_circular,
                allow_nan=allow_nan,
                cls=cls,
                indent=indent,
                separators=separators,
                default=default,
                sort_keys=sort_keys,
                **kw,
            )


class Directory(FileSystemItemBase):
    """Represents a directory in the file system.

    Provides comprehensive directory operations including creating, deleting, copying,
    moving, and content management. Supports nested operations through path traversal
    and recursive iteration.

    .. versionadded:: 2.0.0

    .. versionchanged:: 2.1.0
        Directory now inherits directly from FileSystemItemBase instead of File.
    """

    @property
    def itemType(self) -> ItemType:
        """Get item type.

        Returns:
            ItemType: Always returns ItemType.DIR.
        """
        return ItemType.DIR

    def createSelf(self) -> None:
        """Create directory if it doesn't exist."""
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)

    def delete(self) -> None:
        """Delete directory and all its contents."""
        _shutil.rmtree(self.path)

    def copy(self, target: _tt.Pathable) -> None:
        """Copy directory and contents to target path.

        Args:
            target (Pathable): Target path to copy to.
        """
        _shutil.copytree(self.path, target)

    def move(self, target: _tt.Pathable) -> None:
        """Move directory and contents to target path.

        Args:
            target (Pathable): Target path to move to.
        """
        _shutil.move(self.path, target)
        self.path = Path(target)

    def iterdir(self):
        """Iterate over direct children of the directory."""
        return self.path.iterdir()

    def __iter__(self) -> "_tt.Generator[FileSystemItem]":
        """Iterate over files and directories in this directory.

        Yields:
            FileSystemItem: FileSystemItem objects for each child.
        """
        yield from map(createItem, self.path.iterdir())

    def __getitem__(self, name: str) -> "FileSystemItem":
        """Get child by name.

        Args:
            name (str): Name of the child file or directory.

        Returns:
            FileSystemItem: FileSystemItem for the child.
        """
        return self._get(name, unExistsMode=UnExistsMode.ERROR)

    @_tt.overload
    def recursiveTraversal(
        self, hideDirectory: _tt.Literal[True] = True
    ) -> "_tt.Generator[File]": ...

    @_tt.overload
    def recursiveTraversal(
        self, hideDirectory: _tt.Literal[False]
    ) -> "_tt.Generator[FileSystemItem]": ...

    def recursiveTraversal(self, hideDirectory: bool = True):
        """Recursively traverse directory and subdirectories.

        Args:
            hideDirectory (bool, optional): Whether to exclude directories from results. Defaults to True.

        Yields:
            File: Files (if hideDirectory=True) or all items (if hideDirectory=False).
        """

        if not hideDirectory:
            yield self
        for item in self:
            if isDir(item):
                yield from item.recursiveTraversal(hideDirectory)
            else:
                yield item

    def create(
        self,
        target: _tt.RelativePathable,
        createType: ItemType = ItemType.FILE,
        *,
        existsErrorMode: ErrorMode = ErrorMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
    ) -> "FileSystemItem":
        """Create a file or directory within this directory.

        Supports nested path creation by automatically creating intermediate directories
        when necessary. The target path is relative to this directory.

        Args:
            target (RelativePathable): Relative path to create.
            createType (ItemType, optional): Type to create (FILE or DIR). Defaults to FILE.
            existsErrorMode (ErrorMode, optional): How to handle existing paths. Defaults to WARN.
            errorMode (ErrorMode, optional): General error handling mode. Defaults to WARN.

        Returns:
            FileSystemItem: Created FileSystemItem (File or Directory).
        """
        return self.deepCall(
            target,
            "_create",
            createMiddleDir=True,
            createType=createType,
            existsErrorMode=existsErrorMode,
            errorMode=errorMode,
        )

    def createFile(
        self,
        target: _tt.RelativePathable,
        *,
        existsErrorMode: ErrorMode = ErrorMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
    ) -> "File":
        """Create a file within this directory.

        Args:
            target (RelativePathable): Relative path to the file.
            existsErrorMode (ErrorMode, optional): How to handle existing paths. Defaults to WARN.
            errorMode (ErrorMode, optional): General error handling mode. Defaults to WARN.

        Returns:
            File: Created File object.

        Raises:
            PathTypeError: If created item is not a file.
        """
        res = self.create(
            target,
            createType=ItemType.FILE,
            existsErrorMode=existsErrorMode,
            errorMode=errorMode,
        )
        if not isFile(res):
            raise _ex.PathTypeError(f"{target} is not a file.")
        return res

    def createDir(
        self,
        target: _tt.RelativePathable,
        *,
        existsErrorMode: ErrorMode = ErrorMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
    ) -> "Directory":
        """Create a directory within this directory.

        Args:
            target (RelativePathable): Relative path to the directory.
            existsErrorMode (ErrorMode, optional): How to handle existing paths. Defaults to WARN.
            errorMode (ErrorMode, optional): General error handling mode. Defaults to WARN.

        Returns:
            Directory: Created Directory object.

        Raises:
            PathTypeError: If created item is not a directory.
        """
        res = self.create(
            target,
            createType=ItemType.DIR,
            existsErrorMode=existsErrorMode,
            errorMode=errorMode,
        )
        if not isDir(res):
            raise _ex.PathTypeError(f"{target} is not a directory.")
        return res

    def get(
        self,
        target: _tt.RelativePathable,
        *,
        exceptType: ItemType = ItemType.FILE,
        unExistsMode: UnExistsMode = UnExistsMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
    ) -> "FileSystemItem":
        """Get a file or directory within this directory.

        Args:
            target (RelativePathable): Relative path to the item.
            exceptType (ItemType, optional): Expected item type. Defaults to FILE.
            unExistsMode (UnExistsMode, optional): How to handle non-existent paths. Defaults to WARN.
            errorMode (ErrorMode, optional): General error handling mode. Defaults to WARN.

        Returns:
            FileSystemItem: FileSystemItem for the target.
        """
        return self.deepCall(
            target,
            "_get",
            unExistsMode=unExistsMode,
            errorMode=errorMode,
            exceptType=exceptType,
        )

    def getFile(
        self,
        target: _tt.RelativePathable,
        *,
        unExistsMode: UnExistsMode = UnExistsMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
    ) -> "File":
        """Get a file within this directory.

        Args:
            target (RelativePathable): Relative path to the file.
            unExistsMode (UnExistsMode, optional): How to handle non-existent paths. Defaults to WARN.
            errorMode (ErrorMode, optional): General error handling mode. Defaults to WARN.

        Returns:
            File: File object for the target.

        Raises:
            PathTypeError: If target is not a file.
        """
        res = self.deepCall(
            target,
            "_get",
            unExistsMode=unExistsMode,
            errorMode=errorMode,
            exceptType=ItemType.FILE,
        )
        if not isFile(res):
            raise _ex.PathTypeError(f"{target} is not a file.")

        return res

    def getDir(
        self,
        target: _tt.RelativePathable,
        *,
        unExistsMode: UnExistsMode = UnExistsMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
    ) -> "Directory":
        """Get a directory within this directory.

        Args:
            target (RelativePathable): Relative path to the directory.
            unExistsMode (UnExistsMode, optional): How to handle non-existent paths. Defaults to WARN.
            errorMode (ErrorMode, optional): General error handling mode. Defaults to WARN.

        Returns:
            Directory: Directory object for the target.

        Raises:
            PathTypeError: If target is not a directory.
        """
        res = self.deepCall(
            target,
            "_get",
            unExistsMode=unExistsMode,
            errorMode=errorMode,
            exceptType=ItemType.FILE,
        )
        if not isDir(res):
            raise _ex.PathTypeError(f"{target} is not a file.")
        return res

    def has(
        self,
        target: _tt.RelativePathable,
        *,
        allowedTargetType: _tt.Union[ItemType, None] = None,
    ) -> bool:
        """Check if a file or directory exists within this directory.

        Args:
            target (RelativePathable): Relative path to check.
            allowedTargetType (ItemType, optional): Expected item type (FILE, DIR, or None for any).

        Returns:
            bool: True if target exists and matches type (if specified).
        """
        return self.deepCall(
            target,
            "_has",
            allowedTargetType=allowedTargetType,
        )

    def deepCall(
        self,
        target: _tt.RelativePathable,
        func: str,
        *args,
        createMiddleDir: bool = False,
        **kwargs,
    ) -> "_tt.Any":
        """Perform a deep operation on nested directory structure.

        Handles path traversal through multiple directory levels, automatically
        creating intermediate directories when needed. This is the core method
        that enables nested operations like create(), get(), and has().

        Args:
            target (RelativePathable): Relative path that may contain multiple directory levels.
            func (str): Method name to call on the final directory.
            *args: Positional arguments for the target method.
            createMiddleDir (bool, optional): Whether to create intermediate directories. Defaults to False.
            **kwargs: Keyword arguments for the target method.

        Returns:
            Any: Result from the target method call.

        Raises:
            ValueError: If target path is invalid.
            PathNotExistsError: If intermediate directory doesn't exist.
            PathTypeError: If intermediate path is not a directory.
        """
        _target = relativePathableFormat(target, self.path)

        if len(_target) == 0:
            raise ValueError(f"Invalid target path: {target}")
        if len(_target) == 1:
            return getattr(self, func)(_target[0], *args, **kwargs)

        _next = self._get(
            _target[0],
            exceptType=ItemType.DIR,
            unExistsMode=(
                UnExistsMode.CREATE if createMiddleDir else UnExistsMode.IGNORE
            ),
        )
        if not _next.exists():
            raise _ex.PathNotExistsError(f"{_next.path} not found.")

        if _next.itemType != ItemType.DIR:
            raise _ex.PathTypeError(f"{_next.path} is not a directory.")

        return _tt.cast(Directory, _next).deepCall(
            _target[1:], func, createMiddleDir=createMiddleDir, *args, **kwargs
        )

    def _create(
        self,
        target: str,
        *,
        createType: ItemType = ItemType.FILE,
        existsErrorMode: ErrorMode = ErrorMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
    ) -> "FileSystemItem":
        """Create item directly in this directory (internal method).

        Args:
            target (str): Name of the item to create.
            createType (ItemType, optional): Type to create (FILE or DIR). Defaults to FILE.
            existsErrorMode (ErrorMode, optional): How to handle existing items. Defaults to WARN.
            errorMode (ErrorMode, optional): General error handling mode. Defaults to WARN.

        Returns:
            FileSystemItem: Created FileSystemItem.
        """
        _target = self.path / target
        if _target.exists():
            _ex.unintended(
                f"Path {target} already exists",
                existsErrorMode,
                errorClass=_ex.PathAreadyExistsError,
                warnClass=_ex.PathAreadyExistsWarning,
            )
        return self._get(
            target,
            exceptType=createType,
            errorMode=errorMode,
            unExistsMode=UnExistsMode.CREATE,
        )

    def _get(
        self,
        target: str,
        *,
        exceptType: ItemType = ItemType.FILE,
        unExistsMode: UnExistsMode = UnExistsMode.WARN,
        errorMode: ErrorMode = ErrorMode.WARN,
    ) -> "FileSystemItem":
        """Get item directly from this directory (internal method).

        Args:
            target (str): Name of the item to get.
            exceptType (ItemType, optional): Expected item type. Defaults to FILE.
            unExistsMode (UnExistsMode, optional): How to handle non-existent items. Defaults to WARN.
            errorMode (ErrorMode, optional): General error handling mode. Defaults to WARN.

        Returns:
            FileSystemItem: FileSystemItem for the target.
        """
        _target = self.path / target

        return createItem(
            _target,
            unExistsMode=unExistsMode,
            exceptType=exceptType,
            errorMode=errorMode,
        )

    def _has(
        self, target: str, *, allowedTargetType: _tt.Union[ItemType, None] = None
    ) -> bool:
        """Check if item exists directly in this directory (internal method).

        Args:
            target (str): Name of the item to check.
            allowedTargetType (ItemType, optional): Expected item type or None for any.

        Returns:
            bool: True if item exists and matches type (if specified).
        """
        item = self._get(target, unExistsMode=UnExistsMode.IGNORE)
        if not item.exists():
            return False
        return allowedTargetType is None or item.itemType == allowedTargetType

    def __contains__(
        self, target: "_tt.Union[_tt.RelativePathable, FileSystemItem]"
    ) -> bool:
        """Check if target exists in this directory (supports 'in' operator).

        Args:
            target (Union[RelativePathable, FileSystemItem]): Path string or FileSystemItem to check for.

        Returns:
            bool: True if target exists in this directory.
        """
        _target = target.path if isinstance(target, FileSystemItemBase) else target

        return self.has(
            _target,
            allowedTargetType=(
                target.itemType if isinstance(target, FileSystemItemBase) else None
            ),
        )


FileSystemItem = _tt.Union[File, Directory]
"""Union type representing either a File or Directory object.

.. versionadded:: 2.1.0
"""


FileSystemItemLike = _tt.Union[_tt.Pathable, "FileSystemItem"]
"""Union type for objects that can be converted to FileSystemItem.

Includes path strings/objects and existing FileSystemItem instances.

.. versionadded:: 2.2.0
"""


@_deprecated("Use Directory instead", version="2.0")
class Folder(Directory):
    """Legacy alias for Directory class.
    
    .. deprecated:: 2.0
       Use Directory class instead. This class exists only for migration 
       convenience from version 1.0.
    """
