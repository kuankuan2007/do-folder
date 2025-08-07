# pyint: ignore
from tempfile import gettempdir
import sys
from pathlib import Path
import time
import shutil
import random
from concurrent import futures


def randomString(l=10):
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=l))


def randomFileContent(l=500):
    return "random content:" + randomString(l)


root = Path(gettempdir()) / f"doFolder-simpleTest-{time.time()}"

try:
    root.mkdir(parents=True)
    pkgDir = Path(__file__).parent
    sys.path.insert(0, (str(pkgDir / "src")))
    import doFolder
    import doFolder.hashing

    rootDir = doFolder.Directory("J:/stable-diffusion-webui/models/Stable-diffusion")
    files = rootDir.recursiveTraversal()
    hashCalcer = doFolder.hashing.ThreadedFileHashCalculator(threadNum=16)

    res = [hashCalcer.threadedGet(i) for i in files]

    for i in res:
        i.add_done_callback(
            lambda j: print(
                f"Done: {j.result().path.name} - {j.result().hash}\n", end=""
            )
        )
    futures.wait(res)
finally:
    shutil.rmtree(root, ignore_errors=True)
