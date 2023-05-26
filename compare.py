import doFolder.main as doFolder
from typing import Literal,List,Union
from concurrent.futures import ThreadPoolExecutor
class RepeatedExecutionError(Exception):
    def __init__(self,message:str):
        self.message=message
    def __str__(self):
        return self.message
class FileMissing(doFolder._HasName):
    def __init__(self,file:doFolder.File,root:doFolder.Folder,anotherFolder:doFolder.Folder):
        self.file = file
        self.root = root
        self.anotherFolder = anotherFolder
        self.statue:Literal["copied","removed","waiting"]="waiting"
    @property
    def path(self)->List[str]:
        return self.file.path.findRest(self.root.path)
    @property
    def name(self)->str:
        return self.file.name
    def copy(self)->None:
        if self.statue!="waiting":
            raise RepeatedExecutionError(f"This file has already been {self.statue}")
        self.statue="copied"
        pathto=self.anotherFolder.path.adds(self.path)
        self.file.copy(pathto)
    def remove(self)->None:
        if self.statue!="waiting":
            raise RepeatedExecutionError(f"This file has already been {self.statue}")
        self.statue="removed"
        self.file.remove()
    def __str__(self) -> str:
        return f"<FileMissing file={self.file} missingRoot={self.anotherFolder}>"
    def __repr__(self) -> str:
        return self.__str__()
class FolderMissing(doFolder._HasName):
    def __init__(self,folder:doFolder.Folder,root:doFolder.Folder,anotherFolder:doFolder.Folder):
        self.folder = folder
        self.root = root
        self.anotherFolder = anotherFolder
        self.statue:Literal["copied","removed","waiting"]="waiting"
    @property
    def path(self)->List[str]:
        return self.folder.path.findRest(self.root.path)
    @property
    def name(self)->str:
        return self.folder.name
    def copy(self)->None:
        if self.statue!="waiting":
            raise RepeatedExecutionError(f"This file has already been {self.statue}")
        self.statue="copied"
        pathto=self.anotherFolder.path.adds(self.path)
        self.folder.copy(pathto)
    def remove(self)->None:
        if self.statue!="waiting":
            raise RepeatedExecutionError(f"This file has already been {self.statue}")
        self.statue="removed"
        self.folder.remove()
    def __str__(self) -> str:
        return f"<FolderMissing file={self.folder} missingRoot={self.anotherFolder}>"
    def __repr__(self) -> str:
        return self.__str__()
class FileDifferent(doFolder._HasName):
    def __init__(self,file1:doFolder.File,file2:doFolder.File,root1:doFolder.Folder,root2:doFolder.Folder):
        self.file1 = file1
        self.file2 = file2
        self.root1 = root1
        self.root2 = root2
        self.statue:Literal["choice1","choice2","removed","waiting"]="waiting"
    @property
    def path(self)->List[str]:
        return self.file1.path.findRest(self.root1.path)
    @property
    def name(self)->str:
        return self.file1.name
    def copy(self,choice:Literal[1,2])->None:
        if self.statue!="waiting":
            raise RepeatedExecutionError(f"This file has already been {self.statue}")
        if choice==1:
            self.statue="choice1"
            pathto=self.root2.path.adds(self.path)
            self.file1.copy(pathto)
        else:
            self.statue="choice2"
            pathto=self.root1.path.adds(self.path)
            self.file2.copy(pathto)
    def remove(self)->None:
        if self.statue!="waiting":
            raise RepeatedExecutionError(f"This file has already been {self.statue}")
        self.statue="removed"
        self.file1.remove()
        self.file2.remove()
    def __str__(self) -> str:
        return f"<FileDifferent file1={self.file1} file2={self.file2}>"
    def __repr__(self) -> str:
        return self.__str__()

