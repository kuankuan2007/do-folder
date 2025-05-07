"""
The main part of the doFolder module.
Provides classes and methods for managing files and directories.
"""

import shutil as _shutil
import hashlib
from enum import Enum
import json
from deprecated import deprecated as _deprecated

from .path import Path, relativePathableFormat

from . import (
    exception as _ex,
    globalType as _tt,
)  # pylint: disable=unused-import


class UnExistsMode(Enum):
    """
    Enum representing the behavior when a path does not exist.

    Attributes:
        WARN: Issue a warning if the path does not exist.
        ERROR: Raise an error if the path does not exist.
        IGNORE: Ignore the missing path.
        CREATE: Create the path if it does not exist.
    """
    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"
    CREATE = "create"


class ItemType(Enum):
    """
    Enum representing the type of a file system item.

    Attributes:
        FILE: Represents a file.
        DIR: Represents a directory.
    """
    FILE = "file"
    DIR = "dir"


def isDir(target: "FileSystemItem") -> " _tt.TypeIs[Directory]":
    """
    Determine if the given target is a directory.

    Args:
        target (FileSystemItem): The file system item to check.

    Returns:
        bool: True if the target is a directory, False otherwise.
    """
    return target.itemType == ItemType.DIR


def isFile(target: "FileSystemItem") -> " _tt.TypeIs[File]":
    """
    Determine if the given target is a file.

    Args:
        target (FileSystemItem): The file system item to check.

    Returns:
        bool: True if the target is a file, False otherwise.
    """
    return target.itemType == ItemType.FILE


def createItem(
    path: _tt.Pathable,
    unExistsMode: UnExistsMode = UnExistsMode.WARN,
    errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    toAbsolute: bool = False,
    exceptType: _tt.Union[ItemType, None] = None,
) -> "FileSystemItem":
    """
    Create a file system item (file or directory) based on the given path.

    Args:
        path (Pathable): The path to the file or directory.
        unExistsMode (UnExistsMode, optional): Behavior when the path does not exist.
        errorMode (ErrorMode, optional): Error handling mode.
        toAbsolute (bool, optional): Convert the path to an absolute path.
        exceptType (ItemType, optional): Expected type of the item (file or directory).

    Returns:
        FileSystemItem: The created file or directory object.
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


class FileSystemItemBase(_tt.abc.ABC):
    """
    Abstract base class for file and directory objects.

    Attributes:
        path (Path): The path to the file or directory.
    """

    path: Path

    @property
    @_tt.abc.abstractmethod
    def itemType(self) -> ItemType:
        """
        Get the type of the file system item.

        Returns:
            ItemType: The type of the item (FILE or DIR).
        """
        raise NotImplementedError("itemType is not implemented")

    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        path: _tt.Pathable,
        unExistsMode: UnExistsMode = UnExistsMode.WARN,
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
        toAbsolute: bool = False,
        exceptType: _tt.Union[ItemType, None] = None,
    ):
        """
        Initialize a file system item.

        Args:
            path (Pathable): The path to the file or directory.
            unExistsMode (UnExistsMode, optional): Behavior when the path does not exist.
            errorMode (ErrorMode, optional): Error handling mode.
            toAbsolute (bool, optional): Convert the path to an absolute path.
            exceptType (ItemType, optional): Expected type of the item (file or directory).
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
        """
        Verify if the file or directory exists, and handle it based on the unExistsMode.

        Args:
            unExistsMode (UnExistsMode): Behavior when the path does not exist.

        Raises:
            PathNotExistsError: If the path does not exist and unExistsMode is ERROR.
            ValueError: If the unExistsMode is invalid.
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
        """
        Check if the item type matches the expected type.

        Args:
            itemType (ItemType): The expected item type.

        Returns:
            bool: True if the item type matches, False otherwise.
        """
        return self.itemType == itemType

    @_tt.abc.abstractmethod
    def createSelf(self) -> None:
        """
        Create the file system item.
        """
        raise NotImplementedError("createSelf is not implemented")

    def exists(self) -> bool:
        """
        Check if the item exists.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        return self.path.exists()

    @property
    def name(self) -> str:
        """
        Get the name of the file or directory.

        Returns:
            str: The name of the file or directory.
        """
        return self.path.name

    @property
    def extension(self) -> str:
        """
        Get the extension of the file.

        Returns:
            str: The extension of the file.
        """
        return self.path.suffix

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path}>"

    def isFile(self) -> bool:
        """
        Check if the item is a file.

        Returns:
            bool: True if the item is a file, False otherwise.
        """
        return self.path.is_file()

    def isDir(self) -> bool:
        """
        Check if the item is a directory.

        Returns:
            bool: True if the item is a directory, False otherwise.
        """
        return self.path.is_dir()

    @property
    def state(self):
        """
        Get the state of the file or directory.

        Returns:
            os.stat_result: The state of the file or directory.
        """
        return self.path.stat()

    def parent(self) -> "Directory":
        """
        Get the parent directory of the file or directory.

        Returns:
            Directory: The parent directory of the file or directory.
        """
        return Directory(self.path.parent, unExistsMode=UnExistsMode.IGNORE)

    @_tt.abc.abstractmethod
    def move(self, target: _tt.Pathable) -> None:
        """
        Move the item to the target path.

        Args:
            target (Pathable): The target path to move the item to.
        """
        raise NotImplementedError("move is not implemented")

    @_tt.abc.abstractmethod
    def copy(self, target: _tt.Pathable) -> None:
        """
        Copy the item to the target path.

        Args:
            target (Pathable): The target path to copy the item to.
        """
        raise NotImplementedError("copy is not implemented")

    @_tt.abc.abstractmethod
    def delete(self) -> None:
        """
        Delete the item.
        """
        raise NotImplementedError("delete is not implemented")


