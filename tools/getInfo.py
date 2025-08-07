from dataclasses import dataclass
import _cwd


@dataclass
class VersionInfo:
    version: str
    pkgName: str


def getInfo():
    import importlib
    import sys
    from pathlib import Path

    _cwd.initSysPath()
    sys.path.append(str(Path(__file__).parent.parent))
    pkginfo = importlib.import_module("src.doFolder.__pkginfo__")
    sys.path.remove(str(Path(__file__).parent.parent))
    _cwd.resetSysPath()
    return VersionInfo(version=pkginfo.__version__, pkgName=pkginfo.__pkgname__)
