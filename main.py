"""
Copyright (c) 2023 Gou Haoming
doFolder is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
         http://license.coscl.org.cn/MulanPSL2
THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
See the Mulan PSL v2 for more details.
"""
import os
import re
from typing import (
    Any,
    Union,
    Callable,
    Literal,
    List,
    Tuple,
    Iterable,
    TypeVar,
    Generic,
    IO,
    Dict,
    overload,
    Set,
)
import shutil
import copy
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileSystemEvent,
    FileSystemMovedEvent,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
)
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from specialStr import Path
import base64
import json
from concurrent.futures import ThreadPoolExecutor, _base
import time

__all__ = ["File", "Folder", "Path"]

EVENT_TYPES = Literal["created", "deleted", "modified"]

SearchCondition = Union[str, re.Pattern, Callable[[Union["File", "Folder"]], bool]]
FormatedMatching = Tuple[
    Callable[[Union["File", "Folder"]], bool], int, Union[int, None]
]
UnformattedMatching = Union[
    SearchCondition, Tuple[SearchCondition, int, Union[int, None]]
]
_T = TypeVar("_T", bound="_HasName")
_U = TypeVar("_U")


class RuntimeError(Exception):
    def __init__(self, error: BaseException) -> None:
        super().__init__(str(error))
        self.error = error


class DisabledError(Exception):
    pass


class UnknownError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Sorry, an unknown error has occurred. This could have been due to an oversight by the author. If you feel the same way, open an issue on Gitee(https://gitee.com/kuankuan2007/do-folder) or Github(https://github.com/kuankuan2007/do-folder)"
        )


def tryRun(fn: Callable[..., _U]) -> Union[_U, RuntimeError]:
    try:
        return fn()
    except BaseException as e:
        return RuntimeError(e)


class _HasName(Generic[_T]):
    name: str


class _FolderUpdateHeader(FileSystemEventHandler):
    def __init__(self, target: "Folder"):
        self.target = target

    def on_moved(self, event: FileSystemMovedEvent):
        self.target._update(
            Path(event.src_path).findRest(self.target.path),
            EVENT_TYPE_DELETED,
            Path(event.src_path),
            event.is_directory,
        )
        self.target._update(
            Path(event.dest_path).findRest(self.target.path),
            EVENT_TYPE_CREATED,
            Path(event.dest_path),
            event.is_directory,
        )

    def on_deleted(self, event: FileSystemEvent):
        self.target._update(
            Path(event.src_path).findRest(self.target.path),
            event.event_type,
            Path(event.src_path),
            event.is_directory,
        )

    def on_created(self, event: FileSystemEvent):
        self.target._update(
            Path(event.src_path).findRest(self.target.path),
            event.event_type,
            Path(event.src_path),
            event.is_directory,
        )

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        self.target._update(
            Path(event.src_path).findRest(self.target.path),
            event.event_type,
            Path(event.src_path),
            event.is_directory,
        )


class FolderOrFileNotFoundError(Exception):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self) -> str:
        return str(self.reason)

    def __repr__(self) -> str:
        return str(self.reason)


class FileOrFolderAlreadyExists(Exception):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self) -> str:
        return str(self.reason)

    def __repr__(self) -> str:
        return str(self.reason)


def _formatMatching(condition: UnformattedMatching) -> FormatedMatching:
    limit = (1, 1)
    if isinstance(condition, tuple) and not callable(condition):
        limit = (condition[1], condition[2])
        condition = condition[0]
    if isinstance(condition, str) and not callable(condition):
        match: Callable[[Union["File", "Folder"]], bool] = (
            lambda item: item.name == condition
        )
    elif isinstance(condition, re.Pattern) and not callable(condition):
        match: Callable[[Union["File", "Folder"]], bool] = lambda item: bool(
            condition.search(item.name)
        )
    elif callable(condition):
        match = condition
    else:
        raise ValueError(f'Unknown condition "{condition}" type is "{type(condition)}"')
    return (match, limit[0], limit[1])


