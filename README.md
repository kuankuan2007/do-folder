# doFolder

[![PyPI version](https://badge.fury.io/py/doFolder.svg)](https://badge.fury.io/py/doFolder) [![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=flat&logo=github)](https://github.com/kuankuan2007/do-folder) ![GitHub top language](https://img.shields.io/github/languages/top/kuankuan2007/do-folder) [![License](https://img.shields.io/badge/license-MulanPSL--2.0-blue.svg)](./LICENSE) [![Documentation Status](https://img.shields.io/badge/docs-available-brightgreen.svg?style=flat&logo=read-the-docs)](https://do-folder.doc.kuankuan.site)

**doFolder** is a powerful, intuitive, and cross-platform file system management library that provides a high-level, object-oriented interface for working with files and directories. Built on Python's `pathlib`, it simplifies common file operations while offering advanced features like hashing, content manipulation, and directory tree operations.

## ✨ Key Features

- **🎯 Object-oriented Design**: Work with files and directories as Python objects
- **🌐 Cross-platform Compatibility**: Seamlessly works on Windows, macOS, and Linux
- **🛤️ Advanced Path Handling**: Built on Python's pathlib for robust path management
- **📁 Complete File Operations**: Create, move, copy, delete, and modify files and directories
- **📝 Content Management**: Read and write file content with encoding support
- **🌳 Directory Tree Operations**: Navigate and manipulate directory structures
- **🔍 File Comparison**: Compare files and directories with various comparison modes
- **🔒 Hash Support**: Generate and verify file hashes for integrity checking
- **⚠️ Flexible Error Handling**: Comprehensive error modes for different use cases
- **🏷️ Type Safety**: Full type hints for better IDE support and code reliability

## 📦 Installation

```bash
pip install doFolder
```

**Requirements:** Python 3.8+

## 🚀 Quick Start

```python
from doFolder import File, Directory, ItemType

# Create directory and file objects
project_dir = Directory("./my_project")
config_file = project_dir["config.json"]

# Create a new file in the directory
readme = project_dir.create("README.md", ItemType.FILE)
readme_zh = project_dir.createFile("README.zh-cn.md")

# Write content to the file
readme.content = "# My Project\n\nWelcome to my project!".encode("utf-8")

# Create a subdirectory
src_dir = project_dir.create("src", ItemType.DIR)

# Copy and move files
backup_config = config_file.copy("./backup/")
config_file.move("./settings/")

# List directory contents
for item in project_dir:
    print(f"{item.name} ({'Directory' if item.isDir else 'File'})")
```

## 📖 Usage Examples

### Working with Files

```python
from doFolder import File

# Create a file object
file = File("data.txt")

# Work with binary content
print(file.content) # Reads content as bytes
file.content = "Binary data here".encode("utf-8") # Writes content as bytes

# JSON operations
file.saveAsJson({"name": "John", "age": 30})
data = file.loadAsJson()

# Quickly open file
with file.open("w", encoding="utf-8") as f:
    f.write("Hello, World!")


# File information
print(f"Size: {file.state.st_size} bytes")
print(f"Modified: {file.state.st_mtime}")

# File hashing
print(f"Hash: {file.hash()}")
```

### Working with Directories

```python
from doFolder import Directory, ItemType

# Create a directory object
d = Directory("./workspace")

# Create nested directory structure
d.create("src/utils", ItemType.DIR)
d.create("tests", ItemType.DIR)
d.createDir("docs")
d.createFile("README.md")

# Create files
main_file = d.create("src/main.py", ItemType.FILE)
test_file = d.create("tests/test_main.py", ItemType.FILE)

# List all items (non-recursive)
for item in d:
    print(item.path)

# List all items recursively
for item in d.recursiveTraversal(hideDirectory=False):
    print(f"{'📁' if item.isDir else '📄'} {item.path}")

# Find specific sub items
py_files = ['__init__.py']
```

### Advanced Operations

```python
from doFolder import File, Directory, compare

# File comparison
file1 = File("version1.txt")
file2 = File("version2.txt")

if compare.compare(file1, file2):
    print("Files are identical")
else:
    print("Files differ")

# Directory comparison
dir1 = Directory("./project_v1")
dir2 = Directory("./project_v2")

diff=getDifference(dir1, dir2)

# Hash verification
file = File("important_data.txt")
original_hash = file.hash()
# ... file operations ...
if file.hash() == original_hash:
    print("File integrity verified")

# Safe operations with error handling
from doFolder import UnExistsMode

safe_file = File("might_not_exist.txt", unExists=UnExistsMode.CREATE)
# File will be created if it doesn't exist
```

### Path Utilities

```python
from doFolder import Path

# Enhanced path operations
path = Path("./documents/projects/my_app/src/main.py")

print(f"Project root: {path.parents[3]}")  # ./documents/projects/my_app
print(f"Relative to project: {path.relative_to_parent(3)}")  # src/main.py
print(f"Extension: {path.suffix}")  # .py
print(f"Filename: {path.stem}")  # main

# Path manipulation
config_path = path.sibling("config.json")  # Same directory, different file
backup_path = path.with_name(f"{path.stem}_backup{path.suffix}")
```

## 🔧 Advanced Features

### Error Handling Modes

doFolder provides flexible error handling through `UnExistsMode`:

```python
from doFolder import File, UnExistsMode

# Different modes for handling non-existent files
file1 = File("missing.txt", unExistsMode=UnExistsMode.ERROR)    # Raises exception
file2 = File("missing.txt", unExistsMode=UnExistsMode.WARN)     # Issues warning
file3 = File("missing.txt", unExistsMode=UnExistsMode.IGNORE)   # Silent handling
file4 = File("missing.txt", unExistsMode=UnExistsMode.CREATE)   # Creates if missing
```

### File System Item Types

```python
from doFolder import ItemType, createItem

# Factory function to create appropriate objects
item1 = createItem("./some_path", ItemType.FILE)      # Creates File object
item2 = createItem("./some_path", ItemType.DIR)       # Creates Directory object
item3 = createItem("./some_path")                     # Auto-detects type
```

## 🔄 Migration from v1.x.x

doFolder v2.x.x introduces several improvements while maintaining backward compatibility:

- **Enhanced Path Management**: Now uses Python's built-in `pathlib`
- **Renamed Classes**: `Folder` → `Directory` (backward compatibility maintained)
- **Flexible File Creation**: `File` class can handle directory paths with redirection
- **Improved Type Safety**: Full type hints throughout the codebase

### Migration Example

```python
# v1.x.x style (still works)
from doFolder import Folder
folder = Folder("./my_directory")

# v2.x.x recommended style
from doFolder import Directory
directory = Directory("./my_directory")

# Both work identically!
```

## 📚 Documentation

- **Full API Documentation**: [https://do-folder.doc.kuankuan.site](https://do-folder.doc.kuankuan.site)
- **GitHub Repository**: [https://github.com/kuankuan2007/do-folder](https://github.com/kuankuan2007/do-folder)
- **Issue Tracker**: [https://github.com/kuankuan2007/do-folder/issues](https://github.com/kuankuan2007/do-folder/issues)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the [MulanPSL-2.0 License](./LICENSE) - see the LICENSE file for details.