class File(FileSystemItemBase):
    """
    Represents a file in the file system.

    Provides methods for file operations such as reading, writing, copying, and deleting.
    """

    @property
    def itemType(self) -> ItemType:
        """
        Get the type of the file system item.

        Returns:
            ItemType: Always returns ItemType.FILE.
        """
        return ItemType.FILE

    def createSelf(self) -> None:
        """
        Create the file if it does not exist.
        """
        self.path.touch()

    def open(self, *args, **kwargs):
        """
        Open the file with the specified mode and options.

        Args:
            *args: Positional arguments for the open function.
            **kwargs: Keyword arguments for the open function.

        Returns:
            file object: The opened file object.
        """
        return self.path.open(*args, **kwargs)  # pylint: disable=unspecified-encoding

    @property
    def content(self) -> _tt.Union[bytes, _tt.NoReturn]:
        """
        Get the content of the file as bytes.

        Returns:
            bytes: The content of the file.
        """
        with self.open("rb") as file:
            return _tt.cast(bytes, file.read())

    @content.setter
    def content(self, content: bytes) -> None:
        """
        Set the content of the file.

        Args:
            content (bytes): The content to write to the file.
        """
        with self.open("wb") as file:
            file.write(_tt.cast(_tt.Any, content))

    def delete(self) -> None:
        """
        Delete the file.
        """
        self.path.unlink()

    def copy(self, target: _tt.Pathable) -> None:
        """
        Copy the file to the specified path.

        Args:
            target (Pathable): The target path to copy the file to.
        """
        _shutil.copy2(self.path, target)

    def move(self, target: _tt.Pathable) -> None:
        """
        Move the file to the specified path.

        Args:
            target (Pathable): The target path to move the file to.
        """
        target = Path(target)
        _shutil.move(self.path, target)
        self.path = target

    def hash(self, algorithm: str = "md5") -> str:
        """
        Calculate the hash of the file content using the specified algorithm.

        Args:
            algorithm (str, optional): The hash algorithm to use. Defaults to "md5".

        Returns:
            str: The hash value of the file content.
        """
        hashObj = hashlib.new(algorithm)
        hashObj.update(self.content)
        return hashObj.hexdigest()

    def loadAsJson(self, encoding: str = "utf-8", **kw) -> _tt.Any:
        """
        Load the file content as JSON.

        Args:
            encoding (str, optional): The encoding to use. Defaults to "utf-8".
            **kw: Additional arguments for the json.load function.

        Returns:
            Any: The parsed JSON content.
        """
        with self.open("r", encoding=encoding) as file:
            return json.load(file, **kw)

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
        """
        Save the given data as JSON to the file.

        Args:
            data (Any): The data to save as JSON.
            encoding (str, optional): The encoding to use. Defaults to "utf-8".
            skipkeys (bool, optional): Skip keys that are not serializable. Defaults to False.
            ensure_ascii (bool, optional): Ensure ASCII encoding. Defaults to True.
            check_circular (bool, optional): Check for circular references. Defaults to True.
            allow_nan (bool, optional): Allow NaN values. Defaults to True.
            cls (type, optional): Custom JSON encoder class. Defaults to None.
            indent (int, optional): Indentation level. Defaults to None.
            separators (tuple, optional): Custom separators. Defaults to None.
            default (callable, optional): Custom serialization function. Defaults to None.
            sort_keys (bool, optional): Sort keys in the output. Defaults to False.
            **kw: Additional arguments for the json.dump function.
        """
        with self.open("w", encoding=encoding) as file:
            json.dump(
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
    """
    Represents a directory in the file system.

    Provides methods for directory operations such as creating,
    deleting, copying, and iterating over contents.
    """

    @property
    def itemType(self) -> ItemType:
        """
        Get the type of the file system item.

        Returns:
            ItemType: Always returns ItemType.DIR.
        """
        return ItemType.DIR

    def createSelf(self) -> None:
        """
        Create the directory if it does not exist.
        """
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)

    def delete(self) -> None:
        """
        Delete the directory and all its contents.
        """
        _shutil.rmtree(self.path)

    def copy(self, target: _tt.Pathable) -> None:
        """
        Copy the directory and its contents to the specified path.

        Args:
            target (Pathable): The target path to copy the directory to.
        """
        _shutil.copytree(self.path, target)

    def move(self, target: _tt.Pathable) -> None:
        """
        Move the directory and its contents to the specified path.

        Args:
            target (Pathable): The target path to move the directory to.
        """
        _shutil.move(self.path, target)
        self.path = Path(target)

    def __iter__(self) -> "_tt.Iterator[FileSystemItem]":
        """
        Iterate over the files and directories in this directory.

        Yields:
            FileSystemItem: Each file or directory in the directory.
        """
        l = self.path.iterdir()

        for i in l:
            yield createItem(i)

    def __getitem__(self, name: str) -> "FileSystemItem":
        """
        Get a file or directory by name.

        Args:
            name (str): The name of the file or directory.

        Returns:
            FileSystemItem: The file or directory object.
        """
        return self._get(name, unExistsMode=UnExistsMode.ERROR)

    def create(
        self,
        target: _tt.RelativePathable,
        createType: ItemType = ItemType.FILE,
        *,
        existsErrorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> "FileSystemItem":
        """
        Create a file or directory in this directory.

        Args:
            target (RelativePathable): The relative path to the file or directory.
            createType (ItemType, optional): The type of the item to create (FILE or DIR).
            existsErrorMode (ErrorMode, optional): Error handling mode for existing paths.
            errorMode (ErrorMode, optional): Error handling mode.

        Returns:
            FileSystemItem: The created file or directory object.
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
        existsErrorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> "File":
        """
        Create a file in this directory.

        Args:
            target (RelativePathable): The relative path to the file.
            existsErrorMode (ErrorMode, optional): Error handling mode for existing paths.
            errorMode (ErrorMode, optional): Error handling mode.

        Returns:
            File: The created file object.

        Raises:
            PathTypeError: If the created item is not a file.
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
        existsErrorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> "Directory":
        """
        Create a directory in this directory.

        Args:
            target (RelativePathable): The relative path to the directory.
            existsErrorMode (ErrorMode, optional): Error handling mode for existing paths.
            errorMode (ErrorMode, optional): Error handling mode.

        Returns:
            Directory: The created directory object.

        Raises:
            PathTypeError: If the created item is not a directory.
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
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> "FileSystemItem":
        """
        Get a file or directory in this directory.

        Args:
            target (RelativePathable): The relative path to the file or directory.
            exceptType (ItemType, optional): Expected type of the item (FILE or DIR).
            unExistsMode (UnExistsMode, optional): Behavior when the path does not exist.
            errorMode (ErrorMode, optional): Error handling mode.

        Returns:
            FileSystemItem: The file or directory object.
        """
        return self.deepCall(
            target,
            "_get",
            allowedTargetType=unExistsMode == UnExistsMode.CREATE,
            unExistsMode=unExistsMode,
            errorMode=errorMode,
            exceptType=exceptType,
        )

    def getFile(
        self,
        target: _tt.RelativePathable,
        *,
        unExistsMode: UnExistsMode = UnExistsMode.WARN,
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> "File":
        """
        Get a file in this directory.

        Args:
            target (RelativePathable): The relative path to the file.
            unExistsMode (UnExistsMode, optional): Behavior when the path does not exist.
            errorMode (ErrorMode, optional): Error handling mode.

        Returns:
            File: The file object.

        Raises:
            PathTypeError: If the retrieved item is not a file.
        """
        res = self.deepCall(
            target,
            "_get",
            allowedTargetType=unExistsMode == UnExistsMode.CREATE,
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
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> "Directory":
        """
        Get a directory in this directory.

        Args:
            target (RelativePathable): The relative path to the directory.
            unExistsMode (UnExistsMode, optional): Behavior when the path does not exist.
            errorMode (ErrorMode, optional): Error handling mode.

        Returns:
            Directory: The directory object.

        Raises:
            PathTypeError: If the retrieved item is not a directory.
        """
        res = self.deepCall(
            target,
            "_get",
            allowedTargetType=unExistsMode == UnExistsMode.CREATE,
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
        """
        Check if a file or directory exists in this directory.

        Args:
            target (RelativePathable): The relative path to the file or directory.
            allowedTargetType (ItemType, optional): Expected type of the item (FILE or DIR).

        Returns:
            bool: True if the item exists, False otherwise.
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
        """
        Perform a deep call on the directory.

        Args:
            target (RelativePathable): The relative path to the file or directory.
            func (str): The function to call.
            createMiddleDir (bool, optional): Create intermediate directories if needed.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Any: The result of the function call.
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
        existsErrorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> "FileSystemItem":
        """
        Create a file or directory in this directory.

        Args:
            target (str): The name of the file or directory.
            createType (ItemType, optional): The type of the item to create (FILE or DIR).
            existsErrorMode (ErrorMode, optional): Error handling mode for existing paths.
            errorMode (ErrorMode, optional): Error handling mode.

        Returns:
            FileSystemItem: The created file or directory object.
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
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> "FileSystemItem":
        """
        Get a file or directory in this directory.

        Args:
            target (str): The name of the file or directory.
            exceptType (ItemType, optional): Expected type of the item (FILE or DIR).
            unExistsMode (UnExistsMode, optional): Behavior when the path does not exist.
            errorMode (ErrorMode, optional): Error handling mode.

        Returns:
            FileSystemItem: The file or directory object.
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
        """
        Check if a file or directory exists in this directory.

        Args:
            target (str): The name of the file or directory.
            allowedTargetType (ItemType, optional): Expected type of the item (FILE or DIR).

        Returns:
            bool: True if the item exists, False otherwise.
        """
        item = self._get(target, unExistsMode=UnExistsMode.IGNORE)
        if not item.exists():
            return False
        return allowedTargetType is None or item.itemType == allowedTargetType

    def __contains__(
        self, target: "_tt.Union[_tt.RelativePathable, FileSystemItem]"
    ) -> bool:
        """
        Check if a file or directory exists in this directory.

        Args:
            target (Union[RelativePathable, FileSystemItem]): The target file or directory.

        Returns:
            bool: True if the target exists, False otherwise.
        """
        _target = target.path if isinstance(
            target, FileSystemItemBase) else target

        return self.has(
            _target,
            allowedTargetType=(
                target.itemType if isinstance(
                    target, FileSystemItemBase) else None
            ),
        )


FileSystemItem = _tt.Union[File, Directory]


@_deprecated("Use Directory instead")
class Folder(Directory):
    """
    Deprecated: Use the Directory class instead.
    """
