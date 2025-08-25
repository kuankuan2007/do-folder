# doFolder

[![PyPI version](https://badge.fury.io/py/doFolder.svg)](https://badge.fury.io/py/doFolder) [![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=flat&logo=github)](https://github.com/kuankuan2007/do-folder) ![GitHub top language](https://img.shields.io/github/languages/top/kuankuan2007/do-folder) [![License](https://img.shields.io/badge/license-MulanPSL--2.0-blue.svg)](./LICENSE) [![Documentation Status](https://img.shields.io/badge/docs-available-brightgreen.svg?style=flat&logo=read-the-docs)](https://do-folder.doc.kuankuan.site)

**doFolder** 是一个功能强大、直观且跨平台的文件系统管理库，提供了一个高级的、面向对象的接口来处理文件和目录。它基于 Python 的 `pathlib` 构建，简化了常见的文件操作，同时提供了哈希、内容操作和目录树操作等高级功能。

## ✨ 主要特性

- **🎯 面向对象设计**：将文件和目录作为 Python 对象进行操作
- **🌐 跨平台兼容性**：在 Windows、macOS 和 Linux 上无缝工作
- **🛤️ 高级路径处理**：基于 Python 的 pathlib 进行稳健的路径管理
- **📁 完整的文件操作**：创建、移动、复制、删除和修改文件和目录
- **📝 内容管理**：支持编码的文件内容读写
- **🌳 目录树操作**：导航和操作目录结构
- **🔍 文件比较**：支持多种比较模式的文件和目录比较
- **🔒 哈希支持**：生成和验证文件哈希以进行完整性检查，支持多种算法
- **⚡ 高性能哈希**：多线程哈希计算，具有智能缓存和进度跟踪
- **🖥️ 命令行工具**：全面的 CLI 接口，包括直接命令（`do-compare`、`do-hash`）和统一接口（`do-folder`）
- **⚠️ 灵活的错误处理**：针对不同用例的全面错误处理模式
- **🏷️ 类型安全**：完整的类型提示，提供更好的 IDE 支持和代码可靠性

## 📦 安装

```bash
pip install doFolder
```

**要求：** Python 3.9+

**注意：** 从 2.3.0 版本开始不再支持 Python 3.8

## 🚀 快速入门

### 命令行快速入门

安装后，您可以立即开始使用 doFolder 的命令行工具：

```bash
# 比较两个目录
do-compare /path/to/source /path/to/backup

# 比较并同步目录
do-compare /path/to/source /path/to/backup --sync --sync-direction A2B

# 计算文件哈希
do-hash file1.txt file2.txt

# 使用特定算法计算
do-hash -a sha256,md5 README.md README.zh-cn.md

# 递归哈希目录中的所有文件
do-hash -r -d /path/to/project

# 使用统一接口
do-folder compare /dir1 /dir2 --compare-mode CONTENT
do-folder hash -a blake2b *.py
# 或者
python -m doFolder compare /dir1 /dir2 --compare-mode CONTENT
python -m doFolder hash -a blake2b *.py
# 注意：do-folder 等同于 python -m doFolder，您可以选择任意一种使用
```

### Python 快速入门

```python
from doFolder import File, Directory, ItemType

# 创建目录和文件对象
project_dir = Directory("./my_project")
config_file = project_dir["config.json"]

# 在目录中创建新文件
readme = project_dir.create("README.md", ItemType.FILE)
readme_zh = project_dir.createFile("README.zh-cn.md")

# 向文件写入内容
readme.content = "# My Project\n\nWelcome to my project!".encode("utf-8")

# 创建子目录
src_dir = project_dir.create("src", ItemType.DIR)

# 复制和移动文件
backup_config = config_file.copy("./backup/")
config_file.move("./settings/")

# 列出目录内容
for item in project_dir:
    print(f"{item.name} ({'Directory' if item.isDir else 'File'})")
```

## 📖 用法示例

### 处理文件

```python
from doFolder import File

# 创建文件对象
file = File("data.txt")

# 处理二进制内容
print(file.content) # 以字节形式读取内容
file.content = "Binary data here".encode("utf-8") # 以字节形式写入内容

# JSON 操作
file.saveAsJson({"name": "John", "age": 30})
data = file.loadAsJson()

# 快速打开文件
with file.open("w", encoding="utf-8") as f:
    f.write("Hello, World!")

# 文件信息
print(f"大小: {file.state.st_size} 字节")
print(f"修改时间: {file.state.st_mtime}")

# 文件哈希
print(f"哈希: {file.hash()}")
print(f"SHA256: {file.hash('sha256')}")
print(f"MD5: {file.hash('md5')}")

# 使用多线程哈希以获得更好性能
from doFolder.hashing import ThreadedFileHashCalculator

with ThreadedFileHashCalculator(threadNum=4) as calculator:
    result = calculator.get(file)
    print(f"线程哈希: {result.hash}")
```

### 处理目录

```python
from doFolder import Directory, ItemType

# 创建目录对象
d = Directory("./workspace")

# 创建嵌套目录结构
d.create("src/utils", ItemType.DIR)
d.create("tests", ItemType.DIR)
d.createDir("docs")
d.createFile("README.md")

# 创建文件
main_file = d.create("src/main.py", ItemType.FILE)
test_file = d.create("tests/test_main.py", ItemType.FILE)

# 列出所有项目（非递归）
for item in d:
    print(item.path)

# 递归列出所有项目
for item in d.recursiveTraversal(hideDirectory=False):
    print(f"{'📁' if item.isDir else '📄'} {item.path}")

# 查找特定的子项目
py_files = ['__init__.py']
```

### 命令行操作

doFolder 提供了强大的命令行工具用于文件系统操作：

```bash
# 使用不同模式比较两个目录
do-folder compare /path/to/dir1 /path/to/dir2 --compare-mode CONTENT
do-compare /path/to/dir1 /path/to/dir2 --sync --sync-direction A2B

# 使用多种算法计算文件哈希
do-folder hash -a sha256,md5 file1.txt file2.txt
do-hash -a blake2b -r /path/to/directory

# 对大文件使用多线程以提高性能
do-hash -n 8 -d -r -a sha256 /path/to/large_files/
# 选项：-n: 线程数, -d: 允许目录, -r: 递归
```

### 高级操作

```python
from doFolder import File, Directory, compare
from doFolder.hashing import FileHashCalculator, multipleFileHash

# 文件比较
file1 = File("version1.txt")
file2 = File("version2.txt")

if compare.compare(file1, file2):
    print("文件相同")
else:
    print("文件不同")

# 带有详细差异分析的目录比较
dir1 = Directory("./project_v1")
dir2 = Directory("./project_v2")

diff = compare.getDifference(dir1, dir2)
if diff:
    # 以扁平结构打印所有差异
    for d in diff.toFlat():
        print(f"差异: {d.path1} vs {d.path2} - {d.diffType}")

# 带缓存和多算法的高级哈希
calculator = FileHashCalculator()
file = File("important_data.txt")

# 单一算法
result = calculator.get(file, "sha256")
print(f"SHA256: {result.hash}")

# 缓存哈希以提高性能
print(f"第二次结果: {calculator.get(file).hash}")

file.content = "新内容".encode("utf-8")

# 文件内容更改时缓存将失效
print(f"第三次结果: {calculator.get(file).hash}")

# 一次性使用多种算法（只需一次磁盘读取）
results = calculator.multipleGet(file, ["sha256", "md5", "blake2b"])
for algo, result in results.items():
    print(f"{algo.upper()}: {result.hash}")
```

### 路径工具

自 v2.0.0 起，`doFolder.Path` 是 Python 内置 `pathlib.Path` 的别名，取代了旧版本中自定义的 `specialStr.Path`。

有关详细信息，请参阅 [pathlib 官方文档](https://docs.python.org/3/library/pathlib.html)。

## 💻 命令行界面

doFolder 提供了强大的命令行工具，支持统一接口和直接命令两种方式进行文件系统操作。

### 安装与使用

安装 doFolder 后，您可以使用以下命令行工具：

```bash
# 安装 doFolder
pip install doFolder

# 直接命令（快捷方式）
do-compare /path1 /path2    # 文件/目录比较
do-hash file.txt            # 文件哈希

# 统一接口
do-folder compare /path1 /path2    # 等同于 do-compare
do-folder hash file.txt            # 等同于 do-hash

# Python 模块接口
python -m doFolder compare /path1 /path2
python -m doFolder hash file.txt
```

### 比较命令

使用各种选项比较文件或目录：

```bash
# 基本比较
do-compare file1.txt file2.txt
do-compare /directory1 /directory2

# 不同的比较模式
do-compare /dir1 /dir2 --compare-mode CONTENT    # 比较文件内容
do-compare /dir1 /dir2 --compare-mode SIZE       # 比较文件大小
do-compare /dir1 /dir2 --compare-mode TIMETAG    # 比较修改时间

# 同步
do-compare /source /backup --sync --sync-direction A2B   # 将 A 同步到 B
do-compare /dir1 /dir2 --sync --sync-direction BOTH      # 双向同步

# 覆盖处理
do-compare /dir1 /dir2 --sync --overwrite AUTO          # 根据时间戳自动决定
do-compare /dir1 /dir2 --sync --overwrite ASK           # 对每个冲突进行询问
```

### 哈希命令

使用多种算法和选项计算文件哈希：

```bash
# 基本哈希（默认为 SHA256）
do-hash file.txt

# 多种算法
do-hash -a sha256,md5,sha1 file.txt
do-hash -a blake2b important_document.txt -a md5,sha1 another_file.txt

# 目录哈希
do-hash -d /directory                    # 哈希目录中的所有文件（非递归）
do-hash -r -d /project                   # 递归目录哈希

# 性能选项
do-hash -n 8 -d -a sha256,md5,blake2b ./src

# 禁用进度显示以获得更清晰的输出
do-hash --no-progress -r -d /path/to/files

# 路径格式化
do-hash -p /absolute/path/file.txt       # 使用绝对路径
do-hash -f file.txt                      # 始终显示完整路径
```

### 全局选项

所有命令都支持这些全局选项：

```bash
# 版本信息
do-folder -v                    # 显示版本
do-folder -vv                   # 显示详细版本信息

# 输出控制
do-folder --no-color compare /dir1 /dir2     # 禁用彩色输出
do-folder -w 120 hash file.txt              # 设置控制台宽度
do-folder -m hash file.txt                  # 静默警告
do-folder -t compare /dir1 /dir2             # 错误时显示完整的回溯信息
```

### 实际示例

**备份验证：**

```bash
# 比较原始数据和备份，并同步差异
do-compare /important/data /backup/data --sync --sync-direction A2B --overwrite AUTO
```

**开发工作流：**

```bash
# 比较项目的两个版本
do-compare /project/v1 /project/v2 --compare-mode CONTENT

# 哈希所有源文件以进行变更检测
do-hash -a blake2b -r /src --full-path
```

## 🔧 高级特性

### 命令行界面

doFolder 提供了全面的命令行工具，具有两种使用模式：

**统一接口：**

```bash
# 主命令带子命令
do-folder compare /path/to/dir1 /path/to/dir2 --sync
do-folder hash -a sha256,md5 file1.txt file2.txt

# 使用 Python 模块
python -m doFolder compare /source /backup --compare-mode CONTENT
python -m doFolder hash -a blake2b -r /directory
```

**直接命令：**

```bash
# 直接命令快捷方式
do-compare /path/to/dir1 /path/to/dir2 --sync --overwrite AUTO
do-hash -a sha256,md5 file1.txt file2.txt --thread-num 8
```

#### 比较命令特性

- 多种比较模式（SIZE、CONTENT、TIMETAG、TIMETAG_AND_SIZE、IGNORE）
- 支持双向同步的目录同步
- 灵活的覆盖策略（A2B、B2A、ASK、AUTO、IGNORE）
- 相对时间戳格式化
- 交互式冲突解决

#### 哈希命令特性

- 支持多种哈希算法（SHA 家族、MD5、BLAKE2、SHA3 等）
- 多线程处理以提高性能
- 递归目录哈希
- 带有详细状态的进度跟踪
- 灵活的输出格式

### 高级哈希系统

doFolder 包含一个具有多个优化级别的复杂哈希系统：

```python
from doFolder.hashing import (
    FileHashCalculator,
    ThreadedFileHashCalculator,
    ReCalcHashMode,
    MemoryFileHashManager
)
from concurrent.futures import wait


# 带缓存的基本计算器
calculator = FileHashCalculator(
    algorithm="sha256",
    useCache=True,
    reCalcHashMode=ReCalcHashMode.TIMETAG  # 仅在文件修改时重新计算
)

# 多线程计算器以获得更好性能
with ThreadedFileHashCalculator(threadNum=8) as threaded_calc:
    # 并发处理多个文件
    futures = [threaded_calc.threadedGet(file) for file in file_list]
    wait(futures)
    results = [future.result() for future in futures]

# 自定义缓存管理器
from doFolder.hashing import LfuMemoryFileHashManager
calculator = FileHashCalculator(
    cacheManager=LfuMemoryFileHashManager(maxSize=1000)
)
```

### 错误处理模式

doFolder 通过 `UnExistsMode` 提供灵活的错误处理：

```python
from doFolder import File, UnExistsMode

# 处理不存在文件的不同模式
file1 = File("missing.txt", unExistsMode=UnExistsMode.ERROR)    # 引发异常
file2 = File("missing.txt", unExistsMode=UnExistsMode.WARN)     # 发出警告
file3 = File("missing.txt", unExistsMode=UnExistsMode.IGNORE)   # 静默处理
file4 = File("missing.txt", unExistsMode=UnExistsMode.CREATE)   # 如果不存在则创建
```

### 文件系统项目类型

```python
from doFolder import ItemType, createItem

# 用于创建适当对象的工厂函数
item1 = createItem("./some_path", ItemType.FILE)      # 创建 File 对象
item2 = createItem("./some_path", ItemType.DIR)       # 创建 Directory 对象
item3 = createItem("./some_path")                     # 自动检测类型
```

## 🔄 从 v1.x.x 迁移

doFolder v2.x.x 引入了多项改进，同时保持了向后兼容性：

- **增强的路径管理**：现在使用 Python 内置的 `pathlib`
- **重命名的类**：`Folder` → `Directory`（保持向后兼容性）
- **灵活的文件创建**：`File` 类可以处理带重定向的目录路径
- **改进的类型安全**：整个代码库提供完整的类型提示

### 迁移示例

```python
# v1.x.x 风格（仍然有效）
from doFolder import Folder
folder = Folder("./my_directory")

# v2.x.x 推荐风格
from doFolder import Directory
directory = Directory("./my_directory")

# 两者功能完全相同！
```

## 📚 文档

- **完整 API 文档**: [https://do-folder.doc.kuankuan.site](https://do-folder.doc.kuankuan.site)
- **命令行界面指南**: [CLI 文档](https://do-folder.doc.kuankuan.site/cli.html)
- **GitHub 仓库**: [https://github.com/kuankuan2007/do-folder](https://github.com/kuankuan2007/do-folder)
- **问题跟踪**: [https://github.com/kuankuan2007/do-folder/issues](https://github.com/kuankuan2007/do-folder/issues)

## 🤝 贡献

欢迎贡献！请随时提交拉取请求。对于重大更改，请先打开一个问题来讨论您想要更改的内容。

## 📄 许可证

该项目根据 [MulanPSL-2.0 许可证](./LICENSE) 获得许可 - 有关详细信息，请参阅 LICENSE 文件。