class _ObjectListIndexedByName(Generic[_T]):
    def __init__(self, var: Iterable[_T] = []):
        self.values: List[_T] = list(var)

    def remove(self, var: _T) -> None:
        self.values.remove(var)

    def removeByName(self, name: str) -> None:
        for i in self.values:
            if i.name == name:
                self.values.remove(i)
                return
        raise ValueError(f'No Object named "{name}"')

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} len={len(self.values)}>"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.values}>"

    def append(self, var: _T):
        self.values.append(var)

    def __len__(self):
        return len(self.values)

    def __add__(self, var: "_ObjectListIndexedByName"):
        return _ObjectListIndexedByName(self.values + var.values)

    def __contains__(self, var: Union[_T, str]) -> bool:
        if var in self.values:
            return True
        for i in range(len(self.values)):
            if self.values[i].name == var:
                return True
        return False

    def __getitem__(self, key: Union[int, str]) -> Union[_T, None]:
        if isinstance(key, str):
            for i in self.values:
                if i.name == key:
                    return i
            return None
        elif isinstance(key, int):
            return self.values[key]
        return None

    def __getattribute__(self, key: str) -> Any:
        try:
            return super().__getattribute__(key)
        except AttributeError:
            for i in self.values:
                if i.name == key:
                    return i
            raise AttributeError(f"name {key} is neither attribute or name of values")

    def __iter__(self):
        return self.values.__iter__()

    def getSubAttribute(self, key: str) -> List:
        retsult = []
        for i in self:
            if isinstance(tryRun(lambda: i.__getattribute__(key)), RuntimeError):
                raise AttributeError(
                    f'Not all attributes named "{key}" of the list are existent'
                )
            retsult.append(i.__getattribute__(key))
        return retsult

    def callSubAttribute(self, fn: str, *args, **kw) -> Any:
        li = self.getSubAttribute(fn)
        for i in li:
            if not callable(i):
                raise AttributeError(
                    f'Not all attributes named "{fn}" of the list are callable'
                )
        return [tryRun(lambda: i(*args, **kw)) for i in li]


class SearchResult(_ObjectListIndexedByName[Union["File", "Folder"]]):
    def __init__(
        self,
        var: Iterable[Union["File", "Folder"]] = [],
        match: Union[FormatedMatching, None] = None,
    ):
        super().__init__(var)
        self.match = match

    def __add__(self, var: "SearchResult"):
        return SearchResult(self.values + var.values, match=self.match)

    def remove(self) -> None:
        self.callSubAttribute("remove")

    def copy(self, path: Union[str, Path]) -> None:
        self.callSubAttribute("copy", path)

    def move(self, path: Union[str, Path]) -> None:
        self.callSubAttribute("move", path)

    def rename(self, newName: str) -> None:
        li = self.getSubAttribute("rename")
        for index, i in enumerate(li):
            i(newName.format(index, i=index, index=index))


class FileList(_ObjectListIndexedByName["File"]):
    def __init__(self, var: Iterable["File"] = []):
        super().__init__(var)

    def __add__(self, var: "FileList"):
        return FileList(self.values + var.values)


class FolderList(_ObjectListIndexedByName["Folder"]):
    def __init__(self, var: Iterable["Folder"] = []):
        super().__init__(var)

    def __add__(self, var: "FolderList"):
        return FolderList(self.values + var.values)


class FileSystemNode(_HasName):
    path: Path
    copy: Callable[[], None]
    remove: Callable[[], None]
    move: Callable[[str], None]
    rename: Callable[[str], None]


