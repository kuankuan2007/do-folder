"""
Utility functions and constants for the doFolder CLI module.

This module provides common utilities used across different CLI components,
including version information handling and argument parser configuration.
"""

# pylint: disable=unused-import
import argparse
from dataclasses import dataclass, field

import rich
import rich.console
import rich.table
import rich.prompt
import rich.progress
import rich.text
import rich.style


from .. import env as _env, __pkginfo__ as _pkginfo, exception as _ex, globalType as _tt


console = rich.get_console()

#: Short version string containing package name and version
VERSION_STRING = f"{_pkginfo.__pkgname__} {_pkginfo.__version__}"

#: Full version string including Python version and executable path
FULL_VERSION_STRING = f"{_pkginfo.__pkgname__} {_pkginfo.__version__} From Python {_env.PYTHON_VERSION_STR}({_env.PYTHON_EXECUTABLE})"


def addVersionInfo(parser: argparse.ArgumentParser):
    """
    Add version information arguments to an ArgumentParser.

    This function adds two version-related arguments:
    - `-v, --version`: Shows short version information
    - `-vv, --full-version`: Shows detailed version information including Python details

    Args:
        parser (argparse.ArgumentParser): The argument parser to add version info to.

    Example:
        >>> parser = argparse.ArgumentParser()
        >>> addVersionInfo(parser)
        >>> # Parser now has -v/--version and -vv/--full-version arguments
    """
    parser.add_argument("-v", "--version", action="version", version=VERSION_STRING)
    parser.add_argument(
        "-vv", "--full-version", action="version", version=FULL_VERSION_STRING
    )


def addConsoleInfo(parser: argparse.ArgumentParser):
    """Add console information arguments to an ArgumentParser."""
    parser.add_argument(
        "-w", "--mute-warning", action="store_true", help="Mute warning messages"
    )
    parser.add_argument(
        "-t",
        "--traceback",
        action="store_true",
        help="Show traceback information when an error occurs",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output in the console (useful for piping output to files or other commands)",
    )


def createControllerFromArgs(args: argparse.Namespace):
    return ConsoleController(
        traceback=args.traceback, noColor=args.no_color, muteWarning=args.mute_warning
    )


@dataclass
class ConsoleController:
    traceback: bool
    noColor: bool
    muteWarning: bool = False
    console: rich.console.Console = console

    def __post_init__(self):
        """Initialize cache manager if not provided."""
        self.console.no_color = self.noColor
        self.console.legacy_windows = self.noColor

    def expHook(
        self,
        e: BaseException,
    ):
        excType = e.__class__

        if self.traceback:
            self.console.print_exception(show_locals=True, max_frames=5, extra_lines=2)
        else:
            self.console.print(
                f"Error: {excType.__name__}",
                style=rich.style.Style(color="red", bold=True),
                markup=False,
            )
            self.console.print(
                str(e),
                highlight=False,
                style=rich.style.Style(color="red"),
                markup=False,
            )
            notes = _ex.getNote(e)
            if notes:
                self.console.print("\n")
                for note in notes:
                    self.console.print(f"[green bold]Note:[/bold green] {note}")

    def warn(self, content: str):
        if not self.muteWarning:
            self.console.print(
                "WARN: " + content,
                style=rich.style.Style(color="yellow"),
                highlight=False,
                markup=False,
            )


def idGenerator():
    i = 1
    while True:
        yield i
        i += 1


class UnitShow:
    unitNames: list[tuple[int, str]]
    noneName: str

    def __init__(self, unitNames: list[tuple[int, str]], noneName: str = "N/A") -> None:
        self.unitNames = unitNames
        self.noneName = noneName

    def __call__(self, value: _tt.Optional[float]) -> str:
        if value is None:
            return self.noneName

        lastUnit = self.unitNames[0][1]
        for unit in self.unitNames:
            if value >= unit[0] * 1.3:
                value = value / unit[0]
                lastUnit = unit[1]
            else:
                return f"{value:.2f}{lastUnit}"
        return f"{value}{lastUnit}"


TimeFormat = UnitShow([(1, "s"), (60, "min"), (60, "h"), (24, "d")])
SizeFormat = UnitShow(
    [(1, "B"), (1024, "KB"), (1024, "MB"), (1024, "GB"), (1024, "TB"), (1024, "PB")],
)
SizeSpeedFormat = UnitShow(
    [
        (1, "B/s"),
        (1024, "KB/s"),
        (1024, "MB/s"),
        (1024, "GB/s"),
        (1024, "TB/s"),
        (1024, "PB/s"),
    ]
)
