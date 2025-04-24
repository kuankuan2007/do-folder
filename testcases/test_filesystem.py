from tempfile import TemporaryDirectory
import random
import pytest
from pathlib import Path

import sys

print(1)

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
    return "random content:"+ '-'.join([_randomLine() for _ in range(10)])

def setup_module(module):
    global TEMP_DIR, root
    TEMP_DIR = TemporaryDirectory(prefix="pytest-doFolder-")
    root=Path(TEMP_DIR.name)

def teardown_module(module):
    TEMP_DIR.cleanup()

class TestFileSystem:
    def test_path(self):
        assert doFolder.Path==Path

    def test_create_file(self):
        path=root/'test_create'
        path.touch()
        inner=getRandomString()
        path.write_text(inner,encoding='utf8')

        t1 = doFolder.File(path)
        assert t1.exists(), f"File {path} not exists"
        assert t1.isFile(), f"File {path} is not a file"
        assert t1.content==inner.encode('utf8'), f"File {path} content is not correct"
    def test_file_operation(self):
        path=root/'test_file_operation'
        path.touch()
        inner=getRandomString()
        path.write_text(inner,encoding='utf8')

        t1 = doFolder.File(path)
        assert t1.exists(), f"File {path} not exists"

        copyPath = root / "test_file_operation_copy"
        movePath = root / "test_file_operation_move"

        t1.copy(copyPath)
        assert (copyPath).exists(), f"File was not copied to {copyPath}"
        assert copyPath.read_text(encoding='utf8')==inner, f"File {path} content is not equal to {copyPath}"

        t1.move(movePath)
        assert not path.exists() , f"File {path} was not moved to {movePath}"
        assert movePath.exists(), f"File {path} was not moved to {movePath}"
        assert movePath.read_text(encoding='utf8')==inner, f"File {path} content is not equal to {movePath}"
        
        t1.delete()
        assert not movePath.exists(), f"File {path} was not deleted"
    
    def test_create_folder(self):
        path=root/'test_create_folder'
        path.mkdir()
        inner=getRandomString()
        
        d=doFolder.Directory(path)
        assert d.exists(), f"Folder {path} not exists"
        assert d.isFile()==False, f"Folder {path} is not a folder"
        try:
            d.content
        except _ex.OpenDirectoryError:
            assert True, f"Folder {path} can be opened"
        
        c1=tuple(d.__iter__())
        assert len(c1)==0, f"Folder {path} is not empty"
        
        d.create("test1",doFolder.CreateType.FILE).content=inner.encode('utf8')
        d.create("test2",doFolder.CreateType.DIR)
        
        for i in d:
            if isinstance(i,doFolder.Directory):
                assert i.name=="test2", f"Folder {path} is not created"
            else:
                assert i.name=="test1" and i.content==inner.encode('utf8'), f"File {path} is not created"
    
    def test_folder_operation(self):
        path=root/'test_folder_operation'
        path.mkdir()
        inner=getRandomString()

        d=doFolder.Directory(path)
        d.create("test1",doFolder.CreateType.FILE).content=inner.encode('utf8')

        assert d.exists(), f"Folder {path} not exists"

        copyPath = root / "test_folder_operation_copy"
        movePath = root / "test_folder_operation_move"

        d.copy(copyPath)
        assert (copyPath).exists(), f"Folder was not copied to {copyPath}"
        assert (copyPath/'test1').read_text(encoding='utf8')==inner, f"File {path} content is not equal to {copyPath}"

        d.move(movePath)
        assert not path.exists() , f"Folder {path} was not moved to {movePath}"
        assert movePath.exists(), f"Folder {path} was not moved to {movePath}"
        assert (movePath/'test1').read_text(encoding='utf8')==inner, f"File {path} content is not equal to {movePath}"

        d.delete()
        assert not movePath.exists(), f"Folder {path} was not deleted"
