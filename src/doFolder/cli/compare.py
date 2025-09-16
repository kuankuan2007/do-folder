"""
Define the CLI for doFolder.

.. versionadded:: 2.3.0
"""

# pylint: disable=line-too-long


import datetime
from enum import Enum as _Enum


from . import util


from .. import (
    globalType as _tt,
    fileSystem as _fs,
    compare as _compare,
    exception as _ex,
    sort as _sort,
    env as _env,
    __version__,
    __pkgname__,
)


def compareCli(arguments: _tt.Optional[_tt.Sequence[str]] = None, prog=None) -> int:
    """
    The implementation of the command-line tool `do-compare`
    You can also use it as `do-folder compare` or `python3 -m doFolder compare`.
    """

    parser = util.argparse.ArgumentParser(
        description="Compare two filesystem items.", prog=prog
    )

    util.addVersionInfo(parser)

    parser.add_argument("path_A", type=str, help="Path to the first file")
    parser.add_argument("path_B", type=str, help="Path to the second file")

    parser.add_argument(
        "-C",
        "--compare-mode",
        type=str,
        choices=["SIZE", "CONTENT", "TIMETAG", "TIMETAG_AND_SIZE", "IGNORE"],
        default="TIMETAG_AND_SIZE",
        help="How to compare two files: 'SIZE' for size, 'CONTENT' for content, 'TIMETAG' for timestamp, 'TIMETAG_AND_SIZE' for both, 'IGNORE' to ignore differences'",
    )
    parser.add_argument(
        "-S",
        "--sync",
        action="store_true",
        help="Sync the two directories if they are different",
    )
    parser.add_argument(
        "-D",
        "--sync-direction",
        type=str,
        choices=["BOTH", "A2B", "B2A", "ASK"],
        default="ASK",
        help="Direction of synchronization: 'BOTH' for both directions, 'A2B' for A to B, 'B2A' for B to A, 'ASK' to prompt",
    )
    parser.add_argument(
        "-O",
        "--overwrite",
        nargs="?",
        const="AUTO",
        type=str,
        choices=["A2B", "B2A", "ASK", "AUTO", "IGNORE"],
        default="ASK",
        help="Overwrite mode: 'A2B' for A to B, 'B2A' for B to A, 'ASK' to prompt, 'Ignore' to ignore any overwrites, 'AUTO' to automatically decide by last modified time. Default is ASK, and using the -O parameter alone indicates AUTO.",
    )
    parser.add_argument(
        "--create-root",
        action="store_true",
        help="Create root directory if it does not exist",
    )
    parser.add_argument(
        "-R",
        "--relative-timestamp",
        nargs="?",
        const="ALWAYS",
        type=str,
        choices=["ALWAYS", "NEVER", "AUTO"],
        default="AUTO",
        help="Relative timestamp format: AUTO for automatic detection, ALWAYS for always relative, NEVER for absolute timestamps. Default is AUTO, and using the -r parameter alone indicates ALWAYS.",
    )
    util.addConsoleInfo(parser)

    args = parser.parse_args(arguments)
    return _compareCli(
        pathA=_fs.Path(args.path_A),
        pathB=_fs.Path(args.path_B),
        controller=util.createControllerFromArgs(args),
        compareMode={
            "SIZE": _compare.CompareMode.SIZE,
            "CONTENT": _compare.CompareMode.CONTENT,
            "TIMETAG": _compare.CompareMode.TIMETAG,
            "TIMETAG_AND_SIZE": _compare.CompareMode.TIMETAG_AND_SIZE,
            "IGNORE": _compare.CompareMode.IGNORE,
        }[args.compare_mode],
        sync=args.sync,
        syncDirection=args.sync_direction,
        overwrite=args.overwrite,
        createRoot=args.create_root,
        relativeTimestamp=args.relative_timestamp,
    )


