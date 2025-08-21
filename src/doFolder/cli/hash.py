from . import util
from .. import globalType as _tt, exception as _ex, fileSystem as _fs
from .. import hashing as _hashing


Algorithm = str


class AlgorithmFilesAction(util.argparse.Action):
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


def hashCli(arguments: _tt.Optional[_tt.Sequence[str]] = None):
    parser = util.argparse.ArgumentParser(
        description="Calculate hash values for files using specified algorithms",
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
    util.addConsoleInfo(parser)

    args = parser.parse_args(arguments)

    groupsFromArgs: HashGroup = []

    if args.algorithm_groups:
        groupsFromArgs.extend(args.algorithm_groups)
    if args.default_groups:
        groupsFromArgs.append(([_hashing.DEFAULT_HASH_ALGORITHM], args.default_groups))

    return _hashCli(
        groupsFromArgs,
        allowDirectory=args.allow_directory,
        recursive=args.recursive,
        disableAggregateAlgos=args.disable_aggregate_algos,
        toAbsolute=args.to_absolute,
        controller=util.createControllerFromArgs(args),
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
        res.extend(
            (i, algorithms)
            for i in (
                item.recursiveTraversal(hideDirectory=True)
                if recursive
                else (i for i in item if _fs.isFile(i))
            )
        )
    return res


def _checkAlgorithms(group: HashGroup):
    res = _hashing.unsupport(set(item for i, _ in group for item in i))
    if res:
        raise ValueError("Unsupported hash algorithm(s): " + ",".join(res))


def _hashCli(
    hashGroups: HashGroup,
    *,
    controller: util.ConsoleController,
    allowDirectory: bool = False,
    recursive: bool = False,
    disableAggregateAlgos: bool = True,
    toAbsolute: bool = False,
) -> (
    int
):  # pylint: disable=too-many-arguments

    try:

        _checkAlgorithms(hashGroups)

        flatGroup = _flatHashGroup(hashGroups)
        if toAbsolute:
            flatGroup = _toAbsolute(flatGroup)
        if not disableAggregateAlgos:
            flatGroup = _aggregateAlgos(flatGroup)

        finalGroup = _checkPath(
            flatGroup,
            controller=controller,
            allowDirectory=allowDirectory,
            recursive=recursive,
        )
        print(finalGroup)
    except BaseException as e:  # pylint: disable=broad-exception-caught
        controller.expHook(e)
        return -1
    return 0
