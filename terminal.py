import doFolder
import doFolder.compare as comp
from rich.console import Console
from rich.table import Table,Column
from rich.style import Style
import datetime
import sys
from typing import List,Union,Set

def compare():
    import argparse
    statueMapping={
        'copied':"[green]copied[/green]",
        "removed":'[red]removed[/red]', 
        'waiting':"[yellow]waiting[/yellow]", 
        'choice1':"[cyan]choice1[/cyan]",
        'choice2':"[cyan]choice2[/cyan]"
    }
    argparser = argparse.ArgumentParser()
    argparser.add_argument('folder1',type = str, help = 'The first folder to compare')
    argparser.add_argument('folder2',type = str, help = 'The second folder to compare')
    argparser.add_argument('-c', '--content', type = str, choices=["ignore","hash","content","size"] ,default="ignore", help = 'How to compare the content of the file')
    args = argparser.parse_args()
    folder1 = doFolder.Folder(args.folder1)
    folder2 = doFolder.Folder(args.folder2)
    retsult=comp.compare(folder1, folder2,args.content)
    fileMissingList=retsult.fileMissingList
    folderMissingList=retsult.folderMissingList
    fileDifferentList=retsult.fileDifferentList
    console=Console()
    all:List[Union[comp.FileMissing,comp.FolderMissing,comp.FileDifferent]]=[]
    errSum:int = 0
    result:List=[]
    def doCommand(command:str):
        nonlocal errSum,result
        if len(command)==0:
            errSum+=1
            return "[red]Null instruction[/red]"
        else:
            commands=command.split(" ")
            title=commands[0]
            chooser=" ".join(commands[1:])
        if title.lower() == "cls":
            result=[]
            return ""
        if title.lower() == "help":
            errSum=0
            return """
Help:
Command format :[blue] Command selector [/blue]
Commands have the following types (case insensitive):
[yellow]copy[/yellow]: Copies the selected project (for missing files/folders)
[yellow]del[/yellow]: Deletes the selected item (for all items)
[yellow]choice1[/yellow]: Select the first to override the second (for files with different contents)
[yellow]choice2[/yellow]: Select the second to override the first (for files with different contents)
[yellow]help[/yellow]: Displays the help menu
[yellow]exit[/yellow]: indicates to exit the program
[yellow]show[/yellow]: Only the result of the selector is displayed
[yellow]cls[/yellow]: clear screen
Selector (case sensitive):
A selector is essentially a set, including {}
"""
        if title.lower()=="exit":
            while True:
                console.print("[yellow]exit?[/yellow](Y/n)",end="")
                sure=console.input()
                if sure.lower()=="n":
                    errSum=0
                    return "Cancel exit"
                if sure.lower()=="y":
                    sys.exit()
        elif len(chooser)==0:
            errSum+=1
            return "[red]No selector[/red]"
        try :
            chooser=set(eval(chooser))
            for i in chooser:
                assert type(i)==int
        except BaseException as err:
            errSum+=1
            return "[red]Wrong selector[/red]"
        li:List[Union[comp.FileMissing,comp.FolderMissing,comp.FileDifferent]]=[]
        for i in chooser:
            if i<len(all) and all[i].statue=="waiting":
                li.append(all[i])
        if not len(li):
            return "[yellow]Empty selector[/yellow]"
        if title.lower()=="copy":
            copyChoice:List[Union[comp.FileMissing,comp.FolderMissing]]=[i for i in li if type(i) == comp.FileMissing or  type(i) == comp.FolderMissing]
            selectedItemTable = Table(
                Column(header="Name",no_wrap=True),
                Column(header="Type",no_wrap=True),
                Column(header="Statue",no_wrap=True),
                Column(header="Found Root",no_wrap=True),
                Column(header="Relative Path",max_width=40,no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow",bold=True),
                title_justify="left"
            )
            for i in copyChoice:
                selectedItemTable.add_row(i.name,"[green]File[/green]" if type(i)==comp.FileMissing else "[blue]Folder[/blue]",statueMapping[i.statue],i.root.path,"/".join(i.path))
            console.print(selectedItemTable)
            while True:
                console.print("[yellow]Are you sure to copy these items[/yellow](Y/n)",end="")
                a=console.input("")
                if a.lower()=="n":
                    errSum=0
                    return "Cancel copy"
                elif a.lower()=="y":
                    break
            for i in copyChoice:
                console.print(f"[blue]Copying {i.name}[/blue]")
                i.copy()
            return f"{len(copyChoice)} projects were copied"
        if title.lower()=="del":
            delChoice=li
            selectedItemTable = Table(
                Column(header="Name",no_wrap=True),
                Column(header="Statue",no_wrap=True),
                Column(header="Type",no_wrap=True),
                Column(header="Found Root",no_wrap=True),
                Column(header="Relative Path",max_width=40,no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow",bold=True),
                title_justify="left"
            )
            for i in delChoice:
                selectedItemTable.add_row(i.name,statueMapping[i.statue],"[blue]Folder[/blue]" if type(i)==comp.FolderMissing else "[green]File[/green]",i.root.path if type(i) == comp.FileMissing or type(i) == comp.FolderMissing else "[blue]--BOTH--[/blue]","/".join(i.path))
            console.print(selectedItemTable)
            while True:
                console.print("[yellow]Are you sure to delete these items[/yellow](Y/n)",end="")
                a=console.input("")
                if a.lower()=="n":
                    errSum=0
                    return "Cancel delete"
                elif a.lower()=="y":
                    break
            for i in delChoice:
                console.print(f"[blue]Deleting {i.name}[/blue]")
                i.remove()
            return f"{len(delChoice)} projects were deleted"
        if title.lower()=="choice1":
            choice1Choice:List[comp.FileDifferent]=[i for i in li if type(i) == comp.FileDifferent]
            selectedItemTable = Table(
                Column(header="Name",no_wrap=True),
                Column(header="Statue",no_wrap=True),
                Column(header="Root1",no_wrap=True),
                Column(header="Root2",no_wrap=True),
                Column(header="Relative Path",max_width=40,no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow",bold=True),
                title_justify="left"
            )
            for i in choice1Choice:
                selectedItemTable.add_row(i.name,statueMapping[i.statue],i.root1.path,i.root2.path,"/".join(i.path))
            console.print(selectedItemTable)
            while True:
                console.print("[yellow]Override root2 with the contents of root1[/yellow](Y/n)",end="")
                a=console.input("")
                if a.lower()=="n":
                    errSum=0
                    return "Cancel override"
                elif a.lower()=="y":
                    break
            for i in choice1Choice:
                console.print(f"[blue]Copying {i.name}[/blue]")
                i.copy(1)
            return f"{len(choice1Choice)} projects were override"
        if title.lower()=="choice2":
            choice2Choice:List[comp.FileDifferent]=[i for i in li if type(i) == comp.FileDifferent]
            selectedItemTable = Table(
                Column(header="Name",no_wrap=True),
                Column(header="Statue",no_wrap=True),
                Column(header="Root1",no_wrap=True),
                Column(header="Root2",no_wrap=True),
                Column(header="Relative Path",max_width=40,no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow",bold=True),
                title_justify="left"
            )
            for i in choice2Choice:
                selectedItemTable.add_row(i.name,statueMapping[i.statue],i.root1.path,i.root2.path,"/".join(i.path))
            console.print(selectedItemTable)
            while True:
                console.print("[yellow]Override root1 with the contents of root2[/yellow](Y/n)",end="")
                a=console.input("")
                if a.lower()=="n":
                    errSum=0
                    return "Cancel override"
                elif a.lower()=="y":
                    break
            for i in choice2Choice:
                console.print(f"[blue]Copying {i.name}[/blue]")
                i.copy(2)
            return f"{len(choice2Choice)} projects were override"
        if title.lower()=="show":
            showChoice=li
            selectedItemTable = Table(
                Column(header="Name",no_wrap=True),
                Column(header="Statue",no_wrap=True),
                Column(header="Root",no_wrap=True),
                Column(header="Relative Path",max_width=40,no_wrap=True),
                title="Selected item",
                title_style=Style(color="yellow",bold=True),
                title_justify="left"
            )
            for i in showChoice:
                selectedItemTable.add_row(i.name,statueMapping[i.statue],i.root.path if type(i) == comp.FileMissing or type(i) == comp.FolderMissing else "--BOTH--","/".join(i.path))
            return selectedItemTable
        errSum+=1
        return "[red]Unknown Command[/red]"
    def showTable():
        console.clear()
        nonlocal all
        all.clear()
        if fileMissingList:
            fileMissingTable = Table(
                Column(header="ID",no_wrap=True),
                Column(header="File Name",no_wrap=True),
                Column(header="Statue",no_wrap=True),
                Column(header="Found Root",no_wrap=True),
                Column(header="Relative Path",max_width=40,no_wrap=True),
                title="File Missing",
                title_style=Style(color="yellow",bold=True),
                title_justify="left"
            )
            for i in fileMissingList:
                all.append(i)
                fileMissingTable.add_row(str(len(all)-1),i.name,i.statue,i.root.path,"/".join(i.path))
            console.print(fileMissingTable)
        if folderMissingList:
            folderMissingTable = Table(
                Column(header="ID",no_wrap=True),
                Column(header="Folder Name",no_wrap=True),
                Column(header="Statue",no_wrap=True),
                Column(header="Found Root",no_wrap=True),
                Column(header="Relative Path",max_width=40,no_wrap=True),
                title="Folder Missing",
                title_style=Style(color="yellow",bold=True),
                title_justify="left"
            )
            for i in folderMissingList:
                all.append(i)
                folderMissingTable.add_row(str(len(all)-1),i.name,statueMapping[i.statue],i.root.path,"/".join(i.path))
            console.print(folderMissingTable)
        if fileDifferentList:
            fileDifferentTable = Table(
                Column(header="ID",no_wrap=True),
                Column(header="File Name",no_wrap=True),
                Column(header="Choice1",no_wrap=True),
                Column(header="Choice2",no_wrap=True),
                Column(header="Statue",no_wrap=True),
                Column(header="Relative Path",max_width=40,no_wrap=True),
                title="File Different",
                title_style=Style(color="yellow",bold=True),
                title_justify="left"
            )
            for i in fileDifferentList:
                all.append(i)
                fileDifferentTable.add_row(str(len(all)-1),i.name,datetime.datetime.fromtimestamp(i.file1.mtime).strftime('%y-%m-%d %H:%M'),datetime.datetime.fromtimestamp(i.file2.mtime).strftime('%y-%m-%d %H:%M'),statueMapping[i.statue],"/".join(i.path))
            console.print(fileDifferentTable)
        for i in result:
            console.print(i)
        if errSum>=3:
            console.print("[yellow]Type help to see help[/yellow]")
        console.print(">>>",end="")
    command=""
    if not (fileMissingList or folderMissingList or fileDifferentList):
        console.print("[yellow]No different found[/yellow]")
        sys.exit(0)
    showTable()
    while True:
        command=console.input("")
        result.append(">>>"+command)
        result.append(doCommand(command))
        showTable()