class DiffPlan(_Enum):
    """
    Enum to represent the plan for handling differences.
    """

    PENDING = "Pending"
    PENDING_OVERWRITE = "Pending(Overwrite)"
    IGNORE = "Ignore"
    A2B = "A2B"
    A2B_OVERWRITE = "A2B(Overwrite)"
    B2A = "B2A"
    B2A_OVERWRITE = "B2A(Overwrite)"

    @staticmethod
    def toOverwrite(plan: "DiffPlan") -> "DiffPlan":
        """
        Convert a DiffPlan to its overwrite variant.
        """
        return {
            DiffPlan.PENDING: DiffPlan.PENDING_OVERWRITE,
            DiffPlan.A2B: DiffPlan.A2B_OVERWRITE,
            DiffPlan.B2A: DiffPlan.B2A_OVERWRITE,
        }.get(plan, plan)

    @staticmethod
    def toNonOverwrite(plan: "DiffPlan") -> "DiffPlan":
        """
        Convert a DiffPlan to its non-overwrite variant.
        """
        return {
            DiffPlan.PENDING_OVERWRITE: DiffPlan.PENDING,
            DiffPlan.A2B_OVERWRITE: DiffPlan.A2B,
            DiffPlan.B2A_OVERWRITE: DiffPlan.B2A,
        }.get(plan, plan)

    @staticmethod
    def isPending(plan: "DiffPlan") -> bool:
        """
        Check if the plan is pending or pending overwrite.
        """
        return plan in (DiffPlan.PENDING, DiffPlan.PENDING_OVERWRITE)

    @staticmethod
    def isOverwrite(plan: "DiffPlan") -> bool:
        """
        Check if the plan is overwrite or overwrite variant.
        """
        return plan in (
            DiffPlan.PENDING_OVERWRITE,
            DiffPlan.A2B_OVERWRITE,
            DiffPlan.B2A_OVERWRITE,
        )


def _formatTimestamp(
    target: datetime.datetime,
    base: datetime.datetime = datetime.datetime.now(),
    relativeTimestamp: _tt.Literal["ALWAYS", "NEVER", "AUTO"] = "AUTO",
) -> str:
    """Format a timestamp into a human-readable string."""
    delta = target - base
    seconds = int(delta.total_seconds())
    absSeconds = abs(seconds)

    intervals = [
        ("year", 365 * 24 * 60 * 60),
        ("month", 30 * 24 * 60 * 60),
        ("day", 24 * 60 * 60),
        ("hour", 60 * 60),
        ("minute", 60),
        ("second", 1),
    ]

    _useRelative = (
        (absSeconds < 365 * 24 * 60 * 60)
        if relativeTimestamp == "AUTO"
        else (relativeTimestamp == "ALWAYS")
    )
    if _useRelative:
        for name, count in intervals:
            value = absSeconds // count
            if value > 0:
                if value == 1:
                    unit = name
                else:
                    unit = name + "s"
                if seconds < 0:
                    return f"{value} {unit} ago"

                return f"{value} {unit} later"
        return "just now"
    return target.strftime("%Y-%m-%d %H:%M:%S")


