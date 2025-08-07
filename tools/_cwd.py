import sys
from os import chdir
from pathlib import Path

cwd = Path(__file__).parent.parent.absolute()
_lastCwd = None


def initCwd():
    global _lastCwd
    _lastCwd = Path.cwd()
    chdir(cwd)


def resetCwd():
    global _lastCwd
    if _lastCwd is not None:
        chdir(_lastCwd)
        _lastCwd = None
    else:
        raise RuntimeError("No previous working directory to reset to.")


def initSysPath():
    sys.path.append(str(cwd))


def resetSysPath():
    if str(cwd) in sys.path:
        sys.path.remove(str(cwd))
