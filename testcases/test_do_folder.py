# pyint: ignore
from tempfile import gettempdir
import random
import shutil
from pathlib import Path
import hashlib
import sys
from concurrent import futures
import time

# Check if the script is run with the --no-install flag
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
        """Test doFolder.Path is properly mapped to pathlib.Path"""
        assert doFolder.Path == Path, (
            f"doFolder.Path should reference pathlib.Path, but got {type(doFolder.Path)} instead. "
            f"This indicates an import issue in the doFolder module."
        )

    def test_create_file(self):
        """Test basic file creation and content operations"""
        path = root / "test_create"
        path.touch()
        inner = randomFileContent()
        path.write_text(inner, encoding="utf8")

        t1 = doFolder.createItem(path)
        assert not doFolder.isDir(
            t1
        ), f"File creation failed: {path} was expected to be a file but doFolder.isDir() returned True. Check doFolder.isDir() implementation."
        assert (
            t1.exists()
        ), f"File existence check failed: created file {path} does not exist according to doFolder. Verify file creation or exists() method."
        assert (
            t1.isFile()
        ), f"File type check failed: {path} should be identified as a file but isFile() returned False. Check isFile() method implementation."
        assert t1.content == inner.encode(
            "utf8"
        ), f"File content mismatch: expected '{inner[:50]}...', got '{t1.content.decode('utf8')[:50]}...'. Check content reading/writing logic."

    def test_file_operation(self):
        """Test file copy, move and delete operations"""
        path = root / "test_file_operation"
        path.touch()
        inner = randomFileContent()
        path.write_text(inner, encoding="utf8")

        t1 = doFolder.createItem(path)
        assert (
            t1.exists()
        ), f"File setup failed: source file {path} should exist but doesn't. Check test setup."

        copyPath = root / "test_file_operation_copy"
        movePath = root / "test_file_operation_move"

        # Test copy operation
        t1.copy(copyPath)
        assert (
            copyPath.exists()
        ), f"File copy failed: destination file {copyPath} does not exist after copy operation. Check copy() method implementation."
        assert (
            copyPath.read_text(encoding="utf8") == inner
        ), f"File copy content mismatch: copied file content doesn't match original. Expected '{inner[:50]}...', got '{copyPath.read_text(encoding='utf8')[:50]}...'."

        # Test move operation
        t1.move(movePath)
        assert (
            not path.exists()
        ), f"File move failed: source file {path} still exists after move operation. Move should remove the original file."
        assert (
            movePath.exists()
        ), f"File move failed: destination file {movePath} doesn't exist after move operation. Check move() method implementation."
        assert (
            movePath.read_text(encoding="utf8") == inner
        ), f"File move content mismatch: moved file content doesn't match original. Expected '{inner[:50]}...', got '{movePath.read_text(encoding='utf8')[:50]}...'."

        # Test delete operation
        t1.delete()
        assert (
            not movePath.exists()
        ), f"File delete failed: file {movePath} still exists after delete operation. Check delete() method implementation."

    def test_create_folder(self):
        """Test directory creation and basic directory operations"""
        path = root / "test_create_folder"
        path.mkdir()
        inner = randomFileContent()

        d = doFolder.Directory(path)
        assert (
            d.exists()
        ), f"Directory creation failed: directory {path} should exist but doesn't. Check Directory() constructor."
        assert (
            not d.isFile()
        ), f"Directory type check failed: {path} should be a directory but isFile() returned True. Check isFile() method."

        c1 = tuple(d.__iter__())
        assert (
            len(c1) == 0
        ), f"Empty directory check failed: directory {path} should be empty but contains {len(c1)} items: {[i.name for i in c1]}."

        # Test creating files and directories within the directory
        d.createFile("test1").content = inner.encode("utf8")
        d.createDir("test2")

        found_items = []
        for i in d:
            found_items.append(i)
            if isinstance(i, doFolder.Directory):
                assert (
                    i.name == "test2"
                ), f"Directory creation failed: expected directory named 'test2', but found '{i.name}'. Check createDir() method."
            else:
                assert i.name == "test1" and i.content == inner.encode(
                    "utf8"
                ), f"File creation failed: expected file 'test1' with specific content, but found '{i.name}' with different content. Check createFile() method and content assignment."

        assert (
            len(found_items) == 2
        ), f"Expected 2 items (1 file, 1 directory) but found {len(found_items)}. Check createFile() and createDir() methods."

    def test_folder_operation(self):
        """Test directory copy, move and delete operations"""
        path = root / "test_folder_operation"
        path.mkdir()
        inner = randomFileContent()

        d = doFolder.Directory(path)
        d.createFile("test1").content = inner.encode("utf8")

        assert (
            d.exists()
        ), f"Directory setup failed: source directory {path} should exist but doesn't. Check test setup."

        copyPath = root / "test_folder_operation_copy"
        movePath = root / "test_folder_operation_move"

        # Test copy operation
        d.copy(copyPath)
        assert (
            copyPath.exists()
        ), f"Directory copy failed: destination directory {copyPath} does not exist after copy operation. Check copy() method implementation."
        assert (copyPath / "test1").read_text(
            encoding="utf8"
        ) == inner, f"Directory copy content failed: file content in copied directory doesn't match original. Expected '{inner[:50]}...', got '{(copyPath / 'test1').read_text(encoding='utf8')[:50]}...'."

        # Test move operation
        d.move(movePath)
        assert (
            not path.exists()
        ), f"Directory move failed: source directory {path} still exists after move operation. Move should remove the original directory."
        assert (
            movePath.exists()
        ), f"Directory move failed: destination directory {movePath} doesn't exist after move operation. Check move() method implementation."
        assert (movePath / "test1").read_text(
            encoding="utf8"
        ) == inner, f"Directory move content failed: file content in moved directory doesn't match original. Expected '{inner[:50]}...', got '{(movePath / 'test1').read_text(encoding='utf8')[:50]}...'."

        # Test delete operation
        d.delete()
        assert (
            not movePath.exists()
        ), f"Directory delete failed: directory {movePath} still exists after delete operation. Check delete() method implementation."

    def test_folder_method(self):
        """Test directory utility methods like has() and path creation"""
        path = root / "test_folder_method"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        assert (
            path.exists()
        ), f"Auto-creation failed: directory {path} should be created automatically with unExistsMode.CREATE but doesn't exist. Check unExistsMode.CREATE functionality."

        # Create test structure
        (path / "test1").touch()
        (path / "test2/test3").mkdir(parents=True)
        (path / "test2/test4").touch()

        # Test has() method with files
        assert d.has(
            "test1"
        ), f"File detection failed: has('test1') returned False but file exists in {path}. Check has() method implementation."
        assert d.has(
            "test1", allowedTargetType=doFolder.ItemType.FILE
        ), f"File type filtering failed: has('test1', FILE) should return True but didn't. Check allowedTargetType filtering in has() method."
        assert not d.has(
            "test1", allowedTargetType=doFolder.ItemType.DIR
        ), f"File type filtering failed: has('test1', DIR) should return False for a file but returned True. Check allowedTargetType filtering."

        # Test has() method with directories
        assert d.has(
            "test2"
        ), f"Directory detection failed: has('test2') returned False but directory exists in {path}. Check has() method implementation."
        assert d.has(
            "test2", allowedTargetType=doFolder.ItemType.DIR
        ), f"Directory type filtering failed: has('test2', DIR) should return True but didn't. Check allowedTargetType filtering in has() method."
        assert not d.has(
            "test2", allowedTargetType=doFolder.ItemType.FILE
        ), f"Directory type filtering failed: has('test2', FILE) should return False for a directory but returned True. Check allowedTargetType filtering."

        # Test has() method with nested paths
        assert d.has(
            "test2/test3"
        ), f"Nested path detection failed: has('test2/test3') should find nested directory but didn't. Check nested path handling in has() method."
        assert d.has(
            "test2/test3", allowedTargetType=doFolder.ItemType.DIR
        ), f"Nested directory type filtering failed: has('test2/test3', DIR) should return True but didn't. Check nested path type filtering."
        assert d.has(
            ["test2", "test3"]
        ), f"Path list detection failed: has(['test2', 'test3']) should find nested directory but didn't. Check list path handling in has() method."
        assert d.has(
            Path("test2/test3")
        ), f"Path object detection failed: has(Path('test2/test3')) should find nested directory but didn't. Check Path object handling in has() method."
        assert d.has(
            d.path / "test2/test3"
        ), f"Absolute path detection failed: has(absolute_path) should find nested directory but didn't. Check absolute path handling in has() method."

        # Test nested directory creation
        d.createDir("test5/test6")
        assert (
            path / "test5/test6"
        ).is_dir(), f"Nested directory creation failed: createDir('test5/test6') should create nested directory structure but didn't. Check createDir() method."

        # Test nested file creation
        d.createFile("test7/test8")
        assert (
            path / "test7/test8"
        ).is_file(), f"Nested file creation failed: createFile('test7/test8') should create file with parent directories but didn't. Check createFile() method."

    def test_recursive_traversal(self):
        """Test recursive directory traversal functionality"""
        path = root / "test_recursive_traversal"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        # Create nested structure
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

        # Test recursive traversal (files only, default behavior)
        res1 = tuple(i.path for i in d.recursiveTraversal())
        expected_files = [
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

        assert len(res1) == len(expected_files), (
            f"Recursive traversal count mismatch: expected {len(expected_files)} files, "
            f"but got {len(res1)}. Check recursiveTraversal() implementation."
        )

        for expected_item in expected_files:
            assert expected_item.path in res1, (
                f"Recursive traversal missing item: {expected_item.path} not found in traversal results. "
                f"Check if recursiveTraversal() properly visits all nested files."
            )

        # Test recursive traversal including directories
        res2 = tuple(i.path for i in d.recursiveTraversal(hideDirectory=False))
        expected_all_items = [
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

        assert len(res2) == len(expected_all_items), (
            f"Recursive traversal with directories count mismatch: expected {len(expected_all_items)} items, "
            f"but got {len(res2)}. Check recursiveTraversal(hideDirectory=False) implementation."
        )

        for expected_item in expected_all_items:
            assert expected_item.path in res2, (
                f"Recursive traversal with directories missing item: {expected_item.path} not found in results. "
                f"Check if recursiveTraversal(hideDirectory=False) properly includes all files and directories."
            )

    def test_hash(self):
        """Test basic file hashing functionality with different algorithms"""
        path = root / "test_hash"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        # Test small file SHA256 hash
        f1 = d.createFile("test1")
        content1 = randomFileContent(1024).encode("utf-8")
        f1.content = content1
        calculated_hash = f1.hash()
        expected_hash = calcHash(content1)
        assert calculated_hash == expected_hash, (
            f"SHA256 hash mismatch for small file: expected {expected_hash}, got {calculated_hash}. "
            f"Check hash() method implementation or content reading."
        )

        # Test large file SHA256 hash
        f2 = d.createFile("test2")
        content2 = randomFileContent(1024 * 1024 * 5).encode("utf-8")
        f2.content = content2
        calculated_hash2 = f2.hash()
        expected_hash2 = calcHash(content2)
        assert calculated_hash2 == expected_hash2, (
            f"SHA256 hash mismatch for large file: expected {expected_hash2}, got {calculated_hash2}. "
            f"Check hash() method with large files or content reading."
        )

        # Test MD5 hash algorithm
        calculated_md5 = f2.hash("md5")
        expected_md5 = calcHash(content2, "md5")
        assert calculated_md5 == expected_md5, (
            f"MD5 hash mismatch: expected {expected_md5}, got {calculated_md5}. "
            f"Check hash() method with different algorithm parameter."
        )

    def test_hash_calculator(self):
        """Test FileHashCalculator caching and recalculation modes"""
        path = root / "test_hash_calculator"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        f1 = d.createFile("test1")
        f1.content = randomFileContent(1024 * 1024 * 5).encode("utf-8")
        obj1 = doFolder.hashing.FileHashCalculator()

        # Test initial cache state
        initial_cache = obj1.findCache(f1)
        assert initial_cache is None, (
            f"Initial cache check failed: findCache() should return None for new file but got {initial_cache}. "
            f"Check cache initialization in FileHashCalculator."
        )

        # Test first hash calculation and caching
        res1 = obj1.get(f1)
        cached_result = obj1.findCache(f1)
        assert cached_result == res1, (
            f"Cache storage failed: findCache() should return the same result as get() but values differ. "
            f"Check caching mechanism in FileHashCalculator."
        )

        # Modify content and test cache invalidation
        f1.content = randomFileContent(1024 * 1024 * 5).encode("utf-8")
        res2 = obj1.get(f1)
        assert res2 != res1, (
            f"Cache invalidation failed: hash result should change after content modification but got same result. "
            f"Check content change detection and cache invalidation logic."
        )

        # Test NEVER recalc mode
        obj1.reCalcHashMode = doFolder.hashing.ReCalcHashMode.NEVER
        f1.content = randomFileContent(1024 * 1024 * 5).encode("utf-8")
        never_result = obj1.get(f1)
        assert never_result == res2, (
            f"NEVER recalc mode failed: should return cached result even after content change but got different result. "
            f"Check ReCalcHashMode.NEVER implementation."
        )

        # Test ALWAYS recalc mode
        obj1.reCalcHashMode = doFolder.hashing.ReCalcHashMode.ALWAYS
        res3 = obj1.get(f1)
        time.sleep(1)  # Ensure different timestamps
        res4 = obj1.get(f1)

        assert res3.calcTime != res4.calcTime and res3.hash == res4.hash, (
            f"ALWAYS recalc mode failed: should recalculate with different timestamps but same hash. "
            f"Got calcTime3={res3.calcTime}, calcTime4={res4.calcTime}, hash3={res3.hash}, hash4={res4.hash}. "
            f"Check ReCalcHashMode.ALWAYS implementation."
        )

    def test_threaded_hash_calculator(self):
        """Test ThreadedFileHashCalculator concurrent hash computation"""
        path = root / "test_threaded_hash_calculator"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        # Create multiple test files with random content
        files: list[doFolder.File] = []
        for i in range(20):
            files.append(d.createFile(f"test{i}"))
            files[-1].content = randomFileContent(
                1024 * 1024 * random.randint(1, 8)
            ).encode("utf-8")

        # Test concurrent hash calculation
        with doFolder.hashing.ThreadedFileHashCalculator() as obj1:
            futures_list = [obj1.threadedGet(f) for f in files]

            # Wait for all calculations to complete
            completed_futures = futures.wait(futures_list, timeout=60 * 10)

            # Check that all futures completed successfully
            assert len(completed_futures.done) == len(futures_list), (
                f"Threaded hash calculation timeout: only {len(completed_futures.done)} out of {len(futures_list)} "
                f"hash calculations completed within timeout. Check ThreadedFileHashCalculator performance or increase timeout."
            )

            # Verify all results are valid FileHashResult objects
            for i, future in enumerate(futures_list):
                try:
                    result = future.result()
                    assert isinstance(result, doFolder.hashing.FileHashResult), (
                        f"Invalid result type for file {files[i].name}: expected FileHashResult, got {type(result)}. "
                        f"Check ThreadedFileHashCalculator result type."
                    )
                except Exception as e:
                    assert False, (
                        f"Hash calculation failed for file {files[i].name}: {str(e)}. "
                        f"Check ThreadedFileHashCalculator error handling."
                    )

    def test_div_operators(self):
        """Test division operators for Directory objects"""
        path = root / "test_div_operators"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        t1 = d.createFile("test1")
        file_result = d / "test1"
        assert type(file_result) == doFolder.File and t1.path == file_result.path, (
            f"Single slash operator failed: expected doFolder.File with path {t1.path}, "
            f"but got {type(file_result)} with path {getattr(file_result, 'path', 'N/A')}. "
            f"Check '/' operator implementation for accessing files."
        )

        d2 = d.createDir("test2")
        d2.createDir("test3")
        dir_result = d2 // "test3"
        assert type(dir_result) == doFolder.Directory, (
            f"Double slash operator failed: expected doFolder.Directory for non-existent path 'test3', "
            f"but got {type(dir_result)}. Check '//' operator implementation for directory creation/access."
        )

        try:
            d // "test1"
        except doFolder.exception.PathTypeError:
            pass
        else:
            raise AssertionError(
                "PathTypeError not raised: '//' operator should raise PathTypeError when trying to "
                "access a file as a directory, but no exception was thrown. "
                "Check '//' operator type validation logic."
            )

        d3 = d // "test2" // "test3"
        assert d3.isDir() == True, (
            f"Chained double slash operator failed: expected d3 to be a directory, "
            f"but isDir() returned {d3.isDir()}. Check chained '//' operator implementation "
            f"and directory creation logic."
        )

        d3.createFile("test4")
        created_file = d3["test4"]
        assert created_file.isFile() == True, (
            f"File creation in chained directory failed: expected 'test4' to be a file, "
            f"but isFile() returned {created_file.isFile()}. Check file creation in directories "
            f"created through chained '//' operators."
        )


class TestCompareSystem:
    """
    Tests comparison utility for files and folders, focusing on content, size, timetag, and ignore modes.
    Extended documentation to clarify each assertion's purpose.
    """

    def test_compare_file(self):
        """Test file comparison functionality with different modes"""
        path = root / "test_compare_file"
        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        # Create test files with same content
        content = randomFileContent(1024 * 1024)
        d.createFile("test1").content = content.encode("utf8")
        d.createFile("test2").content = content.encode("utf8")

        # Test content comparison (should match)
        assert doFolder.compare.compare(
            d["test1"], d["test2"], doFolder.compare.CompareMode.CONTENT
        ), f"Content comparison failed: files 'test1' and 'test2' with identical content should match but don't. Check CONTENT compare mode implementation."

        # Modify content and test again (should not match)
        d["test2"].content = "modified content".encode("utf8")
        assert not doFolder.compare.compare(
            d["test1"], d["test2"], doFolder.compare.CompareMode.CONTENT
        ), f"Content comparison failed: files 'test1' and 'test2' with different content should not match but do. Check CONTENT compare mode sensitivity to changes."

        # Test size comparison with different content but same size
        d["test2"].content = randomFileContent(1024 * 1024).encode("utf8")
        assert doFolder.compare.compare(
            d["test1"], d["test2"], doFolder.compare.CompareMode.SIZE
        ), f"Size comparison failed: files 'test1' and 'test2' with same size should match but don't. Check SIZE compare mode implementation."

        # Test ignore mode (should always match)
        assert doFolder.compare.compare(
            d["test1"], d["test2"], doFolder.compare.CompareMode.IGNORE
        ), f"Ignore comparison failed: IGNORE mode should always return True regardless of file differences. Check IGNORE compare mode implementation."

        # Test timetag comparison
        d["test1"].copy(d.path / "test3")
        assert doFolder.compare.compare(
            d["test1"], d["test3"], doFolder.compare.CompareMode.TIMETAG
        ), f"Timetag comparison failed: newly copied file should have similar timestamp to original. Check TIMETAG compare mode or copy() timestamp preservation."

        # Modify content and test timetag again
        d["test3"].content = "modified content".encode("utf8")
        assert not doFolder.compare.compare(
            d["test1"], d["test3"], doFolder.compare.CompareMode.TIMETAG
        ), f"Timetag comparison failed: file with modified content should have different timestamp but comparison still matches. Check TIMETAG compare mode sensitivity."

        # Test comparison with non-existent file
        assert not doFolder.compare.compare(
            d["test1"],
            d.get("test4", unExistsMode=doFolder.UnExistsMode.IGNORE),
            doFolder.compare.CompareMode.IGNORE,
        ), f"Non-existent file comparison failed: comparing with non-existent file should return False even in IGNORE mode. Check comparison with None/non-existent files."

    def test_compare_folder(self):
        """Test directory comparison functionality with nested structures"""
        path = root / "test_compare_dir"

        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        # Create complex nested structure
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

        # Copy directory and test content comparison
        t1.copy(d.path / "test1_copy")
        assert doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
        ), f"Directory content comparison failed: copied directory 'test1_copy' should match original 'test1' but doesn't. Check directory copy() or CONTENT comparison for directories."

        # Modify file content and test again
        t11["test13"].content = randomFileContent(1024 * 1024).encode("utf8")
        assert not doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
        ), f"Directory content comparison failed: directories with different file content should not match but do. Check CONTENT comparison sensitivity for nested changes."

        # Test size comparison (should match despite content changes)
        assert doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.SIZE
        ), f"Directory size comparison failed: directories with same file sizes should match but don't. Check SIZE comparison for directories."

        # Change file size and test again
        t7["test9"].content = randomFileContent(1024 * 5).encode("utf8")
        assert not doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.SIZE
        ), f"Directory size comparison failed: directories with different file sizes should not match but do. Check SIZE comparison sensitivity to file size changes."

        # Test ignore mode (should always match)
        assert doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.IGNORE
        ), f"Directory ignore comparison failed: IGNORE mode should always return True for directories. Check IGNORE comparison implementation for directories."

        # Delete file and test content comparison
        t4["test5"].delete()
        assert not doFolder.compare.compare(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
        ), f"Directory comparison after deletion failed: directories with different file counts should not match. Check CONTENT comparison handling of missing files."

    def test_get_difference(self):
        """Test detailed difference detection between directories"""
        path = root / "test_get_difference"

        d = doFolder.Directory(path, unExistsMode=doFolder.UnExistsMode.CREATE)

        # Create complex nested structure
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

        # Copy and test initial equality
        t1.copy(d.path / "test1_copy")
        assert (
            doFolder.compare.getDifference(
                d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
            )
            is None
        ), f"Initial difference check failed: newly copied directories should have no differences but getDifference() returned a result. Check copy() completeness or getDifference() implementation."

        # Modify content and check differences
        t10["test12"].content = randomFileContent(1024 * 1024).encode("utf8")
        diff0 = doFolder.compare.getDifference(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.CONTENT
        )
        assert (
            diff0 is not None
        ), f"Content difference detection failed: directories with different file content should show differences but getDifference() returned None. Check CONTENT comparison sensitivity."

        # Verify difference structure and path
        diff1 = diff0.sub[0].sub[0].sub[0]
        expected_path1 = d.path / "test1/test4/test10/test12"
        expected_path2 = d.path / "test1_copy/test4/test10/test12"
        assert (
            diff1.path1 == expected_path1
            and diff1.path2 == expected_path2
            and diff1.diffType == doFolder.compare.DifferenceType.FILE_DIFFERENCE
        ), f"Difference details incorrect: expected paths {expected_path1} and {expected_path2} with FILE_DIFFERENCE type, but got {diff1.path1} and {diff1.path2} with {diff1.diffType}. Check difference tree structure."

        flat_diffs = diff0.toFlat()
        assert (
            len(flat_diffs) == 4
        ), f"Flat difference count incorrect: expected 4 differences in hierarchy but got {len(flat_diffs)}. Check toFlat() method."

        # Test size comparison (should be equal)
        assert (
            doFolder.compare.getDifference(
                d["test1"], d["test1_copy"], doFolder.compare.CompareMode.SIZE
            )
            is None
        ), f"Size comparison failed: directories with same file sizes should show no differences but getDifference() returned a result. Check SIZE comparison logic."

        # Change file size and test again
        t8["test9"].content = randomFileContent(1024 * 5).encode("utf8")
        size_diff = doFolder.compare.getDifference(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.SIZE
        )
        assert (
            size_diff is not None
            and size_diff.sub[0].sub[0].sub[0].diffType
            == doFolder.compare.DifferenceType.FILE_DIFFERENCE
        ), f"Size difference detection failed: directories with different file sizes should show FILE_DIFFERENCE but didn't. Check SIZE comparison sensitivity."

        # Test ignore mode (should never find differences)
        assert (
            doFolder.compare.getDifference(
                d["test1"], d["test1_copy"], doFolder.compare.CompareMode.IGNORE
            )
            is None
        ), f"Ignore mode failed: IGNORE comparison should never find differences but getDifference() returned a result. Check IGNORE mode implementation."

        # Delete file and test difference detection
        t6["test7"].delete()
        delete_diff = doFolder.compare.getDifference(
            d["test1"], d["test1_copy"], doFolder.compare.CompareMode.IGNORE
        )
        assert (
            delete_diff is not None
            and delete_diff.toFlat()[-1].diffType
            == doFolder.compare.DifferenceType.NOT_EXISTS
        ), f"Deletion difference detection failed: missing file should show NOT_EXISTS difference type but didn't. Check difference detection for missing files."
