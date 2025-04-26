from .path import Path
from . import (
    exception as _ex,
    globalType as _tt,
    warn as _warn,
)  # pylint: disable=unused-import
import shutil as _shutil
import hashlib
from deprecated import deprecated as _deprecated
from enum import Enum

class UnExistsMode(Enum):
    """
    The mode to use when the path does not exist.
    """
    WARN = "warn"
    ERROR = "error"
    IGNORE = "ignore"
    CREATE = "create"

class CreateType(Enum):
    """
    The type of the file to create.
    """
    FILE = "file"
    DIR = "dir"


class File(object):
    """
    The base class for file and directory.
    You can use this class to create a file or directory.

    Args:
        path (Pathable): The path of the file or directory.
        toAbsolute (bool, optional): Whether the path is absolute. Defaults to False.
        redirect (bool, optional): Whether to redirect to Directory when the path is a directory. Defaults to True.
        unExistsMode (UnExistsMode, optional): The mode to use when the path does not exist. Defaults to UnExistsMode.WARN.

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
    ) -> "_tt.Union[_tt.Self , Directory]":
        path = Path(path)
        if redirect and cls is File and path.is_dir():
            cls = Directory  # pylint: disable=self-cls-assignment
        return super().__new__(cls)  # type: ignore

    def checkExists(self, unExistsMode) -> None:
        if self.path.exists():
            return

        if unExistsMode.value == UnExistsMode.WARN.value:
            _warn.warn(
                "Path does not exist: {0}".format(self.path),
                _warn.PathNotExistsWarning,
            )
        elif unExistsMode.value == UnExistsMode.ERROR.value:
            raise _ex.PathNotExistsError("Path does not exist: {0}".format(self.path))
        elif unExistsMode.value == UnExistsMode.IGNORE.value:
            pass
        elif unExistsMode.value == UnExistsMode.CREATE.value:
            self.createSelf()
        else:
            raise ValueError("Invalid unExistsMode: {0}".format(unExistsMode))

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
        Create the file or directory if it does not exist.
        It will be called automatically when the unExistsMode is UnExistsMode.CREATE.
        """
        self.path.touch()

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def extension(self) -> str:
        return self.path.suffix

    def __str__(self) -> str:
        return "<File {0}>".format(self.name)

    def open(self, *args, **kwargs):
        """
        Open the file.
        """
        return self.path.open(*args, **kwargs)  # pylint: disable=unspecified-encoding

    @property
    def content(self) -> _tt.Union[bytes , _tt.NoReturn]:
        with self.open("rb") as file:
            return _tt.cast(bytes, file.read())

    @content.setter
    def content(self, content: bytes) -> None:
        with self.open("wb") as file:
            file.write(_tt.cast(_tt.Any, content))

    @property
    def state(self):
        return self.path.stat()

    def delete(self) -> None:
        """
        Delete the file or directory.
        """
        self.path.unlink()

    def copy(self, path: _tt.Pathable) -> None:
        """
        Copy the file to the target path.
        
        Warning: Even the higher-level file copying functions cannot copy all file metadata.
        """
        _shutil.copy2(self.path, path)

    def move(self, path: _tt.Pathable) -> None:
        """
        Move the file to the target path.
        """
        target=Path(path)
        _shutil.move(self.path, path)
        self.path=target

    def exists(self) -> bool:
        """
        Check if the file or directory exists.
        """
        return self.path.exists()

    def isFile(self) -> bool:
        """"
        Check if the path is a file.
        """
        return self.path.is_file()

    def hash(self, algorithm: str = "md5") -> str:
        """
        Calculate the hash of the file.
        """
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(self.content)
        return hash_obj.hexdigest()


class Directory(File):
    def createSelf(self) -> None:
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)

    def open(self, *args, **kwargs):
        raise _ex.OpenDirectoryError(
            "Directory cannot be opened and read: {0}".format(self.path)
        )

    def delete(self) -> None:
        _shutil.rmtree(self.path)

    def copy(self, path: _tt.Pathable) -> None:
        _shutil.copytree(self.path, path)

    def __iter__(self) -> _tt.Iterator[File]:

        l = self.path.iterdir()

        for i in l:
            yield File(i)

    def __str__(self) -> str:
        return "<Directory {0}>".format(self.name)

    def __getitem__(self, name: str) -> File:

        return self.get(name, unExistsMode=UnExistsMode.ERROR)

    def relative_to(self, target: _tt.Pathable) -> Path:
        if not isinstance(target, Path):
            target = Path(target)
        if target.is_absolute():
            target = target.relative_to(self.path)
        return target

    def create(
        self,
        target: _tt.Union[str, Path, _tt.Sequence[str]],
        createType: CreateType = CreateType.FILE,
    ):
        """
        Create a file or directory.

        Args:
            target (_tt.Union[str, Path, _tt.Sequence[str]]): The target path to create.
            createType (CreateType, optional): The type of the file or directory to create. Defaults to CreateType.FILE.

        Raises:
            ValueError: If the target is not a valid path or the createType is not valid.

        Returns:
            _tt.Union[File, Directory]: The created file or directory.
        """
        step = target
        if isinstance(step, str):
            step = Path(step)

        if isinstance(step, Path):
            if step.is_absolute():
                step = step.relative_to(self.path)
            step = step.parts

        if not isinstance(step, _tt.Sequence) or len(step) == 0:
            raise ValueError("Invalid target {0}".format(target))

        if len(step) == 1:
            if createType == CreateType.FILE:
                return self.get(step[0], unExistsMode=UnExistsMode.CREATE)
            elif createType == CreateType.DIR:
                return self.getFolder(step[0], unExistsMode=UnExistsMode.CREATE)
            else:
                raise ValueError("Invalid createType {0}".format(createType))

        else:
            return self.getFolder(step[0], unExistsMode=UnExistsMode.CREATE).create(step[1:], createType)

    def get(self, name: str, unExistsMode=UnExistsMode.WARN) -> File:
        return File(self.path / name, unExistsMode=unExistsMode)

    def getFolder(self, name: str, unExistsMode=UnExistsMode.WARN) -> "Directory":
        return Directory(self.path / name, unExistsMode=unExistsMode)

    def has(self, name: str) -> bool:
        return (self.path / name).exists()


@_deprecated("Use Directory instead")
class Folder(Directory):
    """
    Deprecated: Use Directory instead.
    """
