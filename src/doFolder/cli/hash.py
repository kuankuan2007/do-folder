"""CLI module for hash calculation functionality.

This module provides command-line interface for calculating hash values of files
using various algorithms with support for progress tracking and parallel processing.
"""

import time
from concurrent.futures import CancelledError
from pathlib import Path

from . import util
from .. import globalType as _tt, exception as _ex, fileSystem as _fs
from .. import hashing as _hashing


def getShortDisplayNames(  # pylint: disable=too-many-branches
    paths: list[Path],
) -> dict[Path, Path]:
    """Generate short display names for paths by resolving conflicts.

    When multiple paths have the same filename, returns progressively longer
    path segments until all names are unique.

    Args:
        paths: List of Path objects to generate display names for.

    Returns:
        Dictionary mapping original paths to their shortened display names.
    """
    if not paths:
        return {}
    pathStrings = [str(path) for path in paths]
    displayNames = [path.name for path in paths]
    nameCounts = {}
    for i, name in enumerate(displayNames):
        if name not in nameCounts:
            nameCounts[name] = []
        nameCounts[name].append(i)
    for name, indices in nameCounts.items():
        if len(indices) > 1:
            conflictingPaths = [paths[i] for i in indices]
            maxDepth = max(len(path.parts) for path in conflictingPaths)
            for depth in range(2, maxDepth + 1):
                tempNames = []
                for path in conflictingPaths:
                    parts = path.parts
                    if len(parts) >= depth:
                        tempName = str(Path(*parts[-depth:]))
                    else:
                        tempName = str(path)
                    tempNames.append(tempName)
                if len(set(tempNames)) == len(tempNames):
                    for i, tempName in enumerate(tempNames):
                        displayNames[indices[i]] = tempName
                    break
            else:
                for i in indices:
                    displayNames[i] = pathStrings[i]
    return dict(zip(paths, (Path(i) for i in displayNames)))


Algorithm = str
FIELDS_INIT = {
    "_now": "0B",
    "_total": "N/A",
    "_percent": "0.00%",
    "_file": "",
    "_speed": "N/A",
    "_statue": util.TaskStatus.WAITING,
    "_remainTime": "N/A",
}
STATUE_MAP = {
    util.TaskStatus.WAITING: util.rich.text.Text("Waiting", style="bold"),
    util.TaskStatus.RUNNING: util.rich.text.Text("Running", style="blue bold"),
    util.TaskStatus.CANCELED: util.rich.text.Text("Canceled", style="red bold"),
    util.TaskStatus.FAILED: util.rich.text.Text("Failed", style="red bold"),
    util.TaskStatus.COMPLETED: util.rich.text.Text("Completed", style="green bold"),
}


class AlgorithmFilesAction(util.argparse.Action):
    """Custom argparse action for handling algorithm and file combinations.

    Parses command-line arguments in the format: algorithms,... file1 file2 ...
    where algorithms is a comma-separated list of hash algorithms.
    """

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs == 0:
            raise ValueError('nargs for AlgorithmFilesAction must be "+" or "*"')
        super().__init__(option_strings, dest, nargs="+", **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):

        if not hasattr(namespace, self.dest) or getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, [])

        if not values:
            return

        valueList = (
            [str(v) for v in values]
            if hasattr(values, "__iter__") and not isinstance(values, str)
            else [str(values)]
        )
        algorithmsStr = valueList[0]
        algorithms = [alg.strip() for alg in algorithmsStr.split(",")]
        files = valueList[1:] if len(valueList) > 1 else []

        getattr(namespace, self.dest).append((algorithms, files))


