# doFolder

`doFolder` 是一个简单且通用的一站式文件/目录管理工具。

## v1.\*.\* 的变更

- 使用内置的 `pathlib` 管理路径
- 将类名从 `Folder` 更改为 `Directory`（仍然保留对 `Folder` 名称的兼容性）
- 在创建 `File` 类时，允许重定向到 `Directory`

## 安装

```shell
pip install doFolder
```

## 使用方法

### 文件操作

```python
from doFolder import File, Directory

d1 = Directory("path/to/directory")
f1 = File("path/to/file")

# 在目录中创建一个文件
f2 = d1.create("new_file.txt")

# 移动 / 复制 / 删除

f1.copy("path/to/new_directory")
f1.move("path/to/new_directory_1")

f1.delete()
```

## 开源

该包在 [MulanPSL-2.0 许可证](./LICENSE) 下开源。
