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
- **🔒 Hash Support**: Generate and verify file hashes for integrity checking with multi-algorithm support
- **⚡ High-Performance Hashing**: Multi-threaded hash calculation with intelligent caching and progress tracking
- **🖥️ Command-Line Tools**: Comprehensive CLI interface with direct commands (`do-compare`, `do-hash`) and unified interface (`do-folder`)
- **⚠️ Flexible Error Handling**: Comprehensive error modes for different use cases
- **🏷️ Type Safety**: Full type hints for better IDE support and code reliability

## 📦 Installation

```bash
pip install doFolder
```

**Requirements:** Python 3.9+

**Note:** Python 3.8 is no longer supported since version 2.3.0

## 🚀 Quick Start

### Command-Line Quick Start

After installation, you can immediately start using doFolder's command-line tools:

```bash
# Compare two directories
do-compare /path/to/source /path/to/backup

# Compare and sync directories
do-compare /path/to/source /path/to/backup --sync --sync-direction A2B

# Calculate file hashes
do-hash file1.txt file2.txt

# Calculate with specific algorithms
do-hash -a sha256,md5 README.md README.zh-cn.md

# Hash all files in a directory recursively
do-hash -r -d /path/to/project

# Use unified interface
do-folder compare /dir1 /dir2 --compare-mode CONTENT
do-folder hash -a blake2b *.py
# Or
python -m doFolder compare /dir1 /dir2 --compare-mode CONTENT
python -m doFolder hash -a blake2b *.py
# Note: do-folder is equal to python -m doFolder, use any of them you like
```

### Python Quick Start

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
print(f"SHA256: {file.hash('sha256')}")
print(f"MD5: {file.hash('md5')}")

# Multi-threaded hashing for better performance
from doFolder.hashing import ThreadedFileHashCalculator

with ThreadedFileHashCalculator(threadNum=4) as calculator:
    result = calculator.get(file)
    print(f"Threaded hash: {result.hash}")
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

### Command-Line Operations

doFolder provides powerful command-line tools for file system operations:

```bash
# Compare two directories with different modes
do-folder compare /path/to/dir1 /path/to/dir2 --compare-mode CONTENT
do-compare /path/to/dir1 /path/to/dir2 --sync --sync-direction A2B

# Calculate file hashes with multiple algorithms
do-folder hash -a sha256,md5 file1.txt file2.txt
do-hash -a blake2b -r /path/to/directory

# Use threading for better performance on large files
do-hash -n 8 -d -r -a sha256 /path/to/large_files/
# Options: -n: number of threads, -d: allow directory, -r: recursive
```

### Advanced Operations

```python
from doFolder import File, Directory, compare
from doFolder.hashing import FileHashCalculator, multipleFileHash

# File comparison
file1 = File("version1.txt")
file2 = File("version2.txt")

if compare.compare(file1, file2):
    print("Files are identical")
else:
    print("Files differ")

# Directory comparison with detailed difference analysis
dir1 = Directory("./project_v1")
dir2 = Directory("./project_v2")

diff = compare.getDifference(dir1, dir2)
if diff:
    # Print all differences in flat structure
    for d in diff.toFlat():
        print(f"Difference: {d.path1} vs {d.path2} - {d.diffType}")

# Advanced hashing with caching and multiple algorithms
calculator = FileHashCalculator()
file = File("important_data.txt")

# Single algorithm
result = calculator.get(file, "sha256")
print(f"SHA256: {result.hash}")

# Cached hashing for better performance
print(f"The second result: {calculator.get(file).hash}")

file.content = "New content".encode("utf-8")

# The cache will invalidate when file content changes
print(f"The third result: {calculator.get(file).hash}")

# Multiple algorithms at once (only one disk read is needed)
results = calculator.multipleGet(file, ["sha256", "md5", "blake2b"])
for algo, result in results.items():
    print(f"{algo.upper()}: {result.hash}")
```

### Path Utilities

Since v2.0.0, `doFolder.Path` is an alias for Python's built-in `pathlib.Path`, instead of the custom `specialStr.Path` from older versions.

