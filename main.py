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
from typing import Any,Union,Callable,Literal,List,Tuple,Iterable,TypeVar,Generic,IO,Dict,overload,Set
import shutil
import copy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler,FileSystemEvent,FileSystemMovedEvent,EVENT_TYPE_CREATED,EVENT_TYPE_DELETED,EVENT_TYPE_MODIFIED
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from specialStr import Path
import base64
import json
from concurrent.futures import ThreadPoolExecutor,_base
import time

__all__=["File","Folder","Path"]

EVENT_TYPES=Literal["created","deleted","modified"]

SearchCondition=Union[str,re.Pattern,Callable[[Union["File","Folder"]],bool]]
FormatedMatching=Tuple[Callable[[Union["File","Folder"]],bool],int,Union[int,None]]
UnformattedMatching=Union[SearchCondition,Tuple[SearchCondition,int,Union[int,None]]]
_T=TypeVar("_T",bound="_HasName")
_U=TypeVar("_U")
class RuntimeError(Exception):
    def __init__(self, error:BaseException) -> None:
        super().__init__(str(error))
        self.error=error
class DisabledError(Exception):
    pass
class UnknownError(Exception):
    def __init__(self) -> None:
        super().__init__('Sorry, an unknown error has occurred. This could have been due to an oversight by the author. If you feel the same way, open an issue on Gitee(https://gitee.com/kuankuan2007/do-folder) or Github(https://github.com/kuankuan2007/do-folder)') 
def tryRun(fn:Callable[...,_U])->Union[_U,RuntimeError]:
    try:
        return fn()
    except BaseException as e:
        return RuntimeError(e)
class _HasName(Generic[_T]):
    name: str
class _FolderUpdateHeader (FileSystemEventHandler):
    def __init__(self,target:"Folder"):
        self.target=target
    def on_moved(self, event:FileSystemMovedEvent):
        self.target._update(Path(event.src_path).findRest(self.target.path),EVENT_TYPE_DELETED,Path(event.src_path),event.is_directory)
        self.target._update(Path(event.dest_path).findRest(self.target.path),EVENT_TYPE_CREATED,Path(event.dest_path),event.is_directory)
    def on_deleted(self, event:FileSystemEvent):
        self.target._update(Path(event.src_path).findRest(self.target.path),event.event_type,Path(event.src_path),event.is_directory)
    def on_created(self, event:FileSystemEvent):
        self.target._update(Path(event.src_path).findRest(self.target.path),event.event_type,Path(event.src_path),event.is_directory)
    def on_modified(self, event:FileSystemEvent):
        if event.is_directory:
            return
        self.target._update(Path(event.src_path).findRest(self.target.path),event.event_type,Path(event.src_path),event.is_directory)
    
class FolderOrFileNotFoundError(Exception):
    def __init__(self,reason):
        self.reason=reason
    def __str__(self) -> str:
        return str(self.reason)
    def __repr__(self) -> str:
        return str(self.reason)

class FileOrFolderAlreadyExists(Exception):
    def __init__(self,reason):
        self.reason=reason
    def __str__(self) -> str:
        return str(self.reason)
    def __repr__(self) -> str:
        return str(self.reason)

def _formatMatching(condition:UnformattedMatching)->FormatedMatching:
    limit=(1,1)
    if type(condition)==tuple and not callable(condition):
        limit=(condition[1],condition[2])
        condition= condition[0]
    if type(condition)==str and not callable(condition):
        match:Callable[[Union["File","Folder"]],bool]=lambda item:item.name==condition
    elif type(condition)==re.Pattern and not callable(condition):
        match:Callable[[Union["File","Folder"]],bool]=lambda item:bool(condition.search(item.name))
    elif callable(condition):
        match=condition
    else:
        raise ValueError(f"Unknown condition \"{condition}\" type is \"{type(condition)}\"")
    return (match,limit[0],limit[1])
