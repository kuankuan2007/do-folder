from src import doFolder

a = doFolder.Directory("./") 
a.create("test3", doFolder.CreateType.FILE).content="123456".encode("utf-8")