For detailed information, please see [pathlib documentation](https://docs.python.org/3/library/pathlib.html).

## 💻 Command-Line Interface

doFolder provides powerful command-line tools for file system operations with both unified and direct command interfaces.

### Installation & Usage

After installing doFolder, you get access to several command-line tools:

```bash
# Install doFolder
pip install doFolder

# Direct commands (shortcuts)
do-compare /path1 /path2    # File/directory comparison
do-hash file.txt            # File hashing

# Unified interface
do-folder compare /path1 /path2    # Same as do-compare
do-folder hash file.txt            # Same as do-hash

# Python module interface
python -m doFolder compare /path1 /path2
python -m doFolder hash file.txt
```

### Compare Command

Compare files or directories with various options:

```bash
# Basic comparison
do-compare file1.txt file2.txt
do-compare /directory1 /directory2

# Different comparison modes
do-compare /dir1 /dir2 --compare-mode CONTENT    # Compare file contents
do-compare /dir1 /dir2 --compare-mode SIZE       # Compare file sizes
do-compare /dir1 /dir2 --compare-mode TIMETAG    # Compare modification times

# Synchronization
do-compare /source /backup --sync --sync-direction A2B   # Sync A to B
do-compare /dir1 /dir2 --sync --sync-direction BOTH      # Bidirectional sync

# Overwrite handling
do-compare /dir1 /dir2 --sync --overwrite AUTO          # Auto decide by timestamp
do-compare /dir1 /dir2 --sync --overwrite ASK           # Ask for each conflict
```

### Hash Command

Calculate file hashes with multiple algorithms and options:

```bash
# Basic hashing (uses SHA256 by default)
do-hash file.txt

# Multiple algorithms
do-hash -a sha256,md5,sha1 file.txt
do-hash -a blake2b important_document.txt -a md5,sha1 another_file.txt

# Directory hashing
do-hash -d /directory                    # Hash all file in directory(no recursion)
do-hash -r -d /project                   # Recursive directory hashing

# Performance options
do-hash -n 8 -d -a sha256,md5,blake2b ./src

# Disable progress display for cleaner output
do-hash --no-progress -r -d /path/to/files

# Path formatting
do-hash -p /absolute/path/file.txt       # Use absolute paths
do-hash -f file.txt                      # Always show full path
```

### Global Options

All commands support these global options:

```bash
# Version information
do-folder -v                    # Show version
do-folder -vv                   # Show detailed version info

# Output control
do-folder --no-color compare /dir1 /dir2     # Disable colored output
do-folder -w 120 hash file.txt              # Set console width
do-folder -m hash file.txt                  # Mute warnings
do-folder -t compare /dir1 /dir2             # Show full traceback on errors
```

### Practical Examples

**Backup Verification:**

```bash
# Compare original and backup, sync differences
do-compare /important/data /backup/data --sync --sync-direction A2B --overwrite AUTO
```

**Development Workflow:**

```bash
# Compare two versions of a project
do-compare /project/v1 /project/v2 --compare-mode CONTENT

# Hash all source files for change detection
do-hash -a blake2b -r /src --full-path
```

## �🔧 Advanced Features

### Command-Line Interface

doFolder provides comprehensive command-line tools with two usage modes:

**Unified Interface:**

```bash
# Main command with subcommands
do-folder compare /path/to/dir1 /path/to/dir2 --sync
do-folder hash -a sha256,md5 file1.txt file2.txt

# Using Python module
python -m doFolder compare /source /backup --compare-mode CONTENT
python -m doFolder hash -a blake2b -r /directory
```

**Direct Commands:**

```bash
# Direct command shortcuts
do-compare /path/to/dir1 /path/to/dir2 --sync --overwrite AUTO
do-hash -a sha256,md5 file1.txt file2.txt --thread-num 8
```

#### Compare Command Features

- Multiple comparison modes (SIZE, CONTENT, TIMETAG, TIMETAG_AND_SIZE, IGNORE)
- Directory synchronization with bidirectional support
- Flexible overwrite policies (A2B, B2A, ASK, AUTO, IGNORE)
- Relative timestamp formatting
- Interactive conflict resolution

#### Hash Command Features

- Support for multiple hash algorithms (SHA family, MD5, BLAKE2, SHA3, etc.)
- Multi-threaded processing for performance
- Recursive directory hashing
- Progress tracking with detailed status
- Flexible output formatting

### Advanced Hashing System

doFolder includes a sophisticated hashing system with multiple optimization levels:

```python
from doFolder.hashing import (
    FileHashCalculator,
    ThreadedFileHashCalculator,
    ReCalcHashMode,
    MemoryFileHashManager
)
from concurrent.futures import wait


# Basic calculator with caching
calculator = FileHashCalculator(
    algorithm="sha256",
    useCache=True,
    reCalcHashMode=ReCalcHashMode.TIMETAG  # Only recalc if file modified
)

# Multi-threaded calculator for better performance
with ThreadedFileHashCalculator(threadNum=8) as threaded_calc:
    # Process multiple files concurrently
    futures = [threaded_calc.threadedGet(file) for file in file_list]
    wait(futures)
    results = [future.result() for future in futures]

# Custom cache manager
from doFolder.hashing import LfuMemoryFileHashManager
calculator = FileHashCalculator(
    cacheManager=LfuMemoryFileHashManager(maxSize=1000)
)
```

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
- **Command-Line Interface Guide**: [CLI Documentation](https://do-folder.doc.kuankuan.site/cli.html)
- **GitHub Repository**: [https://github.com/kuankuan2007/do-folder](https://github.com/kuankuan2007/do-folder)
- **Issue Tracker**: [https://github.com/kuankuan2007/do-folder/issues](https://github.com/kuankuan2007/do-folder/issues)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the [MulanPSL-2.0 License](./LICENSE) - see the LICENSE file for details.
