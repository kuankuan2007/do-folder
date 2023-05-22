# 文件夹管理(doFolder)

```
pip install import doFolder
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
    + _属性_ `files` 文件夹中的文件列表:`FileList`
    + _属性_ `subfolder` 文件夹中的子文件夹:`FolderList`
    + _方法_ `hasFolder,hasFile` 是否包括某个文件/文件夹,参数为`str`时默认匹配`.name`属性
    + _方法_ `remove,copy,move` 文件夹操作
    + _方法_ `search` 搜索文件夹的内容
        + _参数_ `condition` 搜索条件:`List[UnformattedMatching]`
        + _参数_ `aim` 目标: `"file"|"folder"|"both"`
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
+ `FolderList,FileList` 模拟列表
    + 支持遍历,用index(`str`或`int`)获取值
    + in 运算符可以针对`str`使用，代表匹配`.name`属性
+ `UnformattedMatching` 搜索条件,可能的类型和意义如下
    + `str` 表示完全匹配文件名/文件夹名
    + `re.Pattern` 用正则表达式匹配文件名/文件夹名
    + `Callable[[Union["File","Folder"]],bool]` 自定义匹配函数
    + `FormattedMatching` 意义如下所示
+ `FormattedMatching` 针对`UnformattedMatching`归一化的结果
    类型为`Tuple`,长度为3
    1. `Callable[[Union["File","Folder"]],bool]` 匹配函数
    2. `int` 最小重复次数(默认1)
    3. `int|None` 最大重复次数|正无穷(默认为1)
## 关于作者

作者主页[宽宽2007](https://kuankuan2007.gitee.io "作者主页")

本项目在[苟浩铭/文件夹管理 (gitee.com)](https://gitee.com/kuankuan2007/do-folder)上开源

帮助文档参见[宽宽的帮助文档 (gitee.io)](https://kuankuan2007.gitee.io/docs/do-folder/)