class File(FileSystemNode):
    def __init__(self, path: Union[str, Path], parent: Union["Folder", None] = None):
        self._active = True
        if not isinstance(path, Path):
            path = Path(path)
        self.path = path
        self.parent = parent
        self.refresh()

    def deactivate(self):
        """
        Deactivates the object.
        """
        self._active = False

    def refresh(self):
        """Rebuild all of this file object"""
        state = os.stat(self.path)
        self.mode = state.st_mode
        self.ino = state.st_ino
        self.dev = state.st_dev
        self.uid = state.st_uid
        self.gid = state.st_gid
        self.size = state.st_size
        self.mtime = state.st_mtime
        self.ctime = state.st_ctime
        self.atime = state.st_atime
        self._md5: Union[None, str] = None
        self._sha1: Union[None, str] = None
        self._sha256: Union[None, str] = None
        self._sha512: Union[None, str] = None

    @property
    def name(self) -> str:
        return self.path.name

    def open(self, *args, **kw) -> IO:
        """
        Open the file at the given path with the specified arguments and keyword arguments.

        Parameters:
            *args: Variable length argument list.
            **kw: Arbitrary keyword arguments.

        Returns:
            IO: The opened file object.
        """
        
        return open(self.path, *args, **kw)

    def __str__(self) -> str:
        return f'<File "{self.name}">'

    def __repr__(self) -> str:
        return f'<File "{self.name}">'

    @property
    def content(self) -> bytes:
        """
        Return the content of the file as bytes.

        :return: A bytes object containing the content of the file.
        :rtype: bytes
        """
        with self.open("rb") as f:
            return f.read()

    @content.setter
    def _setContent(self, content: bytes):
        """
        Sets the content of the object.

        Parameters:
            content (bytes): The content to be set.

        Returns:
            None
        """
        with self.open("wb") as f:
            f.write(content)
        f.flush()

    @property
    def md5(self) -> str:
        """
        Returns the MD5 hash of the content.

        :return: The MD5 hash as a string.
        :rtype: str
        """
        if self._md5:
            return self._md5
        self._md5 = hashlib.md5(self.content).hexdigest()
        return self._md5

    @property
    def sha1(self) -> str:
        """
        Returns the SHA-1 hash value of the content.

        :return: A string representing the SHA-1 hash value.
        :rtype: str
        """
        if self._sha1:
            return self._sha1
        self._sha1 = hashlib.sha1(self.content).hexdigest()
        return self._sha1

    @property
    def sha256(self) -> str:
        """
        Returns the SHA-256 hash of the content.

        :return: A string representing the SHA-256 hash.
        :rtype: str
        """
        if self._sha256:
            return self._sha256
        self._sha256 = hashlib.sha256(self.content).hexdigest()
        return self._sha256

    @property
    def sha512(self) -> str:
        """
        Returns the SHA512 hash of the content.

        Returns:
            str: The SHA512 hash of the content.
        """
        if self._sha512:
            return self._sha512
        self._sha512 = hashlib.sha512(self.content).hexdigest()
        return self._sha512

    @property
    def hash(self) -> str:
        """
        Returns the hash value of the object.

        :return: A string representing the hash value.
        :rtype: str
        """
        return self.md5

    def remove(self):
        """
        Removes the file at the specified path.
        
        This method deletes the file located at the `self.path` location. If the file has a parent directory, it also updates the parent directory by calling `self.parent._updateRemoveSubItem(self.name)`.
        """
        os.remove(self.path)
        if self.parent:
            self.parent._updateRemoveSubItem(self.name)

    def copy(self, path: str):
        """
        Copy the file or directory at `self.path` to the specified `path`.

        Parameters:
            path (str): The destination path where the file or directory will be copied to.

        Returns:
            None
        """
        shutil.copy(self.path, path)

    def move(self, path: str):
        """
        Move the file or directory represented by this item to the specified path.

        Args:
            path (str): The destination path to move the item to.

        Returns:
            None
        """
        shutil.move(self.path, path)
        if self.parent:
            self.parent._updateRemoveSubItem(self.name)

    def rename(self, newName: str) -> None:
        """
        Renames the object with a new name.

        Parameters:
            newName (str): The new name for the object.

        Returns:
            None
        """
        splitPath = self.path.spitPath(False)
        while len(splitPath) and splitPath[-1] == "":
            splitPath = splitPath[:-1]
        if not len(splitPath):
            raise ValueError("The path has no location to rename")
        splitPath[-1] = newName
        newPath: Path = Path(self.path.driver + "/".join(splitPath))
        os.rename(self.path, newPath)
        if self.parent:
            self.parent._updateRenameSubItem(self.name, newName)

    def __getattribute__(self, __name: str) -> Any:
        if not super().__getattribute__("_active") and __name not in [
            "_active",
            "path",
            "parent",
            "name",
        ]:
            raise DisabledError(
                "Can not get item from disabled file. You abandoned me, and then you flirt with me like this"
            )
        return super().__getattribute__(__name)


