"""
Copyright (c) 2023 Gou Haoming
doFolder is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
         http://license.coscl.org.cn/MulanPSL2
THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
See the Mulan PSL v2 for more details.
"""
import doFolder
import doFolder.compare as comp
from rich.console import Console
from rich.table import Table, Column
from rich.style import Style
import datetime
import sys
from typing import List, Union, Set
import os
import re


def doCompare(commandArgs: Union[List[str], None] = None):
    import argparse

    statueColorMapping = {
        "copied": "green",
        "removed": "red",
        "waiting": "yellow",
        "overwrited": "cyan",
    }
    statueMapping = {
        i: f"[{statueColorMapping[i]}]{i}[/{statueColorMapping[i]}]"
        for i in statueColorMapping
    }
    argparser = argparse.ArgumentParser()
    argparser.add_argument("folder1", type=str, help="The first folder to compare")
    argparser.add_argument("folder2", type=str, help="The second folder to compare")
    argparser.add_argument(
        "-c",
        "--content",
        type=str,
        choices=[
            "ignore",
            "md5",
            "sha1",
            "sha256",
            "sha512",
            "hash",
            "content",
            "size",
        ],
        default="ignore",
        help="How to compare the content of the file",
    )
    argparser.add_argument(
        "-t", "--threaded", action="store_true", help="Use multithreaded scanning"
    )
    argparser.add_argument(
        "-n", "--num", type=int, default=10, help="Maximum number of threads"
    )
    args = argparser.parse_args(commandArgs)
    folder1 = doFolder.Folder(args.folder1)
    folder2 = doFolder.Folder(args.folder2)
    retsult = comp.compare(folder1, folder2, args.content, args.threaded, args.num)
    fileMissingList = retsult.fileMissingList
    folderMissingList = retsult.folderMissingList
    fileDifferentList = retsult.fileDifferentList
    console = Console()
    all: List[Union[comp.FileMissing, comp.FolderMissing, comp.FileDifferent]] = []
    errSum: int = 0
    result: List = []

    class TableAttr:
        data: str
        name: str
        color: Union[str, None] = None

        def __init__(
            self, name: str, data: str, color: Union[str, None] = None
        ) -> None:
            self.data = data
            self.color = color
            self.name = name

    class TableRow:
        def __init__(self, *args: TableAttr, id: int, table: Table) -> None:
            self.items = args
            self.table = table
            self.id = id
            table.add_row(
                *[
                    (i.data if i.color is None else f"[{i.color}]{i.data}[/{i.color}]")
                    for i in self.items
                ]
            )
            rows.append(self)

    rows: List[TableRow] = []

    def doCommand(command: str):
        nonlocal errSum, result

        def chooserParser(chooser: str):
            def shorthandParser(shorthand: str):
                r = re.compile(r"^(\S+)(?: (.+))?$").findall(shorthand)
                if not r:
                    raise ValueError(f"'{shorthand}' is not the right shorthand")
                func = r[0][0].lower()
                args: List[str] = [
                    i.replace("\\,", ",") for i in re.split(r"(?<!\\),", r[0][1])
                ]

                print(func, args)
                if func == "r":
                    return range(*[int(i) for i in args])
                if func == "m":
                    if len(args) != 2:
                        raise ValueError(f"'{func}' must have 2 arguments")
                    res = set()
                    for i in rows:
                        for j in i.items:
                            if (
                                j.name.lower() == args[0].lower()
                                and str(j.data) == args[1]
                            ):
                                res.add(i.id)
                    return res
                if func == "mr":
                    if len(args) != 2:
                        raise ValueError(f"'{func}' must have 2 arguments")
                    res = set()
                    for i in rows:
                        for j in i.items:
                            if j.name.lower() == args[0].lower() and re.match(
                                args[1], str(j.data)
                            ):
                                res.add(i.id)
                    return res
                raise ValueError(f"Cannot find the shorthand '{func}'")

            if chooser.startswith("#"):
                return shorthandParser(chooser[1:])
            else:
                return eval(
                    chooser,
                    {
                        "all": range(len(rows)),
                        "s": shorthandParser,
                        "rows": rows,
                        "differents": all,
                    },
                    {},
                )

        if len(command) == 0:
            errSum += 1
            return "[red]Null instruction[/red]"
        else:
            commands = command.split(" ")
            title = commands[0]
            chooserStr = " ".join(commands[1:])
        if title.lower() == "cls":
            result = []
            return ""
        if title.lower() == "help":
            errSum = 0
            return """Help:
Command format :[blue] command selector [/blue]
Commands have the following types (case insensitive):
    [green]copy[/green] - Copies the selected project (for missing files/folders)
    [green]del[/green] - Deletes the selected item (for all items)
    [green]choice1[/green] - Select the first to override the second (for files with different contents)
    [green]choice2[/green] - Select the second to override the first (for files with different contents)
    [green]help[/green] - Displays the help menu
    [green]exit[/green] - indicates to exit the program
    [green]show[/green] - Only the result of the selector is displayed
    [green]cls[/green] - clear screen
Selector (case sensitive):
    A selector is essentially a set, we will get it by eval
    There are sum global variable you can use: all, rows, differents
    And we also have provided you with some shorthand methods that can be used in the global function "s"
        [green]r[/green] - range,r x[,y[,z]] means range(x[,y[,z]])
        [green]m[/green] - match,m name,value means all rows whose name is name and value is value
        [green]mr[/green] - match regex,mr name,regex means all rows whose name is name and value matches regex
    Attention: The arguments of the shorthand methods must be separated by a comma, and if you don't want to split it there, you can use "\\,". However, notice how python escapes the "\\" character
    For example:
        s("r 1,10") means range(1,10)
        s("m name,kuankuan") means all rows whose name is name and value is "kuankuan"
        s("mr name,kk\\\\,China.*\\\\.png") means all rows whose name is name and value matches r"kk,China.*\\.png"
    In particular, if you simply want to use an abbreviation, you can simply start with "#" and follow the abbreviation.
    For example:
        [green]#r 1,10[/green] is equivalent to s("r 1,10")
        [green]#mr name,kk\\,China.*\\.png[/green] is equivalent to s("mr name,kk\\\\,China.*\\\\.png")
"""
        if title.lower() == "exit":
            while True:
                console.print("[yellow]exit?[/yellow](Y/n)", end="")
                sure = console.input()
                if sure.lower() == "n":
                    errSum = 0
                    return "Cancel exit"
                if sure.lower() == "y":
                    sys.exit()
        elif len(chooserStr) == 0:
            errSum += 1
            return "[red]No selector[/red]"
        try:
            chooser: set = set(chooserParser(chooserStr))
            for i in chooser:
                assert type(i) == int
        except BaseException as err:
            errSum += 1
            return f"[red]Wrong selector\n{err.__class__.__name__}:{err}[/red]"
        li: List[Union[comp.FileMissing, comp.FolderMissing, comp.FileDifferent]] = []
        for i in chooser:
            if i < len(all) and all[i].statue == "waiting":
                li.append(all[i])
        if not len(li):
            return "[yellow]Empty selector[/yellow]"
        if title.lower() == "copy":
            copyChoice: List[Union[comp.FileMissing, comp.FolderMissing]] = [
                i
                for i in li
                if type(i) == comp.FileMissing or type(i) == comp.FolderMissing
            ]
            selectedItemTable = Table(
                Column(header="Name", no_wrap=True),
                Column(header="Type", no_wrap=True),
                Column(header="Statue", no_wrap=True),
                Column(header="Found Root", no_wrap=True),
                Column(header="Relative Path", max_width=40, no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow", bold=True),
                title_justify="left",
            )
            for i in copyChoice:
                selectedItemTable.add_row(
                    i.name,
                    "[green]File[/green]"
                    if type(i) == comp.FileMissing
                    else "[blue]Folder[/blue]",
                    statueMapping[i.statue],
                    i.root.path,
                    "/".join(i.path),
                )
            console.print(selectedItemTable)
            while True:
                console.print(
                    "[yellow]Are you sure to copy these items[/yellow](Y/n)", end=""
                )
                a = console.input("")
                if a.lower() == "n":
                    errSum = 0
                    return "Cancel copy"
                elif a.lower() == "y":
                    break
            for i in copyChoice:
                console.print(f"[blue]Copying {i.name}[/blue]")
                i.copy()
            return f"{len(copyChoice)} projects were copied"
        if title.lower() == "del":
            delChoice = li
            selectedItemTable = Table(
                Column(header="Name", no_wrap=True),
                Column(header="Statue", no_wrap=True),
                Column(header="Type", no_wrap=True),
                Column(header="Found Root", no_wrap=True),
                Column(header="Relative Path", max_width=40, no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow", bold=True),
                title_justify="left",
            )
            for i in delChoice:
                selectedItemTable.add_row(
                    i.name,
                    statueMapping[i.statue],
                    "[blue]Folder[/blue]"
                    if type(i) == comp.FolderMissing
                    else "[green]File[/green]",
                    i.root.path
                    if type(i) == comp.FileMissing or type(i) == comp.FolderMissing
                    else "[blue]--BOTH--[/blue]",
                    "/".join(i.path),
                )
            console.print(selectedItemTable)
            while True:
                console.print(
                    "[yellow]Are you sure to delete these items[/yellow](Y/n)", end=""
                )
                a = console.input("")
                if a.lower() == "n":
                    errSum = 0
                    return "Cancel delete"
                elif a.lower() == "y":
                    break
            for i in delChoice:
                console.print(f"[blue]Deleting {i.name}[/blue]")
                i.remove()
            return f"{len(delChoice)} projects were deleted"
        if title.lower() == "choice1":
            choice1Choice: List[comp.FileDifferent] = [
                i for i in li if type(i) == comp.FileDifferent
            ]
            selectedItemTable = Table(
                Column(header="Name", no_wrap=True),
                Column(header="Statue", no_wrap=True),
                Column(header="Root1", no_wrap=True),
                Column(header="Root2", no_wrap=True),
                Column(header="Relative Path", max_width=40, no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow", bold=True),
                title_justify="left",
            )
            for i in choice1Choice:
                selectedItemTable.add_row(
                    i.name,
                    statueMapping[i.statue],
                    i.root1.path,
                    i.root2.path,
                    "/".join(i.path),
                )
            console.print(selectedItemTable)
            while True:
                console.print(
                    "[yellow]Override root2 with the contents of root1[/yellow](Y/n)",
                    end="",
                )
                a = console.input("")
                if a.lower() == "n":
                    errSum = 0
                    return "Cancel override"
                elif a.lower() == "y":
                    break
            for i in choice1Choice:
                console.print(f"[blue]Copying {i.name}[/blue]")
                i.copy(1)
            return f"{len(choice1Choice)} projects were override"
        if title.lower() == "choice2":
            choice2Choice: List[comp.FileDifferent] = [
                i for i in li if type(i) == comp.FileDifferent
            ]
            selectedItemTable = Table(
                Column(header="Name", no_wrap=True),
                Column(header="Statue", no_wrap=True),
                Column(header="Root1", no_wrap=True),
                Column(header="Root2", no_wrap=True),
                Column(header="Relative Path", max_width=40, no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow", bold=True),
                title_justify="left",
            )
            for i in choice2Choice:
                selectedItemTable.add_row(
                    i.name,
                    statueMapping[i.statue],
                    i.root1.path,
                    i.root2.path,
                    "/".join(i.path),
                )
            console.print(selectedItemTable)
            while True:
                console.print(
                    "[yellow]Override root1 with the contents of root2[/yellow](Y/n)",
                    end="",
                )
                a = console.input("")
                if a.lower() == "n":
                    errSum = 0
                    return "Cancel override"
                elif a.lower() == "y":
                    break
            for i in choice2Choice:
                console.print(f"[blue]Copying {i.name}[/blue]")
                i.copy(2)
            return f"{len(choice2Choice)} projects were override"
        if title.lower() == "show":
            showChoice = li
            selectedItemTable = Table(
                Column(header="Name", no_wrap=True),
                Column(header="Statue", no_wrap=True),
                Column(header="Root", no_wrap=True),
                Column(header="Relative Path", max_width=40, no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow", bold=True),
                title_justify="left",
            )
            for i in showChoice:
                selectedItemTable.add_row(
                    i.name,
                    statueMapping[i.statue],
                    i.root.path
                    if type(i) == comp.FileMissing or type(i) == comp.FolderMissing
                    else "--BOTH--",
                    "/".join(i.path),
                )
            return selectedItemTable
        errSum += 1
        return "[red]Unknown Command[/red]"

    def showTable():
        console.clear()
        os.system("cls")
        nonlocal all
        all.clear()
        rows.clear()
        if fileMissingList:
            fileMissingTable = Table(
                Column(header="ID", no_wrap=True),
                Column(header="File Name", no_wrap=True),
                Column(header="Statue", no_wrap=True),
                Column(header="Found Root", no_wrap=True),
                Column(header="Relative Path", max_width=40, no_wrap=True),
                title="File Missing",
                title_style=Style(color="yellow", bold=True),
                title_justify="left",
            )
            for i in fileMissingList:
                all.append(i)
                TableRow(
                    TableAttr(
                        "id",
                        str(len(all) - 1),
                    ),
                    TableAttr(
                        "name",
                        i.name,
                    ),
                    TableAttr("statue", i.statue, statueColorMapping[i.statue]),
                    TableAttr(
                        "foundRoot",
                        i.root.path,
                    ),
                    TableAttr(
                        "relativePath",
                        "/".join(i.path),
                    ),
                    id=len(all) - 1,
                    table=fileMissingTable,
                )
            console.print(fileMissingTable)
        if folderMissingList:
            folderMissingTable = Table(
                Column(header="ID", no_wrap=True),
                Column(header="Folder Name", no_wrap=True),
                Column(header="Statue", no_wrap=True),
                Column(header="Found Root", no_wrap=True),
                Column(header="Relative Path", max_width=40, no_wrap=True),
                title="Folder Missing",
                title_style=Style(color="yellow", bold=True),
                title_justify="left",
            )
            for i in folderMissingList:
                all.append(i)
                TableRow(
                    TableAttr(
                        "id",
                        str(len(all) - 1),
                    ),
                    TableAttr(
                        "name",
                        i.name,
                    ),
                    TableAttr("statue", i.statue, statueColorMapping[i.statue]),
                    TableAttr(
                        "foundRoot",
                        i.root.path,
                    ),
                    TableAttr(
                        "relativePath",
                        "/".join(i.path),
                    ),
                    id=len(all) - 1,
                    table=folderMissingTable,
                )
            console.print(folderMissingTable)
        if fileDifferentList:
            fileDifferentTable = Table(
                Column(header="ID", no_wrap=True),
                Column(header="File Name", no_wrap=True),
                Column(header="Choice1", no_wrap=True),
                Column(header="Choice2", no_wrap=True),
                Column(header="Statue", no_wrap=True),
                Column(header="Relative Path", max_width=40, no_wrap=True),
                title="File Different",
                title_style=Style(color="yellow", bold=True),
                title_justify="left",
            )
            for i in fileDifferentList:
                all.append(i)
                TableRow(
                    TableAttr(
                        "id",
                        str(len(all) - 1),
                    ),
                    TableAttr(
                        "name",
                        i.name,
                    ),
                    TableAttr(
                        "choice1",
                        datetime.datetime.fromtimestamp(i.file1.mtime).strftime(
                            "%y-%m-%d %H:%M"
                        ),
                    ),
                    TableAttr(
                        "choice2",
                        datetime.datetime.fromtimestamp(i.file2.mtime).strftime(
                            "%y-%m-%d %H:%M"
                        ),
                    ),
                    TableAttr("statue", i.statue, statueColorMapping[i.statue]),
                    TableAttr(
                        "relativePath",
                        "/".join(i.path),
                    ),
                    id=len(all) - 1,
                    table=fileDifferentTable,
                )
            console.print(fileDifferentTable)
        for i in result:
            console.print(i)
        if errSum >= 3:
            console.print("[yellow]Type help to see help[/yellow]")
        console.print(">>>", end="")

    command = ""
    if not (fileMissingList or folderMissingList or fileDifferentList):
        console.print("[yellow]No different found[/yellow]")
        sys.exit(0)
    showTable()
    while True:
        command = console.input("")
        result.append(">>>" + command)
        result.append(doCommand(command))
        showTable()


if __name__ == "__main__":
    docompare(["e:\\blander", "l:\\blander", "-c", "size"])