class _ObjectListIndexedByName(Generic[_T]):
    def __init__(self,var:Iterable[_T]=[]):
        self.values:List[_T]=list(var)
    def remove(self,var:_T) -> None:
        self.values.remove(var)
    def removeByName(self,name:str)->None:
        for i in self.values:
            if i.name==name:
                self.values.remove(i)
                return
        raise ValueError(f"No Object named \"{name}\"")
    def __str__(self) -> str:
        return f"<{self.__class__.__name__} len={len(self.values)}>"
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.values}>"
    def append(self,var:_T):
        self.values.append(var)
    def __len__(self):
        return len(self.values)
    def __add__(self,var:"_ObjectListIndexedByName"):
        return _ObjectListIndexedByName(self.values+var.values)
    def __contains__(self,var:Union[_T,str])->bool:
        if var in self.values :
            return True
        for i in range(len(self.values)):
            if  self.values[i].name == var:
                return True
        return False
    def __getitem__(self,key:Union[int,str])->Union[_T,None]:
        if type(key)==str:
            for i in self.values:
                if i.name == key:
                    return i
            return None
        elif type(key)==int:
            return  self.values[key]
        return None
    def __getattribute__(self,key:str)->Any:
        try:
            return super().__getattribute__(key)
        except AttributeError:
            for i in self.values:
                if i.name == key:
                    return i
            raise AttributeError(f"name {key} is neither attribute or name of values")
    def __iter__(self):
        return self.values.__iter__()
    def getSubAttribute(self,key:str)->List:
        retsult=[]
        for i in self:
            if type(tryRun(lambda:i.__getattribute__(key)))==RuntimeError:
                raise AttributeError(f"Not all attributes named \"{key}\" of the list are existent")
            retsult.append(i.__getattribute__(key))
        return retsult
    def callSubAttribute(self,fn:str,*args,**kw)->Any:
        li=self.getSubAttribute(fn)
        for i in li:
            if not callable(i):
                raise AttributeError(f"Not all attributes named \"{fn}\" of the list are callable")
        return [tryRun(lambda:i(*args,**kw)) for i in li]

class SearchResult(_ObjectListIndexedByName[Union["File","Folder"]]):
    def __init__(self,var:Iterable[Union["File","Folder"]]=[],match:Union[FormatedMatching,None]=None):
        super().__init__(var)
        self.match=match
    def __add__(self,var:"SearchResult"):
        return SearchResult(self.values+var.values,match=self.match)
    def remove(self) -> None:
        self.callSubAttribute("remove")
    def copy(self,path:Union[str,Path]) -> None:
        self.callSubAttribute("copy",path)
    def move(self,path:Union[str,Path]) -> None:
        self.callSubAttribute("move",path)
    def rename(self,newName:str) -> None:
        li=self.getSubAttribute("rename")
        for index,i in enumerate(li):
            i(newName.format(index,i=index,index=index))
class FileList(_ObjectListIndexedByName["File"]):
    def __init__(self,var:Iterable["File"]=[]):
        super().__init__(var)
    def __add__(self,var:"FileList"):
        return FileList(self.values+var.values)
class FolderList(_ObjectListIndexedByName["Folder"]):
    def __init__(self,var:Iterable["Folder"]=[]):
        super().__init__(var)
    def __add__(self,var:"FolderList"):
        return FolderList(self.values+var.values)
class FileSystemNode(_HasName):
    path:Path
    copy:Callable[[],None]
    remove:Callable[[],None]
    move:Callable[[str],None]
    rename:Callable[[str],None]
