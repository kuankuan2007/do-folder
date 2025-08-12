# doFolder

[![PyPI version](https://badge.fury.io/py/doFolder.svg)](https://badge.fury.io/py/doFolder) [![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=flat&logo=github)](https://github.com/kuankuan2007/do-folder) ![GitHub top language](https://img.shields.io/github/languages/top/kuankuan2007/do-folder) [![License](https://img.shields.io/badge/license-MulanPSL--2.0-blue.svg)](./LICENSE) [![Documentation Status](https://img.shields.io/badge/docs-available-brightgreen.svg?style=flat&logo=read-the-docs)](https://do-folder.doc.kuankuan.site)

**doFolder** 是一个强大、直观且跨平台的文件系统管理库，为文件和目录操作提供了高级的面向对象接口。基于 Python 的 `pathlib` 构建，简化了常见的文件操作，同时提供了散列、内容操作和目录树操作等高级功能。

## ✨ 主要特性

- **🎯 面向对象设计**: 将文件和目录作为 Python 对象处理
- **🌐 跨平台兼容**: 在 Windows、macOS 和 Linux 上无缝工作
- **🛤️ 高级路径处理**: 基于 Python pathlib 的强大路径管理
- **📁 完整的文件操作**: 创建、移动、复制、删除和修改文件和目录
- **📝 内容管理**: 支持编码的文件内容读写
- **🌳 目录树操作**: 导航和操作目录结构
- **🔍 文件比较**: 多种比较模式下的文件和目录比较
- **🔒 散列支持**: 生成和验证文件散列以检查完整性
- **⚠️ 灵活的错误处理**: 针对不同用例的全面错误模式
- **🏷️ 类型安全**: 完整的类型提示，提供更好的 IDE 支持和代码可靠性

## 📦 安装

```bash
pip install doFolder
```

**要求:** Python 3.8+

## 🚀 快速开始

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
    print(f"{item.name} ({'目录' if item.isDir else '文件'})")
```

## 📖 使用示例

### 文件操作

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

# 文件散列
print(f"散列值: {file.hash()}")
```

### 目录操作

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

# 查找特定子项目
py_files = ['__init__.py']
```

### 高级操作

```python
from doFolder import File, Directory, compare

# 文件比较
file1 = File("version1.txt")
file2 = File("version2.txt")

if compare.compare(file1, file2):
    print("文件相同")
else:
    print("文件不同")

# 目录比较
dir1 = Directory("./project_v1")
dir2 = Directory("./project_v2")

diff = getDifference(dir1, dir2)

# 散列验证
file = File("important_data.txt")
original_hash = file.hash()
# ... 文件操作 ...
if file.hash() == original_hash:
    print("文件完整性验证通过")

# 带错误处理的安全操作
from doFolder import UnExistsMode

safe_file = File("might_not_exist.txt", unExists=UnExistsMode.CREATE)
# 如果文件不存在将自动创建
```

### 路径工具

```python
from doFolder import Path

# 增强的路径操作
path = Path("./documents/projects/my_app/src/main.py")

print(f"项目根目录: {path.parents[3]}")  # ./documents/projects/my_app
print(f"相对于项目: {path.relative_to_parent(3)}")  # src/main.py
print(f"扩展名: {path.suffix}")  # .py
print(f"文件名: {path.stem}")  # main

# 路径操作
config_path = path.sibling("config.json")  # 同目录，不同文件
backup_path = path.with_name(f"{path.stem}_backup{path.suffix}")
```

## 🔧 高级功能

### 错误处理模式

doFolder 通过 `UnExistsMode` 提供灵活的错误处理：

```python
from doFolder import File, UnExistsMode

# 处理不存在文件的不同模式
file1 = File("missing.txt", unExists=UnExistsMode.ERROR)    # 抛出异常
file2 = File("missing.txt", unExists=UnExistsMode.WARN)     # 发出警告
file3 = File("missing.txt", unExists=UnExistsMode.IGNORE)   # 静默处理
file4 = File("missing.txt", unExists=UnExistsMode.CREATE)   # 如果缺失则创建
```

### 文件系统项目类型

```python
from doFolder import ItemType, createItem

# 工厂函数创建适当的对象
item1 = createItem("./some_path", ItemType.FILE)      # 创建 File 对象
item2 = createItem("./some_path", ItemType.DIR)       # 创建 Directory 对象
item3 = createItem("./some_path")                     # 自动检测类型
```

## 🔄 从 v1.x.x 迁移

doFolder v2.x.x 在保持向后兼容性的同时引入了多项改进：

- **增强的路径管理**: 现在使用 Python 内置的 `pathlib`
- **重命名的类**: `Folder` → `Directory` (保持向后兼容)
- **灵活的文件创建**: `File` 类可以处理带重定向的目录路径
- **改进的类型安全**: 整个代码库的完整类型提示

### 迁移示例

```python
# v1.x.x 风格 (仍然可用)
from doFolder import Folder
folder = Folder("./my_directory")

# v2.x.x 推荐风格
from doFolder import Directory
directory = Directory("./my_directory")

# 两者使用方式完全相同！
```

## 📚 文档

- **完整的 API 文档**: [https://do-folder.doc.kuankuan.site](https://do-folder.doc.kuankuan.site)
- **GitHub 仓库**: [https://github.com/kuankuan2007/do-folder](https://github.com/kuankuan2007/do-folder)
- **问题跟踪**: [https://github.com/kuankuan2007/do-folder/issues](https://github.com/kuankuan2007/do-folder/issues)

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。对于重大更改，请先开启一个 issue 来讨论您想要更改的内容。

## 📄 许可证

本项目采用 [MulanPSL-2.0 许可证](./LICENSE) - 详见 LICENSE 文件。
