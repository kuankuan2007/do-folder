# pyint: ignore
from tempfile import gettempdir
import random
import shutil
from pathlib import Path
import hashlib
import sys
from concurrent import futures

if "--no-install" in sys.argv:
    pkgDir = Path(__file__).parent.parent

    print(f"\nUse Directory from local: {pkgDir}")

    sys.path.insert(0, (str(pkgDir / "src")))

import doFolder
import doFolder.hashing


root: Path


def calcHash(content: bytes, algorithm: str = "sha256"):
    obj = hashlib.new(algorithm)
    obj.update(content)
    return obj.hexdigest()


def randomString(l=10):
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=l))


def randomFileContent(l=500):
    return "random content:" + randomString(l)


def setup_module(module):
    global root
    while True:
        root = Path(gettempdir()) / f"pytest-doFolder-{randomString(5)}"
        if not root.exists():
            break
    root.mkdir(parents=True, exist_ok=True)

    print(f"\nRoot directory: {root}")


def teardown_module(module):
    if "--keep-temp" in sys.argv:
        print(f"\nKeeping temporary directory at {root}")
    else:
        shutil.rmtree(root)


class TestFileSystem:
    """
    Tests related to file system functionality, including creating, operating, copying,
    moving, and deleting files and folders. Extended descriptions to clarify error messages.
    """

    def test_path(self):
        """
        Verifies doFolder.Path maps directly to pathlib.Path.
        If failure occurs, it likely indicates an incorrect or missing import
        within doFolder that doesn't properly map Path to pathlib.Path.
        """
        assert doFolder.Path == Path, (
            "Expected doFolder.Path to be the same as pathlib.Path, but they are different. "
            "Possible cause: mismatch or improper import of Path in doFolder."
        )

    def test_create_file(self):
        """
        Ensures file creation and content writing works as expected.
        If this fails, an issue with file path initialization or writing logic might be the cause.
        """
        path = root / "test_create"
        path.touch()
        inner = randomFileContent()
        path.write_text(inner, encoding="utf8")

        t1 = doFolder.createItem(path)
        assert not doFolder.isDir(
            t1
        ), f"Expected {path} to be a file, but it is not. Check the implementation of doFolder.isDir."
        assert (
            t1.exists()
        ), f"Expected file {path} to exist, but it does not. Ensure the file creation logic is correct."
        assert (
            t1.isFile()
        ), f"Expected {path} to be a file, but it is not. Verify the isFile method."
        assert t1.content == inner.encode(
            "utf8"
        ), f"Expected content of {path} to be '{inner}', but got '{t1.content.decode('utf8')}'. Check the file writing or content retrieval logic."

    def test_file_operation(self):
        """
        Verifies file copying, moving, and deletion.
        Failures in copy/move/delete often stem from incorrect path handling or file locks.
        """
        path = root / "test_file_operation"
        path.touch()
        inner = randomFileContent()
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
        Ensures folder creation and checks that newly created files/folders have correct attributes.
        Failure may occur if directory creation or content checks are improperly handled.
        """
        path = root / "test_create_folder"
        path.mkdir()
        inner = randomFileContent()

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
        Checks copying, moving, and deleting of folders.
        Potential failures often relate to incomplete directory copy or locked files/directories.
        """
        path = root / "test_folder_operation"
        path.mkdir()
        inner = randomFileContent()

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
        Tests various folder-related methods such as existence checks and creating structures.
        On failure, confirm that folder creation logic and item checks are aligned with doFolder settings.
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

    def test_recursive_traversal(self):

        path = root / "test_recursive_traversal"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        d.createFile("test1").content = randomFileContent().encode("utf8")
        d.createFile("test2").content = randomFileContent().encode("utf8")
        t3 = d.createDir("test3")
        t3.createFile("test4").content = randomFileContent().encode("utf8")
        t3.createFile("test5").content = randomFileContent().encode("utf8")
        t6 = t3.createDir("test6")
        t6.createFile("test7").content = randomFileContent().encode("utf8")
        t6.createFile("test8").content = randomFileContent().encode("utf8")
        t9 = t3.createDir("test9")
        t9.createFile("test10").content = randomFileContent().encode("utf8")
        t9.createFile("test11").content = randomFileContent().encode("utf8")
        t12 = t9.createDir("test12")
        t12.createFile("test13").content = randomFileContent().encode("utf8")
        t12.createFile("test14").content = randomFileContent().encode("utf8")

        res1 = tuple(i.path for i in d.recursiveTraversal())
        exceptRes1 = [
            d["test1"],
            d["test2"],
            t3["test4"],
            t3["test5"],
            t6["test7"],
            t6["test8"],
            t9["test10"],
            t9["test11"],
            t12["test13"],
            t12["test14"],
        ]

        assert len(res1) == len(
            exceptRes1
        ), "Expected the number of items in the result to match the number of expected items, but they do not."
        for i in exceptRes1:
            assert (
                i.path in res1
            ), f"Expected item {i} to be in the result, but it is not."

        res2 = tuple(i.path for i in d.recursiveTraversal(hideDirectory=False))
        exceptRes2 = [
            d["test1"],
            d["test2"],
            t3["test4"],
            t3["test5"],
            t6["test7"],
            t6["test8"],
            t9["test10"],
            t9["test11"],
            t12["test13"],
            t12["test14"],
            t3,
            t6,
            t9,
            t12,
            d,
        ]
        assert len(res2) == len(
            exceptRes2
        ), "Expected the number of items in the result to match the number of expected items, but they do not."
        for i in exceptRes2:
            assert (
                i.path in res2
            ), f"Expected item {i} to be in the result, but it is not."


