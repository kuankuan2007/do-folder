from src.doFolder.scripts import hashCli
import os

os._exit(
    hashCli(
        [
            "-a",
            "md5,sha1",
            "./src",
            "./LICENSE",
            "",
            "-a",
            "sha1,sha256",
            "./README.md",
            "./README.zh-cn.md",
            "-a",
            "md5",
            "./requirements.txt",
            "./requirements_doc.txt",
            "-d",
            "-r",
            "-n",
            "16",
        ]
    )
)
# os._exit(
#     hashCli(
#         [
#             "-a",
#             "md5",
#             "e:/工具包/系统镜像/Windows10(22.2.7).iso",
#             "e:/工具包/系统镜像/Windows10(23.1.1).iso",
#             '--no-color'
#         ]
#     )
# )
