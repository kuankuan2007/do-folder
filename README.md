# doFolder

`doFolder` is a simple and universal one-stop file/directory manager.

## Change From v1.\*.\*

- Manage the path using the built-in pathlib
- Change the class name from `Folder` to `Directory`(Maintain compatibility with the name `Folder` is still retained)
- When creating the `File` class, redirection to `Directory` is allowed

## Installation

```shell
pip install doFolder
```

## Usage

### File

```python
from doFolder import File, Directory

d1=Directory("path/to/directory")
f1=File("path/to/file")

# Create a file in the directory
f2=d1.create("new_file.txt")

# Move / Copy / Delete

f1.copy("path/to/new_directory")
f1.move("path/to/new_directory_1")

f1.delete()
```

## Open Source

The paackage is open source under [MulanPSL-2.0 license](./LICENSE)
