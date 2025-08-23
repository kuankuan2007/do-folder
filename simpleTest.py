from src.doFolder.scripts import hashCli
import os

os._exit(
    hashCli(
        [
            "-a",
            "md5",
            "e:/工具包/系统镜像/Windows10(22.2.7).iso",
            "e:/工具包/系统镜像/Windows10(23.1.1).iso",
            '--no-color'
        ]
    )
)
