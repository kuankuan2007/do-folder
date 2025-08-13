# pylint: disable=unused-import, no-name-in-module
import sys as _sys

PYTHON_VERSION_INFO = _sys.version_info
PYTHON_VERSION_STR = _sys.version
PYTHON_EXECUTABLE = _sys.executable

PYTHON_GIL_DISABLED = (
    not _sys._is_gil_enabled() if hasattr(_sys, "_is_gil_enabled") else False  # pylint: disable=protected-access
)