def _compareCli(
    pathA: _tt.Path,
    pathB: _tt.Path,
    *,
    controller: util.ConsoleController,
    compareMode: _compare.CompareMode = _compare.CompareMode.TIMETAG_AND_SIZE,
    sync: bool = False,
    syncDirection: _tt.Literal["ASK", "A2B", "B2A", "BOTH"] = "ASK",
    overwrite: _tt.Literal["ASK", "A2B", "B2A", "AUTO"] = "ASK",
    createRoot: bool = False,
    relativeTimestamp: _tt.Literal["ALWAYS", "NEVER", "AUTO"] = "AUTO",
) -> (
    int
):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements, too-many-arguments
    """Compare folders using CLI interface."""

    try:

        itemA: _fs.FileSystemItem
        itemB: _fs.FileSystemItem

        if pathA.exists() and pathB.exists():
            if pathA.is_file() ^ pathB.is_file():
                raise _ex.PathTypeError(
                    "Cannot compare a file with a folder or vice versa."
                )
            itemA = _fs.createItem(pathA)
            itemB = _fs.createItem(pathB)
        elif not pathA.exists() and not pathB.exists():
            raise _ex.PathNotExistsError(
                "Both paths do not exist. Please provide at least one existing path."
            )
        else:
            notExistsPath = pathA if pathB.exists() else pathB
            existsPath = pathB if pathB.exists() else pathA
            if (pathA.is_dir() or pathB.is_dir()) and not createRoot:
                e = _ex.PathTypeError(
                    f"Directory '{notExistsPath}' does not exist, but the other path '{existsPath}' is a directory."
                )
                _ex.addNote(
                    e, "To create it automatically, use -c(--create-root) option."
                )
                raise e
            isFile = pathA.is_file() if pathA.exists() else pathB.is_file()
            itemA = _fs.createItem(
                pathA,
                unExistsMode=_fs.UnExistsMode.CREATE,
                exceptType=_fs.ItemType.FILE if isFile else _fs.ItemType.DIR,
            )
            itemB = _fs.createItem(
                pathB,
                unExistsMode=_fs.UnExistsMode.CREATE,
                exceptType=_fs.ItemType.FILE if isFile else _fs.ItemType.DIR,
            )

        diff = _compare.getDifference(itemA, itemB, compareMode)

        if diff is None:
            controller.console.print("[green]No differences found.[/green]")
            return 0

        diffPlans: dict[int, DiffPlan] = {}

        tableColumns = [
            {"header": "Path"},
            {"header": "Status"},
            {"header": "Type"},
            {"header": "A Last Modified", "justify": "center"},
            {"header": "B Last Modified", "justify": "center"},
        ]
        tableArgs = {
            "title": "Differences",
            "show_header": True,
            "header_style": "bold",
            "show_lines": True,
            "title_justify": "left",
            "title_style": "bold italic",
            "box": util.rich.table.box.HEAVY_HEAD,
        }
        if sync:
            tableColumns.append({"header": "Plan"})

        def toTableData(diff: _compare.Difference):
            _path = diff.path1.relative_to(itemA.path)
            _aLastModified = "-"
            _bLastModified = "-"
            if diff.diffType == _compare.DifferenceType.FILE_DIFFERENCE:
                _statue = "File Different"
                _type = "File"
                _aLastModified = _formatTimestamp(
                    datetime.datetime.fromtimestamp(diff.path1.stat().st_mtime),
                    relativeTimestamp=relativeTimestamp,
                )
                _bLastModified = _formatTimestamp(
                    datetime.datetime.fromtimestamp(diff.path2.stat().st_mtime),
                    relativeTimestamp=relativeTimestamp,
                )
            elif diff.diffType == _compare.DifferenceType.ITEM_TYPE_DIFFERENCE:
                _statue = "Type Different"
                _type = (
                    ("F" if diff.path1.is_file() else "D")
                    + "/"
                    + ("F" if diff.path2.is_file() else "D")
                )
                _aLastModified = _formatTimestamp(
                    datetime.datetime.fromtimestamp(diff.path1.stat().st_mtime),
                    relativeTimestamp=relativeTimestamp,
                )
                _bLastModified = _formatTimestamp(
                    datetime.datetime.fromtimestamp(diff.path2.stat().st_mtime),
                    relativeTimestamp=relativeTimestamp,
                )
            elif diff.diffType == _compare.DifferenceType.NOT_EXISTS:
                if diff.path1.exists():
                    _statue = "A only"
                    _type = "File" if diff.path1.is_file() else "Directory"
                    _aLastModified = _formatTimestamp(
                        datetime.datetime.fromtimestamp(diff.path1.stat().st_mtime),
                        relativeTimestamp=relativeTimestamp,
                    )
                else:
                    _statue = "B only"
                    _type = "File" if diff.path2.is_file() else "Directory"
                    _bLastModified = _formatTimestamp(
                        datetime.datetime.fromtimestamp(diff.path2.stat().st_mtime),
                        relativeTimestamp=relativeTimestamp,
                    )
            else:
                raise ValueError(f"Unknown difference type: {diff.diffType}")
            items = [
                str(_path),
                _statue,
                _type,
                _aLastModified,
                _bLastModified,
            ]
            if sync:
                items.append(str(diffPlans[id(diff)].value))
            return tuple(items)

        def getDefaultPlan(  # pylint: disable=too-many-return-statements, too-many-branches
            diff: _compare.Difference,
        ) -> DiffPlan:
            if diff.diffType == _compare.DifferenceType.NOT_EXISTS:
                if syncDirection == "BOTH":
                    return DiffPlan.A2B if diff.path1.exists() else DiffPlan.B2A
                if syncDirection == "A2B":
                    return DiffPlan.A2B if diff.path1.exists() else DiffPlan.IGNORE
                if syncDirection == "B2A":
                    return DiffPlan.B2A if diff.path2.exists() else DiffPlan.IGNORE
                return DiffPlan.PENDING
            if diff.diffType in (
                _compare.DifferenceType.ITEM_TYPE_DIFFERENCE,
                _compare.DifferenceType.FILE_DIFFERENCE,
            ):
                if syncDirection == "ASK":
                    return DiffPlan.PENDING_OVERWRITE
                if syncDirection == "BOTH":
                    if overwrite == "A2B":
                        return DiffPlan.A2B_OVERWRITE
                    if overwrite == "B2A":
                        return DiffPlan.B2A_OVERWRITE
                    if overwrite == "AUTO":
                        return (
                            DiffPlan.A2B_OVERWRITE
                            if diff.path1.stat().st_mtime > diff.path2.stat().st_mtime
                            else DiffPlan.B2A_OVERWRITE
                        )
                    if overwrite == "IGNORE":
                        return DiffPlan.IGNORE
                    return DiffPlan.PENDING_OVERWRITE

                if syncDirection == "A2B":
                    if overwrite in ("A2B", "AUTO"):
                        return DiffPlan.A2B_OVERWRITE
                    return DiffPlan.PENDING_OVERWRITE
                if syncDirection == "B2A":
                    if overwrite in ("B2A", "AUTO"):
                        return DiffPlan.B2A_OVERWRITE
                    return DiffPlan.PENDING_OVERWRITE

            return DiffPlan.PENDING

        def showTable():
            _table = util.rich.table.Table(
                *(util.rich.table.Column(**_tt.cast(_tt.Any, i)) for i in tableColumns),
                **tableArgs,
            )
            for item in diffList:
                _table.add_row(*toTableData(item))
            controller.console.print(_table)

        diffList = [
            i
            for i in diff.toFlat()
            if i.diffType != _compare.DifferenceType.DIRECTORY_DIFFERENCE
        ]
        diffList.sort(key=lambda i: _sort.KeyPath(i.path1.relative_to(itemA.path)))

        def getPlan(diff: _compare.Difference) -> DiffPlan:
            return diffPlans[id(diff)]

        def setPlan(diff: _compare.Difference, plan: DiffPlan):
            diffPlans[id(diff)] = plan

        if sync:
            for item in diffList:

                setPlan(item, getDefaultPlan(item))

        showTable()

        if not sync:
            controller.console.print(
                f"[yellow]There are {len(diffList)} differences found. Use -S(--sync) to sync them[/yellow]"
            )
            return 0

        pendingFlag = False

        def hasPending() -> bool:
            """
            Check if there are any pending items in the diff plans.
            """
            return any(DiffPlan.isPending(getPlan(diff)) for diff in diffList)

        isFirst = True
        while True:
            if not isFirst:
                showTable()
            isFirst = False

            pendingFlag = hasPending()
            editFlag = False
            if not pendingFlag:
                editFlag = not util.rich.prompt.Confirm.ask(
                    "[green]Is these sync plan all correct? [/green]",
                )
                if not editFlag:
                    overwriteList: list[_fs.Path] = []
                    for i in diffList:
                        if diffPlans[id(i)] == DiffPlan.A2B_OVERWRITE:
                            overwriteList.append(i.path2)
                        elif diffPlans[id(i)] == DiffPlan.B2A_OVERWRITE:
                            overwriteList.append(i.path1)
                    if overwriteList:
                        controller.console.print(
                            f"[yellow bold]Warning:[/yellow bold] {len(overwriteList)} items will be overwritten."
                        )
                        for item in overwriteList:
                            controller.console.print(f"[blue]'{item}'[/blue]")
                        editFlag = not util.rich.prompt.Confirm.ask(
                            "[green]Do you want to continue? [/green]",
                            default=True,
                        )
                    if not editFlag:
                        break
            for item in diffList:
                if DiffPlan.isPending(getPlan(item)) or editFlag:
                    res = util.rich.prompt.Prompt.ask(
                        (
                            f"[green]What to do with [blue]'{item.path1.relative_to(itemA.path)}'[/blue]? [/green]"
                            + (
                                "\n[yellow][bold]Warning:[/bold] The file will be overwritten![/yellow]"
                                if DiffPlan.isOverwrite(getPlan(item))
                                else ""
                            )
                        ),
                        choices=[
                            "A2B",
                            "B2A",
                            "Ignore",
                        ],
                        default=(
                            "Ignore"
                            if DiffPlan.isPending(getPlan(item))
                            else DiffPlan.toNonOverwrite(getPlan(item)).value
                        ),
                        console=controller.console,
                        case_sensitive=False,
                    )
                    resPlan = DiffPlan(res)
                    setPlan(
                        item,
                        (
                            DiffPlan.toOverwrite(resPlan)
                            if DiffPlan.isOverwrite(getPlan(item))
                            else resPlan
                        ),
                    )
        ignoreRes: list[_compare.Difference] = []
        syncRes: list[_compare.Difference] = []
        overwriteRes: list[_compare.Difference] = []

        def _syncPath(
            fr: _fs.Path, to: _fs.Path, overwrite: bool, diff: _compare.Difference
        ):
            if not fr.exists():
                raise _ex.PathNotExistsError(
                    f"Cannot sync from '{fr}' to '{to}': source path does not exist."
                )
            if to.exists() and not overwrite:
                controller.console.print(
                    f"[yellow bold]Warning:[/bold] In order to synchronize {fr}, another item needs to be overwritten. However, Overwrite is not specified in the Plan, and we will ignore it"
                )
                ignoreRes.append(diff)
                return
            if to.exists():
                _fs.createItem(to).delete()
                overwriteRes.append(diff)
            controller.console.print(
                f"[green]Syncing [blue]'{fr}'[/blue] to [blue]'{to}'[/blue][/green]"
            )
            syncRes.append(diff)
            _fs.createItem(fr).copy(to)

        for item in diffList:
            plan = getPlan(item)
            if plan == DiffPlan.IGNORE:
                ignoreRes.append(item)
                continue
            if DiffPlan.isPending(plan):
                ignoreRes.append(item)
                controller.console.print(
                    f"[yellow bold]Warning:[/bold] There are still pending items ‘{diff.path1.relative_to(itemA.path)}’. We will ignore it.[/yellow]"
                )
                continue
            if plan in (DiffPlan.A2B, DiffPlan.A2B_OVERWRITE):
                _syncPath(item.path1, item.path2, DiffPlan.isOverwrite(plan), item)
            elif plan in (DiffPlan.B2A, DiffPlan.B2A_OVERWRITE):
                _syncPath(item.path2, item.path1, DiffPlan.isOverwrite(plan), item)
            else:
                raise ValueError(f"Unknown plan: {plan}")
        controller.console.print(
            f"[green]Sync completed. {len(syncRes)} items synced, {len(ignoreRes)} items ignored, {len(overwriteRes)} items overwritten.[/green]"
        )
        return 0
    except BaseException as e:  # pylint: disable=broad-exception-caught
        controller.expHook(e)
        return -1