class CompareResult(doFolder._HasName):
    def __init__(self,folder1:doFolder.Folder,folder2:doFolder.Folder):
        self.folder1=folder1
        self.folder2=folder2
        self._fileMissingList:doFolder._ObjectListIndexedByName[FileMissing]=doFolder._ObjectListIndexedByName(var=[])
        self._folderMissingList:doFolder._ObjectListIndexedByName[FolderMissing]=doFolder._ObjectListIndexedByName(var=[])
        self._fileDifferentList:doFolder._ObjectListIndexedByName[FileDifferent]=doFolder._ObjectListIndexedByName(var=[])
        self._FolderDifferentList:doFolder._ObjectListIndexedByName[CompareResult]=doFolder._ObjectListIndexedByName(var=[])
        self.cacheFileMissingList:Union[List[FileMissing],None]=None
        self.cacheFileDifferentList:Union[List[FileDifferent],None]=None
        self.cacheFolderMissingList:Union[List[FolderMissing],None]=None
    @property
    def name(self)->str:
        return self.folder1.name
    def newDifferent(self,different:Union[FileMissing,FolderMissing,FileDifferent,"CompareResult"]) -> None:
        if type(different) is FileMissing:
            self._fileMissingList.append(different)
        elif type(different) is FolderMissing:
            self._folderMissingList.append(different)
        elif type(different) is FileDifferent:
            self._fileDifferentList.append(different)
        elif type(different) is CompareResult:
            self._FolderDifferentList.append(different)
    def __str__(self):
        return f"<CompareResult between {self.folder1} and {self.folder2}>"
    def __repr__(self):
        return self.__str__()
    @property
    def fileMissingList(self)->List[FileMissing]:
        if self.cacheFileMissingList==None:
            self.cacheFileMissingList=self._fileMissingList.values
            for  i in self._FolderDifferentList:
                self.cacheFileMissingList+=i.fileMissingList
        return self.cacheFileMissingList
    @property
    def fileDifferentList(self)->List[FileDifferent]:
        if self.cacheFileDifferentList==None:
            self.cacheFileDifferentList=self._fileDifferentList.values
            for  i in self._FolderDifferentList:
                self.cacheFileDifferentList+=i.fileDifferentList
        return self.cacheFileDifferentList
    @property
    def folderMissingList(self)->List[FolderMissing]:
        if self.cacheFolderMissingList==None:
            self.cacheFolderMissingList=self._folderMissingList.values
            for  i in self._FolderDifferentList:
                self.cacheFolderMissingList+=i.folderMissingList
        return self.cacheFolderMissingList
    @property
    def differentList(self)->List[Union[FileMissing,FolderMissing,FileDifferent]]:
        return self.fileMissingList+self.folderMissingList+self.fileDifferentList
def _compareFile(result:CompareResult,file1:doFolder.File,file2:doFolder.File,compareContent:Literal["ignore","hash","content","size"],root1:doFolder.Folder
            ,root2:doFolder.Folder)->None:
    if compareContent=="hash" and file1.hash!=file2.hash:
        result.newDifferent(FileDifferent(file1,file2,root1,root2))
    elif compareContent=="content" and file1.content!=file2.content:
        result.newDifferent(FileDifferent(file1,file2,root1,root2))
    elif compareContent=="size" and file1.size!=file2.size:
        result.newDifferent(FileDifferent(file1,file2,root1,root2))
def compare(folder1:doFolder.Folder,folder2:doFolder.Folder,compareContent:Literal["ignore","hash","content","size"]="ignore",threaded:bool=False,threads:Union[None,int]=None)->CompareResult:
    threadPool=ThreadPoolExecutor(max_workers=threads) if threaded else None
    result=_compare(folder1,folder2,folder1,folder2,compareContent,threadPool)
    assert result
    if threadPool:threadPool.shutdown(wait=True)
    return result
def _compare(folder1:doFolder.Folder,folder2:doFolder.Folder,root1:doFolder.Folder
            ,root2:doFolder.Folder,compareContent:Literal["ignore","hash","content","size"]="ignore",threadPool:Union[ThreadPoolExecutor,None]=None,parent:Union[CompareResult,None]=None)->Union[CompareResult,None]:
    result=CompareResult(folder1,folder2)
    for file1 in folder1.files:
        file2=folder2.files[file1.name]
        if file2==None:
            result.newDifferent(FileMissing(file1,root1,root2))
        else:
            if threadPool:threadPool.submit(_compareFile,result,file1,file2,compareContent,root1,root2)
            else:_compareFile(result,file1,file2,compareContent,root1,root2)
    for file2 in folder2.files:
        file1=folder1.files[file2.name]
        if file1==None:
            result.newDifferent(FileMissing(file2,root2,root1))
    for subfolder1 in folder1.subfolder:
        subfolder2=folder2.subfolder[subfolder1.name]
        if subfolder2==None:
            result.newDifferent(FolderMissing(subfolder1,root1,root2))
        else:
            if threadPool:threadPool.submit(_compare,subfolder1,subfolder2,root1,root2,compareContent,threadPool,result)
            else:_compare(subfolder1,subfolder2,root1,root2,compareContent,threadPool,result)
    for subfolder2 in folder2.subfolder:
        subfolder1=folder1.subfolder[subfolder2.name]
        if subfolder1==None:
            result.newDifferent(FolderMissing(subfolder2,root2,root1))
    if parent:
        parent.newDifferent(result)
        return
    else:
        return result