class Folder(FileSystemNode):
    def __init__(
        self,
        path: Union[str, Path],
        onlisten: bool = False,
        parent: Union["Folder", None] = None,
        scan: bool = False,
        ignores: Iterable[Union[str, Path]] = [],
        gitignore: bool = False,
    ):
        """
        Args:
            path (Union[str, Path]): The path to the file or directory.
            onlisten (bool, optional): Indicates whether to enable listening for changes. Defaults to False.
            parent (Union["Folder", None], optional): The parent folder. Defaults to None.
            scan (bool, optional): Indicates whether to scan the directory contents. Defaults to False.
            ignores (Iterable[Union[str, Path]], optional): A list of paths to ignore. Defaults to [].
            gitignore (bool, optional): Indicates whether to use the .gitignore file. Defaults to False.
        """
        self._active = True
        if not isinstance(path, Path):
            path = Path(path)
        self.onlisten = onlisten
        self.path = path
        self.parent = parent
        self.scaned = scan
        self.gitignore = gitignore
        self.ignores: List[Path] = []
        self.scan = scan
        self.logger = logging.getLogger(self.name)
        if self.onlisten:
            self.event_handler = _FolderUpdateHeader(self)
            self.observer = Observer()
            self.observer.schedule(self.event_handler, path=path, recursive=True)
            self.observer.start()
        gitignores = []
        if gitignore:
            try:
                with open(path.add(".gitignore"), encoding="utf-8") as f:
                    gitignores = [i[:-1] for i in set(f.readlines())]

            except:
                gitignores = []
        for i in set(gitignores + list(ignores)):
            if not isinstance(i, Path):
                i = Path(path.getAbsolutePath(i))
            self.ignores.append(i)
        if scan:
            self.refresh()

    def deactivate(self):
        """
        Deactivates the object.
        """
        self._active = False

    def refresh(self):
        self.logger.debug("refresh folder contents")
        """Rebuild all of this folder object"""
        self.scaned = True
        self.dir: List[str] = os.listdir(self.path)
        self.files: FileList = FileList([])
        self.subfolder: FolderList = FolderList([])
        for i in self.dir:
            newPath = self.path.add(i)
            if newPath in self.ignores:
                continue
            if os.path.isfile(newPath):
                self.files.append(self._newFile(newPath))
            elif os.path.isdir(newPath):
                self.subfolder.append(self._newSubFolder(newPath))

    def _newFile(self, path: Path) -> File:
        """
        Creates a new File object with the given path and adds it to the current directory.

        Args:
            path (Path): The path of the file to be created.

        Returns:
            File: The newly created File object.

        """
        return File(path, parent=self)

    def _newSubFolder(self, path: Path) -> "Folder":
        """
        Create a new subfolder within the current folder.

        Args:
            path (Path): The path of the new subfolder.

        Returns:
            Folder: The newly created subfolder.
        """
        return Folder(
            path,
            parent=self,
            scan=self.scan,
            ignores=self.ignores,
            gitignore=self.gitignore,
        )

    @property
    def name(self) -> str:
        """
        Returns the name of the object.

        :return: A string representing the name of the object.
        :rtype: str
        """
        return self.path.name

    def __str__(self) -> str:
        return f'<Folder "{self.name}">'

    def __repr__(self) -> str:
        return self.__str__()

    def __contains__(self, item: Union[str, "Folder", "File"]) -> bool:
        if isinstance(item, str):
            return item in self.dir
        elif isinstance(item, Folder):
            return item in self.subfolder
        elif isinstance(item, File):
            return item in self.files
        return False

    def __getitem__(self, key) -> Union["File", "Folder", None]:
        if not self._active and key not in ["path", "name"]:
            raise DisabledError(
                "Can not get item from disabled folder. You abandoned me, and then you flirt with me like this"
            )
        for item in self.subfolder:
            if item.name == key:
                return item
        for item in self.files:
            if item.name == key:
                return item
        return None

    def __travel(self):
        for i in self.files:
            yield i
        for i in self.subfolder:
            yield i

    def __iter__(self):
        return self.__travel()

    def _update(
        self, path: List[str], eventType: str, eventTarget: Path, isDirectory: bool
    ):
        """Update when something changes"""
        if not self.scaned:
            return
        if len(path) > 1:
            nextFolder = self[path[0]]
            if isinstance(nextFolder, Folder):
                nextFolder._update(path[1:], eventType, eventTarget, isDirectory)
            return
        self.logger.debug(f"file content update.{eventType}")
        name = path[0]
        if eventType == EVENT_TYPE_CREATED:
            if name in self:
                return
            if name in self.ignores:
                return
            if isDirectory:
                self.subfolder.append(self._newSubFolder(eventTarget))
            else:
                self.files.append(self._newFile(eventTarget))
        if eventType == EVENT_TYPE_DELETED:
            target = self[name]
            if isinstance(target, Folder):
                self.subfolder.remove(target)
            elif isinstance(target, File):
                self.files.remove(target)
        if eventType == EVENT_TYPE_MODIFIED:
            target = self[name]
            if isinstance(target, Folder):
                target.refresh()

    def __getattribute__(self, name: str) -> Any:
        if not super().__getattribute__("_active") and name not in [
            "path",
            "name",
            "parent",
            "_active",
        ]:
            raise DisabledError(
                "Can not get attributes from disabled folder. You abandoned me, and then you flirt with me like this"
            )
        if not super().__getattribute__("scaned") and name not in [
            "path",
            "name",
            "parent",
            "_active",
            "scaned",
            "refresh",
            "logger",
            "ignores",
        ]:
            self.refresh()
        try:
            return super().__getattribute__(name)
        except AttributeError:
            target = self[name]
            if target:
                return target
            raise AttributeError(f'"{name}" is not a attribute ,a subfolder or a file')

    def forEach(
        self,
        callback: Callable[[Union["File", "Folder"]], Any],
        rootPosition: Literal["first", "last"] = "first",
    ) -> None:
        """
        Go through each of these elements
        :param callback:The function to call
        :rootPosition:Is the root before or after the child element
        """
        if rootPosition == "first":
            callback(self)
        for item in self.files:
            callback(item)
        for item in self.subfolder:
            item.forEach(callback, rootPosition)
        if rootPosition == "last":
            callback(self)

    def forEachFile(self, callback: Callable[[File], Any]) -> None:
        """
        Go through each of these file
        :param callback:The function to call
        """
        for item in self.files:
            callback(item)
        for item in self.subfolder:
            item.forEachFile(callback)

    def forEachFolder(
        self,
        callback: Callable[["Folder"], Any],
        rootPosition: Literal["first", "last"] = "first",
    ) -> None:
        """
        Go through each of these folder
        :param callback:The function to call
        :param rootPosition:Is the root before or after the child element
        """
        if rootPosition == "first":
            callback(self)
        for item in self.subfolder:
            item.forEachFolder(callback, rootPosition)
        if rootPosition == "last":
            callback(self)

    def remove(self) -> None:
        """
        Remove the folder.

        This function removes the folder along with all its contents. It uses the `shutil.rmtree` function to delete the folder recursively. If the folder has a parent, it also calls the `_updateRemoveSubItem` function on the parent to update its internal state.

        Parameters:
            None

        Returns:
            None
        """
        self.logger.info("Removing folder")
        shutil.rmtree(self.path)
        if self.parent:
            self.parent._updateRemoveSubItem(self.name)

    def _updateRemoveSubItem(self, name: str):
        """
        Updates and removes a sub-item from the directory.

        Parameters:
            name (str): The name of the sub-item to be updated and removed.

        Returns:
            None
        """
        item = self[name]
        if item == None:
            return
        elif isinstance(item, File):
            self.files.remove(item)
        elif isinstance(item, Folder):
            self.subfolder.remove(item)
        item.deactivate()

    def move(self, path: str) -> None:
        """
        Move a folder to the specified path.

        Args:
            path (str): The path where the folder will be moved to.

        Returns:
            None: This function does not return anything.
        """
        self.logger.info(f"Moving folder to {path}")
        shutil.move(self.path, path)

    def copy(self, path: str) -> None:
        """
        Copies the entire folder at `self.path` to the specified destination `path`.
        
        Args:
            path (str): The destination path where the folder will be copied.
        
        Returns:
            None: This function does not return anything.
        """
        self.logger.info(f"Copying folder to {path}")
        shutil.copytree(self.path, path)

    def rename(self, newName: str) -> None:
        """
        Renames the file or directory to the specified new name.

        Parameters:
            newName (str): The new name to assign to the file or directory.

        Returns:
            None

        Raises:
            ValueError: If the path has no location to rename.

        Notes:
            - The function modifies the existing file or directory name.
            - If the function is called on a directory, all its sub-items will also be renamed.
        """
        splitPath = self.path.spitPath(False)
        while len(splitPath) and splitPath[-1] == "":
            splitPath = splitPath[:-1]
        if not len(splitPath):
            raise ValueError("The path has no location to rename")
        splitPath[-1] = newName
        newPath: Path = Path(self.path.driver + "/".join(splitPath))
        os.rename(self.path, newPath)
        if self.parent:
            self.parent._updateRenameSubItem(self.name, newName)

    def _updateRenameSubItem(self, name: str, newName: str):
        """
        Updates the name of a sub-item in the current directory.

        Parameters:
            name (str): The name of the sub-item to be updated.
            newName (str): The new name to assign to the sub-item.

        Returns:
            None
        """
        item = self[name]
        if item == None:
            return
        elif isinstance(item, File):
            self.files.remove(item)
            self.files.append(self._newFile(self.path.add(newName)))
        elif isinstance(item, Folder):
            self.subfolder.remove(item)
            self.subfolder.append(self._newSubFolder(self.path.add(newName)))
        item.deactivate()

    def hasSubfolder(self, name: str, recursive: bool = False) -> bool:
        """
        Whether to include a subfolder
        :param name:folder name
        """
        for i in self.subfolder:
            if i.name == name:
                return True
        if recursive:
            for i in self.subfolder:
                if i.hasSubfolder(name, recursive=recursive):
                    return True
        return False

    def hasFile(self, name: str, recursive: bool = False) -> bool:
        """
        Whether to include a file
        :param name:file name
        """
        for i in self.files:
            if i.name == name:
                return True
        if recursive:
            for i in self.subfolder:
                if i.hasFile(name, recursive=recursive):
                    return True
        return False

    def search(
        self,
        condition: List[UnformattedMatching],
        aim: Literal["file", "folder", "both"] = "both",
        threaded: bool = False,
        threads: Union[None, int] = None,
    ) -> SearchResult:
        """
        Search item in the Folder
        :param condition: search conditions which is unformatted
        str: match the files whose name == condition\n
        re.Pattern[str]: match the files whose name matches the regular expression\n
        Callable[[Union["File","Folder"]],bool]: Returns a match based on the folder or file object\n
        Tuple[str | re.Pattern[str]| Callable ,int,int|None] the condition , the Minimum repetition , Maximum repetition("None" indicates that there is no limit)
        :param aim: search type
        """
        self.logger.debug(f"Searching objects in folder.{condition}")
        threadPool = ThreadPoolExecutor(max_workers=threads) if threaded else None
        waitlist: List[_base.Future] = []
        retsult: SearchResult = SearchResult()

        self._match(
            [_formatMatching(i) for i in condition],
            retsult,
            aim=aim,
            pool=threadPool,
            waitlist=waitlist,
        )
        for i in waitlist:
            while not i.done():
                time.sleep(0.1)
        return retsult

    def _match(
        self,
        condition: List[FormatedMatching],
        retsult: SearchResult,
        aim: Literal["file", "folder", "both"] = "both",
        pool: Union[ThreadPoolExecutor, None] = None,
        waitlist: List[_base.Future] = [],
    ) -> None:
        """
        This is the ultimate implementation of the search behavior, but if your criteria are not formatted, consider starting with the "search" function, which will format the criteria and complete the search for you
        :param condition: search conditions which is formatted
        :param aim: search type
        """
        for i in range(len(condition)):
            if aim != "folder":
                for j in self.files:
                    if not condition[i][0](j):
                        continue
                    restCondition = copy.deepcopy(condition[i:])
                    restCondition[0] = (
                        restCondition[0][0],
                        max(restCondition[0][1] - 1, 0),
                        None
                        if restCondition[0][2] == None
                        else max(restCondition[0][2] - 1, 0),
                    )
                    k = i
                    while k < len(restCondition):
                        if restCondition[k][1] != 0:
                            break
                        k += 1
                    if k == len(restCondition):
                        retsult.append(j)
            for j in self.subfolder:
                if not condition[i][0](j):
                    continue
                restCondition = copy.deepcopy(condition)
                restCondition[0] = (
                    restCondition[0][0],
                    max(restCondition[0][1] - 1, 0),
                    None
                    if restCondition[0][2] == None
                    else max(restCondition[0][2] - 1, 0),
                )
                if restCondition[0][2] != None and restCondition[0][2] <= 0:
                    del restCondition[0]
                if pool:
                    waitlist.append(
                        pool.submit(j._match, restCondition, retsult, aim, pool)
                    )
                else:
                    j._match(restCondition, retsult, aim, pool)
                if aim == "file":
                    continue
                k = i
                while k < len(restCondition):
                    if restCondition[k][1] != 0:
                        break
                    k += 1
                if k == len(restCondition):
                    retsult.append(j)
            if condition[i][1] > 0:
                break

    @overload
    def _create(
        self, name: str, aimType: Literal["File"], content: Union[None, bytes] = None
    ) -> File:
        ...

    @overload
    def _create(self, name: str, aimType: Literal["Folder"]) -> "Folder":
        ...

    def _create(
        self,
        name: str,
        aimType: Literal["File", "Folder"] = "File",
        content: Union[None, bytes] = None,
    ):
        """
        Create a file or folder in the specified path.

        Args:
            name (str): The name of the file or folder to create.
            aimType (Literal["File", "Folder"], optional): The type of the item to create. Defaults to "File".
            content (Union[None, bytes], optional): The content of the file to create. Defaults to None.

        Returns:
            Union[File, Folder]: The created file or folder object.
        """
        fullpath = self.path.add(name)
        if os.path.exists(fullpath):
            raise FileOrFolderAlreadyExists(
                "We can't create a file for that folder because it already exists"
            )
        if aimType == "File":
            with open(fullpath, "wb") as f:
                if content:
                    f.write(content)
            aim = self._newFile(fullpath)
            self.files.append(aim)
            return aim
        else:
            os.mkdir(fullpath)
            aim = self._newSubFolder(fullpath)
            self.subfolder.append(aim)
            return aim

    @overload
    def _deepCreate(
        self,
        paths: List[str],
        aimType: Literal["File"],
        content: Union[None, bytes] = None,
    ) -> File:
        ...

    @overload
    def _deepCreate(self, paths: List[str], aimType: Literal["Folder"]) -> "Folder":
        ...

    def _deepCreate(
        self,
        paths: List[str],
        aimType: Literal["File", "Folder"] = "File",
        content: Union[None, bytes] = None,
    ):
        """
        Recursively creates a file or folder at the specified path.

        Parameters:
            paths (List[str]): A list of paths representing the hierarchy of folders and/or files to be created.
            aimType (Literal["File", "Folder"], optional): The type of the element to be created. Defaults to "File".
            content (Union[None, bytes], optional): The content of the file to be created. Defaults to None.

        Returns:
            The created file or folder object.

        Raises:
            UnknownError: If the list of paths is empty.
            FileOrFolderAlreadyExists: If the file already exists in the specified location.

        """
        if len(paths) <= 0:
            raise UnknownError()
        if len(paths) == 1:
            if aimType == "File":
                return self._create(paths[0], aimType, content)
            else:
                return self._create(paths[0], aimType)
        else:
            nextFolder = self[paths[0]]
            if isinstance(nextFolder, File):
                raise FileOrFolderAlreadyExists(
                    f"The file {paths[0]} already exists in {self.path}, so we cannot create folder there"
                )
            if nextFolder == None:
                nextFolder = self._create(paths[0], "Folder")
            if aimType == "File":
                return nextFolder._deepCreate(paths[1:], aimType, content)
            else:
                return nextFolder._deepCreate(paths[1:], aimType)

    def createFile(self, path: Union[str, Path], content: bytes = b"") -> File:
        """
        Creates a file at the specified path with the given content.

        Args:
            path (Union[str, Path]): The path of the file to be created.
            content (bytes, optional): The content to be written to the file. Defaults to b"".

        Returns:
            File: The created file object.
        """
    
        path = self.path.getAbsolutePath(path)
        paths = path.findRest(self.path)
        return self._deepCreate(paths, "File", content)

    def createFolder(self, path: Union[str, Path]) -> "Folder":
        """
        Create a folder at the specified path.

        Args:
            path (Union[str, Path]): The path where the folder should be created.

        Returns:
            Folder: The created folder.

        """
        
        path = self.path.getAbsolutePath(path)
        paths = path.findRest(self.path)
        return self._deepCreate(paths, "Folder")

    def add(self, aim: Union["File", "Folder"], move: bool = False):
        "add a file or folder to this folder"
        if move:
            aim.move(self.path)
        else:
            aim.copy(self.path)

    def _normalizedToDictIncludeFiles(
        self,
        includeFiles: Union[
            Literal["info", "base64", "bytes", "keep"], Callable[[File], Any]
        ],
    ) -> Callable[[File], Any]:
        if callable(includeFiles):
            return includeFiles
        ma: Dict[str, Callable[[File], Any]] = {
            "base64": lambda x: {
                "name": x.name,
                "base64": base64.b64encode(x.content).decode(),
            },
            "info": lambda x: {
                "name": x.name,
                "size": x.size,
                "dev": x.dev,
                "uid": x.uid,
                "gid": x.gid,
                "ctime": x.ctime,
                "atime": x.atime,
                "mtime": x.mtime,
                "ino": x.ino,
                "mode": x.mode,
            },
            "bytes": lambda x: {"name": x.name, "bytes": x.content},
            "keep": lambda x: x,
        }
        if includeFiles in ma:
            return ma[includeFiles]
        raise ValueError(f"Invalid value for includeFiles: {includeFiles}")

    def toDict(
        self,
        includeFiles: Union[
            Literal["ignore", "info", "base64", "bytes", "keep"], Callable[[File], Any]
        ] = "keep",
    ) -> Dict[str, Any]:
        """
        Converts the current folder object to a dictionary representation.

        Args:
            includeFiles (Union[Literal["ignore", "info", "base64", "bytes", "keep"], Callable[[File], Any]], optional):
                Determines how the files should be included in the dictionary representation.
                Defaults to "keep", which includes all file information.
            
        Returns:
            Dict[str, Any]:
                A dictionary representation of the current folder object.
        """
        result = {}
        result["type"] = "Folder"
        result["name"] = self.name
        if includeFiles != "ignore":
            includeFiles = self._normalizedToDictIncludeFiles(includeFiles)
            result["files"] = [includeFiles(i) for i in self.files]
        result["subfolder"] = {i.name: i.toDict(includeFiles) for i in self.subfolder}
        return result

    def toJson(self, **kw) -> str:
        """
        Convert the object to a JSON string.

        :param kw: Additional keyword arguments to pass to json.dumps().
        :return: A JSON string representation of the object.
        :rtype: str
        """
        return json.dumps(self.toDict("base64"), **kw)
