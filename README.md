# 文件夹管理(doFolder)

```bash
pip install doFolder
```

## 使用方法

### 导入

```python
import doFolder
```

### 部分功能

+ `Folder` 指一个文件夹

    + _参数_ `path` 文件夹路径:`str|doFolder.Path`
    + _参数_ `onlisten` 是否监听比同步文件夹变动:`bool`
    + _参数_ `scan` 是否在现在扫描(否则会在访问时进行扫描)
    + _属性_ `files` 文件夹中的文件列表:`FileList`
    + _属性_ `subfolder` 文件夹中的子文件夹:`FolderList`
    + _方法_ `hasFolder,hasFile` 是否包括某个文件/文件夹,参数为 `str`时默认匹配 `.name`属性
    + _方法_ `remove,copy,move` 文件夹操作
    + _方法_ `search` 搜索文件夹的内容
        + _参数_ `condition` 搜索条件:`List[UnformattedMatching]`
        + _参数_ `aim` 目标: `"file"|"folder"|"both"`
        + _参数_ `threaded` 是否线程化 `bool`
        + _参数_ `threaded` 最大线程数:`int`
        + _返回_ 搜索结果:`SearchResult`
+ `File` 指一个文件

    + _参数_ `path` 文件路径:`str|doFolder.Path`
    + _方法_ `remove,copy,move` 文件操作
    + _属性_ `mode,ino,dev,uid,gid...` 参见 `os.stat`
+ `Path` 指一个路径
+ _参数_ `path` 路径(绝对或相对):`str`

    + _属性_ `partition` 将路径(不包含驱动器)切片
    + _方法_ `add` 将内容加载路径后面
    + _方法_ `findRest` 去除两个路径的共同部分
+ `compare`提供比较文件夹的API

    + _函数_ `compare` 比较两个文件夹

        + _参数_ `folder1&folder2` _比较的文件夹:`Folder`_
        + _参数_ `compareContent` 文件内容的比较方法:`str|Callable[[doFolder.File,doFolder.File],bool]`
        + _参数_ `threaded` 是否线程化 `bool`
        + _参数_ `threaded` 最大线程数:`int`
        + *返回* 比较结果:`CompareResult`

### 命令行使用

```bash
compare Folder1 Folder2 [-c ] [-t [-n num]]
```

具体作用参见

```bash
compare -h
```

## 关于作者

作者主页[宽宽2007](https://kuankuan2007.gitee.io "作者主页")

本项目在[苟浩铭/文件夹管理 (gitee.com)](https://gitee.com/kuankuan2007/do-folder)上开源

帮助文档参见[宽宽的帮助文档 (gitee.io)](https://kuankuan2007.gitee.io/docs/do-folder/)

pypi官网项目地址[Pypi](https://pypi.org/project/doFolder/)