class TestCompareSystem:
    """
    Tests comparison utility for files and folders, focusing on content, size, timetag, and ignore modes.
    Extended documentation to clarify each assertion's purpose.
    """

    def test_compare_file(self):
        """
        Compares file content, size, and timetag to ensure correctness.
        If these checks fail, verify the compare mode logic or confirm that file content is written properly.
        """
        path = root / "test_compare_file"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        content = randomFileContent(1024 * 1024)
        d.createFile("test1").content = content.encode("utf8")
        d.createFile("test2").content = content.encode("utf8")

        assert doFolder.compare.compare(
            d["test1"], d["test2"], doFolder.compare.CompareMode.CONTENT
        ), "Expected files 'test1' and 'test2' to be equal, but they are not."

        d["test2"].content = "modified content".encode("utf8")

        assert not doFolder.compare.compare(
            d["test1"], d["test2"], doFolder.compare.CompareMode.CONTENT
        ), "Expected files 'test1' and 'test2' to be not equal, but they are."

        d["test2"].content = randomFileContent(1024 * 1024).encode("utf8")

        assert doFolder.compare.compare(
            d["test1"], d["test2"], doFolder.compare.CompareMode.SIZE
        ), "Expected files 'test1' and 'test2' to have same size, but they are not."

        assert doFolder.compare.compare(
            d["test1"], d["test2"], doFolder.compare.CompareMode.IGNORE
        ), "Expected the compare method to ignore the compare mode, but it did not."

        d["test1"].copy(d.path / "test3")

        assert doFolder.compare.compare(
            d["test1"], d["test3"], doFolder.compare.CompareMode.TIMETAG
        ), "Expected files 'test1' and 'test3' to be equal, but they are not."

        d["test3"].content = "modified content".encode("utf8")

        assert not doFolder.compare.compare(
            d["test1"], d["test3"], doFolder.compare.CompareMode.TIMETAG
        ), "Expected files 'test1' and 'test3' to be not equal, but they are."

        assert not doFolder.compare.compare(
            d["test1"],
            d.get("test4", unExistsMode=doFolder.UnExistsMode.IGNORE),
            doFolder.compare.CompareMode.IGNORE,
        ), "Expected file 'test4' to not exist, but it does."

    def test_compare_folder(self):
        """
        Compares folder structures by content, size, or ignoring details.
        Failures generally point to partial copy, differences in subdirectories, or file content mismatches.
        """
        path = root / "test_compare_dir"

        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)
        t1 = d.createDir("test1")
        t1.createFile("test2").content = randomFileContent(1024 * 1024).encode("utf8")
        t1.createFile("test3").content = randomFileContent(1024 * 1024).encode("utf8")
        t4 = t1.createDir("test4")
        t4.createFile("test5").content = randomFileContent(1024 * 1024).encode("utf8")
        t4.createFile("test6").content = randomFileContent(1024 * 1024).encode("utf8")
        t7 = t4.createDir("test7")
        t7.createFile("test8").content = randomFileContent(1024 * 1024).encode("utf8")
        t7.createFile("test9").content = randomFileContent(1024 * 1024).encode("utf8")
        t10 = t4.createDir("test10")
        t10.createFile("test11").content = randomFileContent(1024 * 1024).encode("utf8")
        t10.createFile("test12").content = randomFileContent(1024 * 1024).encode("utf8")
        t11 = t4.createDir("test11")
        t11.createFile("test13").content = randomFileContent(1024 * 1024).encode("utf8")

        t1.copy(d.path / "test1_copy")

        assert doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
        ), "Expected folders 'test1' and 'test1_copy' to match in content, but they differ. Possible cause: incorrect or incomplete copy."

        t11["test13"].content = randomFileContent(1024 * 1024).encode("utf8")
        assert not doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
        ), "Expected 'test1' and 'test1_copy' to differ in content, but they match. Possible cause: file wasn't updated or compare mode is incorrect."

        assert doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.SIZE
        ), "Expected 'test1' and 'test1_copy' to be equal in size, but they differ. Verify file size logic or if data was modified."

        t7["test9"].content = randomFileContent(1024 * 5).encode("utf8")

        assert not doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.SIZE
        ), "Expected a size mismatch between 'test1' and 'test1_copy', but they appear identical. Possible cause: the file changes did not apply."

        assert doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.IGNORE
        ), "Expected 'test1' and 'test1_copy' to be considered equal when ignoring differences, but they are not. Check compare mode or path references."

        t4["test5"].delete()
        assert not doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
        ), "Expected 'test1' and 'test1_copy' to differ post-deletion, but they are equal. Possible cause: the file deletion or compare logic may be incorrect."

    def test_get_difference(self):
        """
        Evaluates differences between two folders for given compare modes.
        If this fails, investigate file modifications, missing items, or size changes within the compared directories.
        """
        path = root / "test_get_difference"

        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        t1 = d.createDir("test1")
        t1.createFile("test2").content = randomFileContent(1024 * 1024).encode("utf8")
        t1.createFile("test3").content = randomFileContent(1024 * 1024).encode("utf8")
        t4 = t1.createDir("test4")
        t4.createFile("test5").content = randomFileContent(1024 * 1024).encode("utf8")
        t6 = t4.createDir("test6")
        t6.createFile("test7").content = randomFileContent(1024 * 1024).encode("utf8")
        t8 = t4.createDir("test8")
        t8.createFile("test9").content = randomFileContent(1024 * 1024).encode("utf8")
        t10 = t4.createDir("test10")
        t10.createFile("test11").content = randomFileContent(1024 * 1024).encode("utf8")
        t10.createFile("test12").content = randomFileContent(1024 * 1024).encode("utf8")

        t1.copy(d.path / "test1_copy")

        assert (
            doFolder.compare.getDifference(
                d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
            )
            is None
        ), "Expected folders 'test1' and 'test1_copy' to be equal, but they are not."

        t10["test12"].content = randomFileContent(1024 * 1024).encode("utf8")
        diff0 = doFolder.compare.getDifference(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
        )
        assert (
            diff0 is not None
        ), "Expected folders 'test1' and 'test1_copy' to be not equal, but they are."
        diff1 = diff0.sub[0].sub[0].sub[0]
        assert (
            diff1.path1 == d.path / "test1/test4/test10/test12"
            and diff1.path2 == d.path / "test1_copy/test4/test10/test12"
            and diff1.diffType == doFolder.compare.DifferenceType.FILE_DIFFERENCE
        ), f"The compare result is not correct, expected the path to be 'test1/test4/test10/test12' and 'test1_copy/test4/test10/test12', but got {diff1.path1} and {diff1.path2}."
        assert (
            len(diff0.toFlat()) == 4
        ), f"Expected the length of the flat list to be 4, but got {len(diff1.toFlat())}."
        assert (
            doFolder.compare.getDifference(
                d["test1"], d["test1_copy"], doFolder.compare.CompareMode.SIZE
            )
            is None
        ), "Expected folders 'test1' and 'test1_copy' to be equal in size, but they are not."
        t8["test9"].content = randomFileContent(1024 * 5).encode("utf8")

        assert (
            doFolder.compare.getDifference(
                d["test1"], d["test1_copy"], doFolder.compare.CompareMode.SIZE
            )
            .sub[0]
            .sub[0]
            .sub[0]
            .diffType
            == doFolder.compare.DifferenceType.FILE_DIFFERENCE
        ), "Expected folders 'test1' and 'test1_copy' to be not equal in size, but they are."

        assert (
            doFolder.compare.getDifference(
                d["test1"], d["test1_copy"], doFolder.compare.CompareMode.IGNORE
            )
            is None
        ), "Expected folders 'test1' and 'test1_copy' to be equal, but they are not."

        t6["test7"].delete()

        assert (
            doFolder.compare.getDifference(
                d["test1"], d["test1_copy"], doFolder.compare.CompareMode.IGNORE
            )
            .toFlat()[-1]
            .diffType
            == doFolder.compare.DifferenceType.NOT_EXISTS
        ), "Expected folders 'test1' and 'test1_copy' to be not equal, but they are."

    def test_hash(self):
        path = root / "test_hash"

        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        f1 = d.createFile("test1")
        content1 = randomFileContent(1024).encode("utf-8")
        f1.content = content1
        assert f1.hash() == calcHash(content1), "wrong answer for sha256"

        f2 = d.createFile("test2")
        content2 = randomFileContent(1024 * 1024 * 5).encode("utf-8")
        f2.content = content2

        assert f2.hash() == calcHash(content2), "wrong answer for sha256"

        assert f2.hash("md5") == calcHash(content2, "md5"), "wrong answer for md5"

    def test_hash_calculator(self):
        path = root / "test_hash_calculator"

        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        f1 = d.createFile("test1")
        f1.content = randomFileContent(1024 * 1024 * 5).encode("utf-8")
        obj1 = doFolder.hashing.FileHashCalculator()

        assert obj1.findCache(f1) is None

        res1 = obj1.get(f1)

        assert obj1.findCache(f1) == res1

        f1.content = randomFileContent(1024 * 1024 * 5).encode("utf-8")

        res2 = obj1.get(f1)
        assert res2 != res1

        obj1.reCalcHashMode = doFolder.hashing.ReCalcHashMode.NEVER

        f1.content = randomFileContent(1024 * 1024 * 5).encode("utf-8")

        assert obj1.get(f1) == res2

        obj1.reCalcHashMode = doFolder.hashing.ReCalcHashMode.ALWAYS

        res3 = obj1.get(f1)
        res4 = obj1.get(f1)

        assert res3.calcTime != res4.calcTime and res3.hash == res4.hash

    def test_threaded_hash_calculator(self):

        path = root / "test_threaded_hash_calculator"

        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        files: list[doFolder.File] = []

        for i in range(20):
            files.append(d.createFile(f"test{i}"))
            files[-1].content = randomFileContent(
                1024 * 1024 * random.randint(1, 8)
            ).encode("utf-8")

        obj1 = doFolder.hashing.ThreadedFileHashCalculator()

        res = [obj1.threadedGet(i) for i in files]

        futures.wait(res, timeout=60 * 10)

        for i in res:
            assert type(i.result()) == doFolder.hashing.FileHashResult
