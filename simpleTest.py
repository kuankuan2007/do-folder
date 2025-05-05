from src import doFolder
from src.doFolder import path

print(path.relativePathableFormat(path.Path("a/b/c"), path.Path('./').absolute()))