def hashCli(arguments: _tt.Optional[_tt.Sequence[str]] = None, prog=None) -> int:
    """Main CLI function for hash calculation commands.

    Args:
        arguments: Optional sequence of command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = util.argparse.ArgumentParser(
        description="Calculate hash values for files using specified algorithms",
        prog=prog,
    )
    util.addVersionInfo(parser)

    # 使用自定义的Action来处理 -a 参数和后续的文件列表

    parser.add_argument(
        "-a",
        "--algorithms",
        action=AlgorithmFilesAction,
        dest="algorithm_groups",
        metavar=("ALGORITHMS", "FILES"),
        help="Specify algorithms (comma-separated) followed by files. Can be used multiple times. "
        "Example: -a sha1,md5 file1.txt file2.txt",
    )
    parser.add_argument(
        "default_groups",
        nargs="*",
        help=f"Calculate hashes using default algorithms({_hashing.DEFAULT_HASH_ALGORITHM}) for specified files.",
    )
    parser.add_argument(
        "-d",
        "--allow-directory",
        action="store_true",
        help="Allow hashing of directories",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively hash all subdirectories",
    )

    parser.add_argument(
        "-A",
        "--disable-aggregate-algos",
        action="store_false",
        help="Disable aggregate algorithms",
    )
    parser.add_argument(
        "-p", "--to-absolute", action="store_true", help="Use absolute paths"
    )
    parser.add_argument(
        "-f",
        "--full-path",
        action="store_true",
        help="Display the full path in all circumstances",
    )
    parser.add_argument(
        "-s",
        "--show-all",
        action="store_true",
        help="Display all progress bars in any situation.",
    )
    parser.add_argument("-n", "--thread-num", type=int, default=4)
    parser.add_argument("--no-progress", action="store_true", help="Show result only")
    util.addConsoleInfo(parser)

    args = parser.parse_args(arguments)

    groupsFromArgs: HashGroup = []

    if args.algorithm_groups:
        groupsFromArgs.extend(args.algorithm_groups)
    if args.default_groups:
        groupsFromArgs.append(([_hashing.DEFAULT_HASH_ALGORITHM], args.default_groups))

    fileFlag = any(len(files) > 0 for _, files in groupsFromArgs)

    if not fileFlag:
        parser.error("No files specified, nothing to do. Use -h for help.")

    return _hashCli(
        groupsFromArgs,
        allowDirectory=args.allow_directory,
        recursive=args.recursive,
        disableAggregateAlgos=args.disable_aggregate_algos,
        toAbsolute=args.to_absolute,
        controller=util.createControllerFromArgs(args),
        threadNum=args.thread_num,
        fullPath=args.full_path,
        showAll=args.show_all,
        noProgress=args.no_progress,
    )


HashGroup = list[tuple[list[Algorithm], list[str]]]

FlatHashGroup = list[tuple[_fs.Path, set[Algorithm]]]

FinalHashGroup = list[tuple[_fs.File, set[Algorithm]]]


def _flatHashGroup(group: HashGroup) -> FlatHashGroup:
    res: FlatHashGroup = []
    for algorithms, path in group:
        _algorithms = set(algorithms)
        for i in path:
            res.append((_fs.Path(i), _algorithms))
    return res


def _toAbsolute(flatGroup: FlatHashGroup):
    return [(_fs.Path(path).absolute(), algorithms) for path, algorithms in flatGroup]


def _aggregateAlgos(flatGroup: FlatHashGroup) -> FlatHashGroup:
    cache: dict[_fs.Path, set[str]] = {}
    for path, algorithms in flatGroup:
        if path in cache:
            cache[path].update(algorithms)
        else:
            cache[path] = set(algorithms)
    return list(cache.items())


def _checkPath(
    flatGroup: FlatHashGroup,
    *,
    controller: util.ConsoleController,
    showNames: dict[Path, Path],
    allowDirectory: bool = False,
    recursive: bool = False,
):
    firstWarn = True
    res: FinalHashGroup = []
    for path, algorithms in flatGroup:
        item = _fs.createItem(path, unExistsMode=_fs.UnExistsMode.ERROR)
        if _fs.isFile(item):
            res.append((item, algorithms))
            continue
        if not allowDirectory:
            if firstWarn:
                firstWarn = False
                controller.warn(
                    "Some paths are directories. If you want to expand their contents, use the -d option. To expand recursively, add the -r option."
                )
        for i in (
            item.recursiveTraversal(hideDirectory=True)
            if recursive
            else (i for i in item if _fs.isFile(i))
        ):
            res.append((i, algorithms))
            showNames[i.path] = showNames.get(path, path) / i.path.relative_to(path)
    return res


def _checkAlgorithms(group: HashGroup):
    res = _hashing.unsupport(set(item for i, _ in group for item in i))
    if res:
        raise ValueError("Unsupported hash algorithm(s): " + ",".join(res))


_taskIdGenerator = util.idGenerator()


@util.dataclass
class CalcTask:
    """Represents a hash calculation task with progress tracking.

    Attributes:
        feature: Future object with progress tracking for the calculation.
        result: The result of the hash calculation, if completed.
        file: The file being hashed.
        algorithms: Set of hash algorithms to apply.
        id: Unique identifier for the task.
    """

    feature: _hashing.FutureWithProgress[_hashing.MultipleHashResult]
    result: _tt.Optional[_hashing.MultipleHashResult]
    file: _fs.File
    algorithms: set[str]
    showName: str
    id: int = util.field(default_factory=_taskIdGenerator.__next__)

    @property
    def fields(self):
        """Get formatted field values for progress display.

        Returns:
            Dictionary of formatted fields for progress bar display.
        """
        return {
            "_now": util.SizeFormat(self.feature.progress),
            "_total": util.SizeFormat(self.feature.total),
            "_percent": f"{self.feature.percent:0.2f}%",
            "_file": self.file.path,
            "_speed": util.SizeSpeedFormat(self.feature.speed),
            "_statue": STATUE_MAP[self.feature.statue],
            "_remainTime": util.TimeFormat(self.feature.remain),
        }


class CalcProgress(util.rich.progress.Progress):
    """Progress tracker for hash calculation tasks.

    Extends Rich Progress to provide custom progress tracking for multiple
    concurrent hash calculation tasks with detailed status information.
    """

    taskList: list[CalcTask]
    taskMap: dict[int, util.rich.progress.TaskID]
    showRunningOnly: bool = False

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        consoleController: util.ConsoleController,
        auto_refresh: bool = True,
        refresh_per_second: float = 3,
        speed_estimate_period: float = 30,
        transient: bool = False,
        redirect_stdout: bool = True,
        redirect_stderr: bool = True,
        get_time: _tt.Callable[[], float] | None = None,
        disable: bool = False,
        expand: bool = False,
        showRunningOnly: bool = False,
    ) -> None:

        super().__init__(
            *[
                util.rich.progress.TextColumn(
                    "[progress.description]{task.description}",
                ),
                util.rich.progress.BarColumn(),
                util.rich.progress.TextColumn("{task.fields[_now]}", justify="right"),
                util.rich.progress.TextColumn("/"),
                util.rich.progress.TextColumn("{task.fields[_total]}", justify="left"),
                util.rich.progress.TextColumn(
                    "{task.fields[_percent]}", style="blue", justify="right"
                ),
                util.rich.progress.TextColumn("{task.fields[_speed]}", style="green"),
                util.rich.progress.TextColumn(
                    "{task.fields[_remainTime]}", style="yellow"
                ),
                util.rich.progress.TextColumn("{task.fields[_statue]}"),
            ],
            console=consoleController.console,
            auto_refresh=auto_refresh,
            refresh_per_second=refresh_per_second,
            speed_estimate_period=speed_estimate_period,
            transient=transient,
            redirect_stdout=redirect_stdout,
            redirect_stderr=redirect_stderr,
            get_time=get_time,
            disable=disable,
            expand=expand,
        )

        self.taskList = []
        self.taskMap = {}
        self.showRunningOnly = showRunningOnly

    def traceTask(self, *args: CalcTask):
        """Add tasks to be tracked by this progress instance.

        Args:
            *args: CalcTask instances to track.
        """
        self.taskList.extend(args)

    def getTaskId(self, task: CalcTask) -> util.rich.progress.TaskID:
        """Get or create a Rich progress task ID for a CalcTask.

        Args:
            task: The CalcTask to get an ID for.

        Returns:
            Rich progress TaskID for the given task.
        """
        if task.id not in self.taskMap:
            self.taskMap[task.id] = self.add_task(
                description=str(task.showName),
                completed=0,
                start=True,
                total=None,
                visible=not self.showRunningOnly,
                **FIELDS_INIT,
            )
        return self.taskMap[task.id]

    def updateTask(
        self,
        task: CalcTask,
    ):
        """Update progress display for a specific task.

        Args:
            task: The CalcTask to update progress for.
        """
        self.update(
            self.getTaskId(task),
            description=str(task.file.path),
            advance=None,
            total=task.feature.total,
            completed=task.feature.progress,
            refresh=False,
            visible=(
                (task.feature.statue == util.TaskStatus.RUNNING)
                if self.showRunningOnly
                else True
            ),
            **task.fields,
        )

    def refreshCalcTask(self) -> None:
        """Refresh progress display for all tracked tasks."""

        for i in self.taskList:
            self.updateTask(i)


def _hashCli(  # pylint: disable=too-many-arguments, too-many-locals
    hashGroups: HashGroup,
    *,
    controller: util.ConsoleController,
    allowDirectory: bool = False,
    recursive: bool = False,
    disableAggregateAlgos: bool = True,
    toAbsolute: bool = False,
    threadNum: int = 4,
    fullPath: bool = False,
    showAll: bool = False,
    noProgress: bool = False,
) -> int:

    try:

        _checkAlgorithms(hashGroups)
        flatGroup = _flatHashGroup(hashGroups)

        if toAbsolute:
            flatGroup = _toAbsolute(flatGroup)
        if not disableAggregateAlgos:
            flatGroup = _aggregateAlgos(flatGroup)

        showNames = (
            {i: i for i, _ in flatGroup}
            if fullPath
            else getShortDisplayNames([i for i, _ in flatGroup])
        )

        finalGroup = _checkPath(
            flatGroup,
            controller=controller,
            showNames=showNames,
            allowDirectory=allowDirectory,
            recursive=recursive,
        )

        with CalcProgress(
            consoleController=controller,
            showRunningOnly=not showAll,
            disable=noProgress,
        ) as progress, _hashing.ThreadedFileHashCalculator(
            threadNum=threadNum
        ) as calculator:
            calcTasks = [
                CalcTask(
                    feature=calculator.threadedMultipleGet(file, algorithms),
                    result=None,
                    file=file,
                    algorithms=algorithms,
                    showName=str(showNames[file.path]),
                )
                for file, algorithms in finalGroup
            ]
            progress.traceTask(*calcTasks)
            while True:
                flag = True
                for i in calcTasks:

                    flag = flag and i.feature.done()
                progress.refreshCalcTask()
                if flag:
                    break
                time.sleep(0.1)

        for i in calcTasks:
            try:
                res = i.feature.result()
                controller.console.print(
                    util.rich.text.Text(f"\n{i.file.path}", style="bold green"),
                    markup=False,
                )
                for algo, res in res.items():
                    controller.console.print(
                        util.rich.text.Text(f"{algo}", style="bold blue"),
                        util.rich.text.Text(f" {res.hash}"),
                        markup=False,
                    )

            except CancelledError:
                controller.console.print(
                    f"Task {i.file.path} was cancelled.",
                    style=util.rich.style.Style(color="yellow"),
                    markup=False,
                )
                continue
            except BaseException as e:  # pylint: disable=broad-exception-caught
                controller.expHook(e)
                continue

    except BaseException as e:  # pylint: disable=broad-exception-caught
        controller.expHook(e)
        return -1
    return 0
