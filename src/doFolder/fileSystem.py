"""
The main part of the doFolder module.
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


def isDirectory(target: "File") -> " _tt.TypeIs[Directory]":
    """
    Check if the target is a directory.

    Args:
        target (File): The file object to check.

    Returns:
        bool: True if the target is a directory, False otherwise.
    """
    return isinstance(target, Directory)


class UnExistsMode(Enum):
    """
    The mode to use when the path does not exist.
    """

    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"
    CREATE = "create"


class ItemType(Enum):
    """
    The type of the file to create.
    """

    FILE = "file"
    DIR = "dir"


class File:
    """
    The base class for file and directory.
    You can use this class to create a file or directory.

    Args:
        path (_tt.Pathable): The path of the file or directory.
        toAbsolute (bool, optional): Whether the path is absolute. Defaults to False.
        redirect (bool, optional): Whether to redirect to Directory
                                    when the path is a directory. Defaults to True.
        unExistsMode (UnExistsMode, optional): The mode to use when the path does not exist.
                                                Defaults to UnExistsMode.WARN.

    Raises:
        _ex.PathNotExistsError: When the path does not exist and unExistsMode is UnExistsMode.ERROR.
        ValueError: When the unExistsMode is not a valid UnExistsMode.
    """

    path: Path

    @_tt.overload
    def __new__(
        cls,
        path: _tt.Pathable,
        *,
        toAbsolute: bool = False,
        redirect: _tt.Literal[False] = False,
        unExistsMode=UnExistsMode.WARN,
    ) -> "_tt.Self": ...

    @_tt.overload
    def __new__(
        cls,
        path: _tt.Pathable,
        *,
        toAbsolute: bool,
        redirect: _tt.Literal[True] = True,
        unExistsMode=UnExistsMode.WARN,
    ) -> "_tt.Union[_tt.Self , Directory]": ...

    def __new__(
        cls, path: _tt.Pathable, *, redirect: bool = True, **kw
    ) -> "_tt.Union[_tt.Self, Directory]":
        path = Path(path)
        if redirect and cls is File and path.is_dir():
            cls = Directory  # pylint: disable=self-cls-assignment
        return super().__new__(cls)  # type: ignore

    def checkExists(self, unExistsMode) -> None:
        """
        Check if the file or directory exists. If not, handle it based on the unExistsMode.

        Args:
            unExistsMode (UnExistsMode): The mode to handle non-existing paths.

        Raises:
            _ex.PathNotExistsError: If the path does not exist and unExistsMode is ERROR.
            ValueError: If the unExistsMode is invalid.
        """
        if self.path.exists():
            return

        if unExistsMode.value == UnExistsMode.WARN.value:
            _ex.warn(
                f"Path does not exist: {self.path}",
                _ex.PathNotExistsWarning,
            )
        elif unExistsMode.value == UnExistsMode.ERROR.value:
            raise _ex.PathNotExistsError(f"Path does not exist: {self.path}")
        elif unExistsMode.value == UnExistsMode.IGNORE.value:
            pass
        elif unExistsMode.value == UnExistsMode.CREATE.value:
            self.createSelf()
        else:
            raise ValueError(f"Invalid unExistsMode: {unExistsMode}")

    def __init__(
        self,
        path: _tt.Pathable,
        *,
        toAbsolute: bool = False,
        redirect: bool = True,  # pylint: disable=unused-argument
        unExistsMode=UnExistsMode.WARN,
    ) -> None:
        self.path = Path(path) if toAbsolute else Path(path).absolute()
        self.checkExists(unExistsMode)

    def createSelf(self) -> None:
        """
        Create the file if it does not exist. Called automatically when unExistsMode is CREATE.
        """
        self.path.touch()

    @property
    def name(self) -> str:
        """The name of the file or directory."""
        return self.path.name

    @property
    def extension(self) -> str:
        """The extension of the file."""
        return self.path.suffix

    def __str__(self) -> str:
        return f"<File {self.name}>"

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
        """Get the content of the file as bytes."""
        with self.open("rb") as file:
            return _tt.cast(bytes, file.read())

    @content.setter
    def content(self, content: bytes) -> None:
        with self.open("wb") as file:
            file.write(_tt.cast(_tt.Any, content))

    @property
    def state(self):
        """Get the state of the file or directory."""
        return self.path.stat()

    @property
    def itemType(self) -> ItemType:
        """Get the type of the file or directory."""
        if self.path.is_file():
            return ItemType.FILE
        if self.path.is_dir():
            return ItemType.DIR
        raise _ex.PathNotExistsError(f"Path does not exist: {self.path}")

    def delete(self) -> None:
        """
        Delete the file or directory.
        """
        self.path.unlink()

    def copy(self, path: _tt.Pathable) -> None:
        """
        Copy the file to the specified path.

        Args:
            path (_tt.Pathable): The target path to copy the file to.


        """
        _shutil.copy2(self.path, path)

    def move(self, path: _tt.Pathable) -> None:
        """
        Move the file to the specified path.

        Args:
            path (_tt.Pathable): The target path to move the file to.
        """
        target = Path(path)
        _shutil.move(self.path, path)
        self.path = target

    def exists(self) -> bool:
        """
        Check if the file or directory exists.

        Returns:
            bool: True if the file or directory exists, False otherwise.
        """
        return self.path.exists()

    def isFile(self) -> bool:
        """
        Check if the path is a file.

        Returns:
            bool: True if the path is a file, False otherwise.
        """
        return self.path.is_file()

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


class Directory(File):
    """
    A class representing a directory, inheriting from File.
    """

    def createSelf(self) -> None:
        """
        Create the directory if it does not exist.
        """
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)

    def open(self, *args, **kwargs):
        """
        Raise an error because directories cannot be opened as files.

        Raises:
            _ex.OpenDirectoryError: Always raised when this method is called.
        """
        raise _ex.OpenDirectoryError(
            f"Directory cannot be opened and read: {self.path}"
        )

    def delete(self) -> None:
        """
        Delete the directory and all its contents.
        """
        _shutil.rmtree(self.path)

    def copy(self, path: _tt.Pathable) -> None:
        """
        Copy the directory and its contents to the specified path.

        Args:
            path (_tt.Pathable): The target path to copy the directory to.
        """
        _shutil.copytree(self.path, path)

    def __iter__(self) -> _tt.Iterator[File]:
        """
        Iterate over the files and directories in this directory.

        Yields:
            File: Each file or directory in the directory.
        """
        l = self.path.iterdir()

        for i in l:
            yield File(i)

    def __str__(self) -> str:
        return f"<Directory {self.name}>"

    def __getitem__(self, name: str) -> File:
        """
        Get a file or directory by name.

        Args:
            name (str): The name of the file or directory.

        Returns:
            File: The file or directory object.
        """
        return self.get(name, unExistsMode=UnExistsMode.ERROR)

    def relativeTo(self, target: _tt.Pathable) -> Path:
        """
        Get the relative path from this directory to the target.

        Args:
            target (_tt.Pathable): The target path.

        Returns:
            Path: The relative path.
        """
        if not isinstance(target, Path):
            target = Path(target)
        if target.is_absolute():
            target = target.relative_to(self.path)
        return target

    @_tt.overload
    def create(
        self,
        target: _tt.RelativePathable,
        createType: _tt.Literal[ItemType.FILE],
    ) -> File: ...

    @_tt.overload
    def create(
        self,
        target: _tt.RelativePathable,
        createType: _tt.Literal[ItemType.DIR],
    ) -> "Directory": ...
    def create(
        self,
        target: _tt.RelativePathable,
        createType: ItemType = ItemType.FILE,
    ):
        """
        Create a file or directory at the specified relative path.

        Args:
            target (_tt.RelativePathable): The relative path to create.
            createType (ItemType, optional): The type of item to create. Defaults to ItemType.FILE.

        Returns:
            Union[File, Directory]: The created file or directory.
        """
        step = relativePathableFormat(target, self.path)

        if len(step) == 1:
            if createType == ItemType.FILE:
                return self.get(step[0], unExistsMode=UnExistsMode.CREATE)
            if createType == ItemType.DIR:
                return self.getFolder(step[0], unExistsMode=UnExistsMode.CREATE)
            raise ValueError(f"Invalid createType {createType}")

        return self.getFolder(step[0], unExistsMode=UnExistsMode.CREATE).create(
            step[1:], createType
        )

    def createFile(self, target: _tt.RelativePathable) -> File:
        """
        Create a file at the specified relative path.

        Args:
            target (_tt.RelativePathable): The relative path to create the file.

        Returns:
            File: The created file.
        """
        return self.create(target, ItemType.FILE)

    def createDir(self, target: _tt.RelativePathable) -> "Directory":
        """
        Create a directory at the specified relative path.

        Args:
            target (_tt.RelativePathable): The relative path to create the directory.

        Returns:
            Directory: The created directory.
        """
        return self.create(target, ItemType.DIR)

    def get(self, name: str, unExistsMode=UnExistsMode.WARN) -> File:
        """
        Get a file by name, creating it if necessary based on unExistsMode.

        Args:
            name (str): The name of the file.
            unExistsMode (UnExistsMode, optional): The mode to handle non-existing files.
                                                    Defaults to UnExistsMode.WARN.

        Returns:
            File: The file object.
        """
        return File(self.path / name, unExistsMode=unExistsMode)

    def getFolder(self, name: str, unExistsMode=UnExistsMode.WARN) -> "Directory":
        """
        Get a directory by name, creating it if necessary based on unExistsMode.

        Args:
            name (str): The name of the directory.
            unExistsMode (UnExistsMode, optional): The mode to handle non-existing directories.
                                                    Defaults to UnExistsMode.WARN.

        Returns:
            Directory: The directory object.
        """
        return Directory(self.path / name, unExistsMode=unExistsMode)

    def has(
        self,
        target: _tt.Union[_tt.RelativePathable, File],
        targetType: _tt.Union[ItemType, None] = None,
        errorMode: _ex.ErrorMode = _ex.ErrorMode.WARN,
    ) -> bool:
        """
        Check if a file or directory exists in this directory.

        Args:
            target (Union[RelativePathable, File]): The target file or directory.
            targetType (Union[ItemType, None], optional): The expected type of the target.
                                                                Defaults to None.
            errorMode (_ex.ErrorMode, optional): The error mode to use.
                                                    Defaults to _ex.ErrorMode.WARN.

        Returns:
            bool: True if the target exists, False otherwise.
        """
        _target = target.path if isinstance(target, File) else target

        step = relativePathableFormat(_target, self.path)

        item = self.get(step[0], unExistsMode=UnExistsMode.IGNORE)

        if not item.exists():
            return False

        if len(step) == 1:
            return targetType is None or item.itemType == targetType

        if isDirectory(item):
            return item.has(step[1:], targetType, errorMode)

        _ex.unintended(
            f"{item.path} is a file, not a directory",
            mode=errorMode,
            warnClass=_ex.PathIsNotDirWarning,
            errorClass=_ex.PathIsNotDirError,
        )
        return False

    def __contains__(self, target: _tt.Union[_tt.RelativePathable, File]) -> bool:
        """
        Check if a file or directory exists in this directory.

        Args:
            target (Union[RelativePathable, File]): The target file or directory.

        Returns:
            bool: True if the target exists, False otherwise.
        """
        return self.has(target, targetType=None, errorMode=_ex.ErrorMode.IGNORE)


@_deprecated("Use Directory instead")
class Folder(Directory):
    """
    Deprecated: Use Directory instead.
    """