class File(FileSystemNode):
    """
    Represents a file on disk.
    ## Attributes:
        - path (Path): The path of the file.
        - parent (Folder or None): The parent folder of the file.
        - mode (int): The mode of the file.
        - ino (int): The inode number of the file.
        - dev (int): The device identifier of the filesystem containing this file.
        - uid (int): The user ID of the owner of this file.
        - gid (int): The group ID of the owner of this file.
        - size(int) :The size, in bytes,of this file
        - mtime(float) :The time when content was last modified expressed as seconds since epoch
        - atime(float) :The time when content was last accessed expressed as seconds since epoch
        - content(bytes) :The contents read from and written to files.
        - md5(str),sha1(str),sha256(str),sha512(str)：Hashes for verifying data integrity.
    ## Methods:
        -__init__(self,path:Union[str,Path],parent:Union["Folder",None]=None)
        Initializes a new instance with specified path and optional parent folder.
        - refresh(self)
        Rebuilds all attributes based on current state on disk.
        - open(self,*args,**kw)->IO
        Opens and returns a handle to underlying OS-level representation using built-in open function.
        - remove(self)
        Deletes underlying OS-level representation using os.remove() method.
        - copy(self,path:str)
        Copies underlying OS-level representation to specified destination using shutil.copy() method.
        - move(self,path:str)
        Moves underlying OS-level representation to specified destination using shutil.move() method.
        - __str__(self)->str
        Returns string representation "<File \"{name}\">".
        - __repr__(self)->str
        Returns string representation "<File \"{name}\">".
        - rename(self,newName:str)->None
            Rename the file
    """
    def __init__(self,path:Union[str,Path],parent:Union["Folder",None]=None):
        self._active=True
        if type(path)!=Path:
            path=Path(path)
        self.path = path
        self.parent = parent
        self.refresh()
    def deactivate(self):
        self._active=False
    def refresh(self):
        """Rebuild all of this file object"""
        state=os.stat(self.path)
        self.mode=state.st_mode
        self.ino=state.st_ino
        self.dev=state.st_dev
        self.uid=state.st_uid
        self.gid=state.st_gid
        self.size=state.st_size
        self.mtime=state.st_mtime
        self.ctime=state.st_ctime
        self.atime=state.st_atime
        self._md5:Union[None,str]=None
        self._sha1:Union[None,str]=None
        self._sha256:Union[None,str]=None
        self._sha512:Union[None,str]=None
    @property
    def name(self)->str:
        return self.path.name
    def open(self,*args,**kw)->IO:
        """open the file by function open"""
        return open(self.path,*args,**kw)
    def __str__(self)->str:
        return f"<File \"{self.name}\">"
    def __repr__(self) -> str:
        return f"<File \"{self.name}\">"
    @property
    def content(self)->bytes:
        with self.open("rb") as f:
            return f.read()
    @content.setter
    def _setContent(self,content:bytes):
        with self.open("wb") as f:
            f.write(content)
    @property
    def md5(self)->str:
        if self._md5:
            return self._md5
        self._md5=hashlib.md5(self.content).hexdigest()
        return self._md5
    @property
    def sha1(self)->str:
        if self._sha1:
            return self._sha1
        self._sha1=hashlib.sha1(self.content).hexdigest()
        return self._sha1
    @property
    def sha256(self)->str:
        if self._sha256:
            return self._sha256
        self._sha256=hashlib.sha256(self.content).hexdigest()
        return self._sha256
    @property
    def sha512(self)->str:
        if self._sha512:
            return self._sha512
        self._sha512=hashlib.sha512(self.content).hexdigest()
        return self._sha512
    @property
    def hash(self)->str:
        return self.md5
    def remove(self):
        os.remove(self.path)
        if self.parent:
            self.parent._updateRemoveSubItem(self.name)
        
    def copy(self,path:str):
        shutil.copy(self.path,path)
    def move(self,path:str):
        shutil.move(self.path,path)
        if self.parent:
            self.parent._updateRemoveSubItem(self.name)
    def rename(self,newName:str)->None:
        splitPath=self.path.spitPath(False)
        while len(splitPath) and splitPath[-1]=="":
            splitPath=splitPath[:-1]
        if not len(splitPath):
            raise ValueError("The path has no location to rename")
        splitPath[-1]=newName
        newPath:Path=Path(self.path.driver+"/".join(splitPath))
        os.rename(self.path,newPath)
        if self.parent:
            self.parent._updateRenameSubItem(self.name,newName)
    def __getattribute__(self, __name: str) -> Any:
        if not super().__getattribute__("_active") and __name not in ["_active","path","parent","name"]:
            raise DisabledError('Can not get item from disabled file. You abandoned me, and then you flirt with me like this')
        return super().__getattribute__(__name)
