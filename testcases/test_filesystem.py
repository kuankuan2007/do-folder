# pyint: ignore
from tempfile import TemporaryDirectory
import random
import pytest
from pathlib import Path

import sys


if "--no-install" in sys.argv:
    pkgDir = Path(__file__).parent.parent

    print("Use Directory from local: {0}".format(pkgDir))
    sys.path.insert(0, (str(pkgDir)))
    from src import doFolder
    from src.doFolder import exception as _ex
else:
    print("Global module is used")
    import doFolder
    from doFolder import exception as _ex


root: Path
TEMP_DIR: TemporaryDirectory


def _randomLine():
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))


def getRandomString():
    return "random content:" + "-".join([_randomLine() for _ in range(10)])


def setup_module(module):
    global TEMP_DIR, root
    TEMP_DIR = TemporaryDirectory(prefix="pytest-doFolder-")
    root = Path(TEMP_DIR.name)


def teardown_module(module):
    TEMP_DIR.cleanup()


class TestFileSystem:
    """
    Tests related to file system functionality, including creating, operating, copying, moving, and deleting files and folders.
    """

    def test_path(self):
        """
        Test whether doFolder.Path is the same as pathlib.Path.
        """
        assert (
            doFolder.Path == Path
        ), "Expected doFolder.Path to be the same as pathlib.Path, but they are different. This may indicate an incorrect implementation or import issue."

    def test_create_file(self):
        """
        Test file creation, writing content, and verifying related attributes.
        """
        path = root / "test_create"
        path.touch()
        inner = getRandomString()
        path.write_text(inner, encoding="utf8")

        t1 = doFolder.createItem(path)
        assert not doFolder.isDir(t1), f"Expected {path} to be a file, but it is not. Check the implementation of doFolder.isDir."
        assert t1.exists(), f"Expected file {path} to exist, but it does not. Ensure the file creation logic is correct."
        assert t1.isFile(), f"Expected {path} to be a file, but it is not. Verify the isFile method."
        assert t1.content == inner.encode(
            "utf8"
        ), f"Expected content of {path} to be '{inner}', but got '{t1.content.decode('utf8')}'. Check the file writing or content retrieval logic."

    def test_file_operation(self):
        """
        Test file copy, move, and delete operations.
        """
        path = root / "test_file_operation"
        path.touch()
        inner = getRandomString()
        path.write_text(inner, encoding="utf8")

        t1 = doFolder.createItem(path)
        assert t1.exists(), f"Expected file {path} to exist, but it does not."

        copyPath = root / "test_file_operation_copy"
        movePath = root / "test_file_operation_move"

        t1.copy(copyPath)
        assert (
            copyPath.exists()
        ), f"Expected file to be copied to {copyPath}, but it does not exist. Verify the copy method implementation."
        assert (
            copyPath.read_text(encoding="utf8") == inner
        ), f"Expected content of {copyPath} to be '{inner}', but got '{copyPath.read_text(encoding='utf8')}'."

        t1.move(movePath)
        assert (
            not path.exists()
        ), f"Expected file {path} to be moved to {movePath}, but it still exists. Check the move method."
        assert (
            movePath.exists()
        ), f"Expected file to be moved to {movePath}, but it does not exist."
        assert (
            movePath.read_text(encoding="utf8") == inner
        ), f"Expected content of {movePath} to be '{inner}', but got '{movePath.read_text(encoding='utf8')}'."

        t1.delete()
        assert (
            not movePath.exists()
        ), f"Expected file {movePath} to be deleted, but it still exists. Ensure the delete method works as expected."

    def test_create_folder(self):
        """
        Test folder creation, content operations, and attribute verification.
        """
        path = root / "test_create_folder"
        path.mkdir()
        inner = getRandomString()

        d = doFolder.Directory(path)
        assert d.exists(), f"Expected folder {path} to exist, but it does not."
        assert not d.isFile(), f"Expected {path} to be a folder, but it is a file."

        c1 = tuple(d.__iter__())
        assert (
            len(c1) == 0
        ), f"Expected folder {path} to be empty, but it contains {len(c1)} items. Check the folder initialization logic."

        d.createFile("test1").content = inner.encode("utf8")
        d.createDir("test2")

        for i in d:
            if isinstance(i, doFolder.Directory):
                assert (
                    i.name == "test2"
                ), f"Expected folder 'test2' to be created in {path}, but found {i.name}. Verify the createDir method."
            else:
                assert i.name == "test1" and i.content == inner.encode(
                    "utf8"
                ), f"Expected file 'test1' with content '{inner}' in {path}, but found {i.name} with content '{i.content.decode('utf8')}'. Check the createFile method."

    def test_folder_operation(self):
        """
        Test folder copy, move, and delete operations.
        """
        path = root / "test_folder_operation"
        path.mkdir()
        inner = getRandomString()

        d = doFolder.Directory(path)
        d.createFile("test1").content = inner.encode("utf8")

        assert d.exists(), f"Expected folder {path} to exist, but it does not."

        copyPath = root / "test_folder_operation_copy"
        movePath = root / "test_folder_operation_move"

        d.copy(copyPath)
        assert (
            copyPath.exists()
        ), f"Expected folder to be copied to {copyPath}, but it does not exist. Verify the copy method for directories."
        assert (copyPath / "test1").read_text(
            encoding="utf8"
        ) == inner, f"Expected content of {copyPath / 'test1'} to be '{inner}', but got '{(copyPath / 'test1').read_text(encoding='utf8')}'."

        d.move(movePath)
        assert (
            not path.exists()
        ), f"Expected folder {path} to be moved to {movePath}, but it still exists. Check the move method for directories."
        assert (
            movePath.exists()
        ), f"Expected folder to be moved to {movePath}, but it does not exist."
        assert (movePath / "test1").read_text(
            encoding="utf8"
        ) == inner, f"Expected content of {movePath / 'test1'} to be '{inner}', but got '{(movePath / 'test1').read_text(encoding='utf8')}'."

        d.delete()
        assert (
            not movePath.exists()
        ), f"Expected folder {movePath} to be deleted, but it still exists. Ensure the delete method for directories works as expected."

    def test_folder_method(self):
        """
        Test various folder methods, including existence checks and creating files and folders.
        """
        path = root / "test_folder_method"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        assert (
            path.exists()
        ), f"Expected folder {path} to be created, but it does not exist. Verify the unExistsMode.CREATE functionality."

        (path / "test1").touch()
        (path / "test2/test3").mkdir(parents=True)
        (path / "test2/test4").touch()

        assert d.has(
            "test1"
        ), f"Expected file 'test1' to exist in {path}, but it does not. Check the has method."
        assert d.has(
            "test1", allowedTargetType=doFolder.ItemType.FILE
        ), f"Expected 'test1' in {path} to be a file, but it is not."
        assert not d.has(
            "test1", allowedTargetType=doFolder.ItemType.DIR
        ), f"Expected 'test1' in {path} to not be a directory, but it is."

        assert d.has(
            "test2"
        ), f"Expected folder 'test2' to exist in {path}, but it does not."
        assert d.has(
            "test2", allowedTargetType=doFolder.ItemType.DIR
        ), f"Expected 'test2' in {path} to be a directory, but it is not."
        assert not d.has(
            "test2", allowedTargetType=doFolder.ItemType.FILE
        ), f"Expected 'test2' in {path} to not be a file, but it is."

        assert d.has(
            "test2/test3"
        ), f"Expected folder 'test2/test3' to exist in {path}, but it does not."
        assert d.has(
            "test2/test3", allowedTargetType=doFolder.ItemType.DIR
        ), f"Expected 'test2/test3' in {path} to be a directory, but it is not."
        assert d.has(
            ["test2", "test3"]
        ), f"Expected folder path ['test2', 'test3'] to exist in {path}, but it does not."
        assert d.has(
            Path("test2/test3")
        ), f"Expected folder path 'test2/test3' to exist in {path}, but it does not."
        assert d.has(
            d.path / "test2/test3"
        ), f"Expected folder path 'test2/test3' to exist in {path}, but it does not."

        d.createDir("test5/test6")
        assert (
            path / "test5/test6"
        ).is_dir(), f"Expected directory 'test5/test6' to be created in {path}, but it does not exist. Verify the createDir method."

        d.createFile("test7/test8")
        assert (
            path / "test7/test8"
        ).is_file(), f"Expected file 'test7/test8' to be created in {path}, but it does not exist. Check the createFile method."
