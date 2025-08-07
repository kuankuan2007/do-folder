# doFolder

`doFolder` 是一个简单且通用的一站式文件/目录管理工具。

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