class Folder(FileSystemNode):
    """
    Represents a folder on disk.
    ## Attributes:
        - path (Union[str,Path]): The path of the folder.
        - onlisten (bool): Whether to listen for changes in the folder.
        - parent (Union["Folder",None]): The parent folder of this folder. None if it is a root directory.
        - scaned (bool): Whether the contents of this folder have been scanned and stored in memory.
        - scan(bool): Whether to automatically scan and store all contents when initializing or refreshing this object.
    ## Methods:
        - __init__(self,path:Union[str,Path],onlisten:bool=False,parent:Union["Folder",None]=None,scan:bool=False)
        Initializes a new instance of the Folder class with specified parameters.
        - refresh(self)
        Rebuilds all information about files and subfolders contained within this Folder object.
        - __str__(self)->str
        Returns string representation of current object
        - __repr__(self) -> str
        Returns string representation that can be used to recreate an equivalent instance using eval() function
        - __contains__(self,item:Union[str,"Folder","File"]) -> bool
        Determines whether item exists within current directory or not
        - __getitem__(self,key)->Union["File","Folder",None]
        Gets file/folder by name from current directory
        - forEach(self,callback:Callable[[Union["File","Folder"]],Any],rootPosition:Literal["first","last"]="first")->None
        Goes through each element in current directory calling callback function for each one.
        - forEachFile(self,callback:Callable[[File],Any])->None
        Goes through each file in current directory calling callback function for each one.
        - forEachFolder(self,callback:Callable[["Folder"],Any],rootPosition:Literal["first","last"]="first")->None:
        Goes through each subfolder in current directory calling callback function for each one.
        - remove(self)->None
        Removes current folder and all its contents
        - move(self,path:str)->None
        Moves current folder to specified path
        - rename(self,newName:str)->None
        Rename the folder
        - copy(self,path:str)->None:
        Copies current folder to specified path
        - hasSubfolder(self,name:str,recursive:bool=False)->bool:
        Determines whether a subfolder with the given name exists within this Folder object or not.
        - hasFile(self,name:str,recursive:bool=False)->bool:
        Determines whether a file with the given name exists within this Folder object or not.
        - search(self,condition:List[UnformattedMatching],aim:Literal["file","folder","both"]="both",threaded:bool=False,threads:Union[None,int]=None)
        Searches for files/folders in the current directory that match certain criteria.
        - createFile(self,path:Union[str,Path],content:bytes=b"")->Path
        Creates a new file at the specified location with optional content.
        - createFolder(self,path:Union[str,Path])->Path
        Creates a new sub-folder at the specified location.
    """
    def __init__(self,path:Union[str,Path],onlisten:bool=False,parent:Union["Folder",None]=None,scan:bool=False,ignores:Iterable[Union[str,Path]]=[],gitignore:bool=False):
        self._active=True
        if type(path)!=Path:
            path=Path(path)
        self.onlisten=onlisten
        self.path=path
        self.parent=parent
        self.scaned=scan
        self.scan=scan
        self.logger=logging.getLogger(self.name)
        if self.onlisten:
            self.event_handler = _FolderUpdateHeader(self)
            self.observer = Observer()
            self.observer.schedule(self.event_handler, path=path, recursive=True)
            self.observer.start()
        gitignores=[]
        self.gitignore=gitignore
        if gitignore:
            try:
                with open(path.add(".gitignore"),encoding="utf-8") as f:
                    gitignores=[i[:-1] for i in set(f.readlines())]
                    
            except:
                gitignores=[]
        self.ignores:List[Path]=[]
        for i in set(gitignores+list(ignores)):
            if type(i)!=Path:
                i=Path(path.getAbsolutePath(i))
            self.ignores.append(i)
        if scan:
            self.refresh()
    def deactivate(self):
        self._active=False
    def refresh(self):
        self.logger.debug("refresh folder contents")
        """Rebuild all of this folder object"""
        self.scaned=True
        self.dir:List[str]=os.listdir(self.path)
        self.files:FileList = FileList([])
        self.subfolder:FolderList=FolderList([])
        for i in self.dir:
            newPath=self.path.add(i)
            if newPath in self.ignores:
                continue
            if os.path.isfile(newPath):
                self.files.append(self._newFile(newPath))
            elif os.path.isdir(newPath):
                self.subfolder.append(self._newSubFolder(newPath))
    def _newFile(self,path:Path)->File:
        return File(path,parent=self)
    def _newSubFolder(self,path:Path)->"Folder":
        return Folder(path,parent=self,scan=self.scan,ignores=self.ignores,gitignore=self.gitignore)
    @property
    def name(self)->str:
        return self.path.name
    def __str__(self)->str:
        return f"<Folder \"{self.name}\">"
    def __repr__(self) -> str:
        return self.__str__()
    def __contains__(self,item:Union[str,"Folder","File"]) -> bool:
        if type(item)==str:
            return item in self.dir
        elif type(item)==Folder:
            return item in self.subfolder
        elif type(item)==File:
            return item in self.files
        return False
    def __getitem__(self,key)->Union["File","Folder",None]:
        if not self._active and key not in ["path","name"]:
            raise DisabledError('Can not get item from disabled folder. You abandoned me, and then you flirt with me like this')
        for item in self.subfolder:
            if item.name==key:
                return item
        for item in self.files:
            if item.name==key:
                return item
        return None
    def __travel(self):
        for i in self.files:
            yield i
        for i in self.subfolder:
            yield i
    def __iter__(self):
        return self.__travel()
    def _update(self,path:List[str],eventType:str,eventTarget:Path,isDirectory:bool):
        """Update when something changes"""
        if not self.scaned:
            return
        if len(path)>1:
            nextFolder=self[path[0]]
            if type(nextFolder)==Folder:
                nextFolder._update(path[1:],eventType,eventTarget,isDirectory)
            return
        self.logger.debug(f"file content update.{eventType}")
        name=path[0]
        if eventType==EVENT_TYPE_CREATED:
            if name in self: return
            if name in self.ignores: return
            if isDirectory:self.subfolder.append(self._newSubFolder(eventTarget))
            else:self.files.append(self._newFile(eventTarget))
        if eventType==EVENT_TYPE_DELETED:
            target=self[name]
            if type(target)==Folder:self.subfolder.remove(target)
            elif type(target)==File:self.files.remove(target)
        if eventType==EVENT_TYPE_MODIFIED:
            target=self[name]
            if type(target)==File:target.refresh()
    def __getattribute__(self, name: str) -> Any:
        if not super().__getattribute__('_active')  and name not in ["path","name","parent","_active"]:
            raise DisabledError('Can not get attributes from disabled folder. You abandoned me, and then you flirt with me like this')
        if not super().__getattribute__("scaned"):
            self.refresh()
        try:
            return super().__getattribute__(name)
        except AttributeError:
            target=self[name]
            if target:
                return target
            raise AttributeError(f"\"{name}\" is not a attribute ,a subfolder or a file")
    def forEach(self,callback:Callable[[Union["File","Folder"]],Any],rootPosition:Literal["first","last"]="first")->None:
        """
        Go through each of these elements
        :param callback:The function to call
        :rootPosition:Is the root before or after the child element
        """
        if  rootPosition=="first":
            callback(self)
        for item in self.files:
            callback(item)
        for item in self.subfolder:
            item.forEach(callback,rootPosition)
        if rootPosition=="last":
            callback(self)
    def forEachFile(self,callback:Callable[[File],Any])->None:
        """
        Go through each of these file
        :param callback:The function to call
        """
        for item in self.files:
            callback(item)
        for item in self.subfolder:
            item.forEachFile(callback)
    def forEachFolder(self,callback:Callable[["Folder"],Any],rootPosition:Literal["first","last"]="first")->None:
        """
        Go through each of these folder
        :param callback:The function to call
        :param rootPosition:Is the root before or after the child element
        """
        if  rootPosition=="first":
            callback(self)
        for item in self.subfolder:
            item.forEachFolder(callback,rootPosition)
        if rootPosition=="last":
            callback(self)
    def remove(self)->None:
        self.logger.info("Removing folder")
        shutil.rmtree(self.path)
        if self.parent:
            self.parent._updateRemoveSubItem(self.name)
    def _updateRemoveSubItem(self,name:str):
        item=self[name]
        if item==None:
            return
        elif isinstance(item,File):
            self.files.remove(item)
        elif isinstance(item,Folder):
            self.subfolder.remove(item)
        item.deactivate()
    def move(self,path:str)->None:
        self.logger.info(f"Moving folder to {path}")
        shutil.move(self.path,path)
    def copy(self,path:str)->None:
        self.logger.info(f"Copying folder to {path}")
        shutil.copytree(self.path, path)
    def rename(self,newName:str)->None:
        splitPath=self.path.spitPath(False)
        while len(splitPath) and splitPath[-1]=="":
            splitPath=splitPath[:-1]
        if not len(splitPath):
            raise ValueError("The path has no location to rename")
        splitPath[-1]=newName
        newPath:Path=Path(self.path.driver+"/".join(splitPath))
        os.rename(self.path,newPath)
        if self.parent:
            self.parent._updateRenameSubItem(self.name,newName)
    def _updateRenameSubItem(self,name:str,newName: str):
        item=self[name]
        if item==None:
            return
        elif isinstance(item,File):
            self.files.remove(item)
            self.files.append(self._newFile(self.path.add(newName)))
        elif isinstance(item,Folder):
            self.subfolder.remove(item)
            self.subfolder.append(self._newSubFolder(self.path.add(newName)))
        item.deactivate()
    def hasSubfolder(self,name:str,recursive:bool=False)->bool:
        """
        Whether to include a subfolder
        :param name:folder name
        """
        for i in self.subfolder:
            if i.name==name:
                return True
        if recursive:
            for i  in self.subfolder:
                if i.hasSubfolder(name,recursive=recursive):
                    return True
        return False
    def hasFile(self,name:str,recursive:bool=False)->bool:
        """
        Whether to include a file
        :param name:file name
        """
        for i in self.files:
            if i.name==name:
                return True
        if recursive:
            for i  in self.subfolder:
                if i.hasFile(name,recursive=recursive):
                    return True
        return False
    def search(self,condition:List[UnformattedMatching],aim:Literal["file","folder","both"]="both",threaded:bool=False,threads:Union[None,int]=None)->SearchResult:
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
        threadPool=ThreadPoolExecutor(max_workers=threads) if threaded else None
        waitlist:List[_base.Future]=[]
        retsult:SearchResult=SearchResult()
        
        self._match([_formatMatching(i) for i in condition],retsult,aim=aim,pool=threadPool,waitlist=waitlist)
        for i in waitlist:
            while not i.done():
                time.sleep(0.1)
        return retsult
    def _match(self,condition:List[FormatedMatching],retsult:SearchResult,aim:Literal["file","folder","both"]="both",pool:Union[ThreadPoolExecutor,None]=None,waitlist:List[_base.Future]=[])->None:
        """
        This is the ultimate implementation of the search behavior, but if your criteria are not formatted, consider starting with the "search" function, which will format the criteria and complete the search for you
        :param condition: search conditions which is formatted
        :param aim: search type
        """
        for i in range(len(condition)):
            if aim!="folder":
                for j in self.files:
                    if not condition[i][0](j):continue
                    restCondition=copy.deepcopy(condition[i:])
                    restCondition[0]=(restCondition[0][0],max(restCondition[0][1]-1,0),None if restCondition[0][2]==None else max(restCondition[0][2]-1,0))
                    k=i
                    while k<len(restCondition):
                        if restCondition[k][1]!=0:
                            break
                        k+=1
                    if (k==len(restCondition)):
                        retsult.append(j)
            for j in self.subfolder:
                if not condition[i][0](j):continue
                restCondition=copy.deepcopy(condition)
                restCondition[0]=(restCondition[0][0],max(restCondition[0][1]-1,0),None if restCondition[0][2]==None else max(restCondition[0][2]-1,0))
                if restCondition[0][2]!=None and restCondition[0][2]<=0:del restCondition[0]
                if pool:waitlist.append(pool.submit(j._match,restCondition,retsult,aim,pool))
                else:j._match(restCondition,retsult,aim,pool)
                if aim=="file":continue
                k=i
                while k<len(restCondition):
                    if restCondition[k][1]!=0:
                        break
                    k+=1
                if (k==len(restCondition)):
                    retsult.append(j)
            if condition[i][1]>0:
                break
    @overload
    def _create(self,name: str,aimType:Literal['File'],content:Union[None,bytes]=None)->File:...
    @overload
    def _create(self,name: str,aimType:Literal['Folder'])->"Folder":...
    def _create(self,name:str,aimType:Literal['File','Folder']='File',content:Union[None,bytes]=None):
        fullpath=self.path.add(name)
        if os.path.exists(fullpath):
            raise FileOrFolderAlreadyExists("We can't create a file for that folder because it already exists")
        if aimType=="File":
            with open(fullpath,'wb') as f:
                if content:
                    f.write(content)
            aim= self._newFile(fullpath)
            self.files.append(aim)
            return aim
        else:
            os.mkdir(fullpath)
            aim= self._newSubFolder(fullpath)
            self.subfolder.append(aim)
            return aim
    @overload
    def _deepCreate(self,paths: List[str],aimType:Literal['File'],content:Union[None,bytes]=None)->File:...
    @overload
    def _deepCreate(self,paths: List[str],aimType:Literal['Folder'])->"Folder":...
    def _deepCreate(self,paths: List[str],aimType:Literal['File','Folder']='File',content:Union[None,bytes]=None):
        if len(paths)<=0:
            raise UnknownError()
        if (len(paths)==1):
            if aimType=="File":
                return self._create(paths[0],aimType,content)
            else:
                return self._create(paths[0],aimType)
        else:
            nextFolder=self[paths[0]]
            if isinstance(nextFolder,File):
                raise FileOrFolderAlreadyExists(f"The file {paths[0]} already exists in {self.path}, so we cannot create folder there")
            if nextFolder==None:
                nextFolder=self._create(paths[0],"Folder")
            if aimType=="File":
                return nextFolder._deepCreate(paths[1:],aimType,content)
            else:
                return nextFolder._deepCreate(paths[1:],aimType)
    def createFile(self,path:Union[str,Path],content:bytes=b"")->File:
        """
        Create a new file at the specified path with the given content.
        :param path: The path where the file will be created. Can be either a string or a Path object.
        :param content: The bytes to write into the newly created file. Default is an empty byte string.
        :return: A Path object representing the newly created file.
        :raise FileOrFolderAlreadyExists: If there is already a file or folder at the specified path.
        """
        path=self.path.getAbsolutePath(path)
        paths=path.findRest(self.path)
        return self._deepCreate(paths,"File",content)
    def createFolder(self,path:Union[str,Path])->"Folder":
        """
        Create a new folder at the specified path.
        :param path: The path where the new folder will be created. Can be either a string or a Path object.
        :return: Returns a Path object representing the newly created folder.
        :raise FileOrFolderAlreadyExists: If there is already a file or folder with the same name as `path`.
        """
        path=self.path.getAbsolutePath(path)
        paths=path.findRest(self.path)
        return self._deepCreate(paths,"Folder")
    def add(self,aim:Union["File","Folder"],move:bool=False):
        "add a file or folder to this folder"
        if move:
            aim.move(self.path)
        else:
            aim.copy(self.path)
    def _normalizedToDictIncludeFiles(self,includeFiles:Union[Literal["info","base64","bytes","keep"],Callable[[File],Any]])->Callable[[File],Any]:
        if callable(includeFiles):
            return includeFiles
        ma:Dict[str,Callable[[File],Any]]={
            "base64":lambda x:{
                "name":x.name,
                "base64":base64.b64encode(x.content).decode(),    
            },
            "info":lambda x:{
                "name":x.name,
                "size":x.size,
                "dev":x.dev,
                "uid":x.uid,
                "gid":x.gid,
                "ctime":x.ctime,
                "atime":x.atime,
                "mtime":x.mtime,
                "ino":x.ino,
                "mode":x.mode
            },
            "bytes":lambda x:{
                "name":x.name,
                "bytes":x.content
            },
            "keep":lambda x:x
        }
        if includeFiles in ma:
            return ma[includeFiles]
        raise ValueError(f"Invalid value for includeFiles: {includeFiles}")
    def toDict(self,includeFiles:Union[Literal["ignore","info","base64","bytes","keep"],Callable[[File],Any]]="keep")->Dict[str,Any]:
        result={}
        result["type"]="Folder"
        result["name"]=self.name
        if includeFiles!="ignore":
            includeFiles=self._normalizedToDictIncludeFiles(includeFiles)
            result["files"]=[includeFiles(i) for i in self.files]
        result["subfolder"]={i.name:i.toDict(includeFiles) for i in self.subfolder}
        return result
    def toJson(self,**kw)->str:
        return json.dumps(self.toDict("base64"),**kw)