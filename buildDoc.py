#!/usr/bin/python3
"""Generate API documentation using Sphinx's apidoc."""
from pathlib import Path
import sys
from typing import TypedDict
import traceback
import json
import io
import shutil
import subprocess
import tomllib
import datetime
import sphinx
import sphinx.application
from sphinx._cli.util.colour import disable_colour
import sphinx.ext
import sphinx.ext.apidoc
import sphinx.ext.apidoc._generate as apidoc_generate
import zipfile

from sphinx.ext.apidoc._shared import ApidocOptions


ApiDocOptions = TypedDict(
    "ApiDocOptions",
    {
        "src": Path,
        "dist": Path,
        "templatedir": Path,
        "force": bool,
    },
)
SphinxOptions = TypedDict(
    "SphinxOptions",
    {
        "src": Path,
        "dist": Path,
        "build": str,
        "noColor": bool,
        "force": bool,
    },
)


def formatError():
    e = sys.exception()
    if e is None:
        return "__NO_EXCEPTION"
    return f"{e.__class__.__name__}: {e}\n--------\n{traceback.format_exc()}"


class CopyStream:
    """A class to duplicate output to both console and a file."""

    streams: list[io.IOBase]

    def __init__(self, *streams: io.IOBase):
        self.streams = list(streams)

    def write(self, data):
        for stream in self.streams:
            if hasattr(stream, "write"):
                stream.write(data)

    def flush(self):
        for stream in self.streams:
            if hasattr(stream, "flush"):
                stream.flush()


def get_git_info():
    """Retrieve current Git branch and commit information."""
    try:
        longCommitId = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        return {
            "branch": subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip(),
            "commit": longCommitId,
            "shortCommit": subprocess.check_output(
                ["git", "log", "--pretty=format:%h", longCommitId, "-1"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip(),
            "commitTitle": subprocess.check_output(
                ["git", "log", "--pretty=format:%s", longCommitId, "-1"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip(),
            "commitContent": subprocess.check_output(
                ["git", "log", "--pretty=format:%b", longCommitId, "-1"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip(),
            "commitTime": subprocess.check_output(
                ["git", "log", "--pretty=format:%ci", longCommitId, "-1"],
                text=True,
            ).strip(),
            "commitAuthor": subprocess.check_output(
                ["git", "log", "--pretty=format:%cn", longCommitId, "-1"],
                text=True,
            ).strip(),
            "commitEmail": subprocess.check_output(
                ["git", "log", "--pretty=format:%ce", longCommitId, "-1"],
                text=True,
            ).strip(),
            "parentCommitId": subprocess.check_output(
                ["git", "log", "--pretty=format:%P", longCommitId, "-1"],
                text=True,
            ).strip(),
        }
    except Exception:
        return {
            "branch": "__UNKNOWN",
            "commit": "__UNKNOWN",
            "error": "Cannot get git info",
            "exception": formatError(),
        }


def build(apidocOptions: ApiDocOptions, sphinxOptions: SphinxOptions):
    OUT_DIR = sphinxOptions["dist"]
    LOG_DIR = OUT_DIR / "logs"
    if LOG_DIR.exists():
        shutil.rmtree(LOG_DIR)  # Remove existing log directory
    LOG_DIR.mkdir(exist_ok=True, parents=True)  # Create log directory

    buildLog = LOG_DIR / "build_error.log"
    apidocLog = LOG_DIR / "apidoc.log"
    stdout_log = LOG_DIR / "stdout.log"
    stderr_log = LOG_DIR / "stderr.log"
    _stdout = sys.stdout
    _stderr = sys.stderr

    with stdout_log.open("w", encoding="utf-8") as stdout_file, stderr_log.open(
        "w", encoding="utf-8"
    ) as stderr_file:
        sys.stdout = CopyStream(stdout_file, _stdout)  # type: ignore
        sys.stderr = CopyStream(stderr_file, _stderr)  # type: ignore

        try:

            apidocOpt = ApidocOptions(
                module_path=apidocOptions["src"],
                dest_dir=apidocOptions["dist"],
                force=apidocOptions["force"],
                template_dir=str(apidocOptions["templatedir"]),
                separate_modules=True,
            )

            res = apidoc_generate.recurse_tree(
                apidocOpt.module_path,
                [],
                apidocOpt,
                apidocOpt.template_dir,
            )

            with apidocLog.open("w", encoding="utf-8") as f:
                json.dump(
                    {"res": {"paths": [str(i) for i in res[0]], "modules": res[1]}},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            if sphinxOptions["noColor"]:  # pylint: disable=too-many-function-args
                disable_colour()
            sphinx.application.Sphinx(
                srcdir=sphinxOptions["src"],
                outdir=sphinxOptions["dist"],
                confdir=sphinxOptions["src"],
                doctreedir=sphinxOptions["dist"] / ".doctrees",
                buildername=sphinxOptions["build"],
                status=sys.stdout, # type: ignore
                warning=sys.stderr,  # type: ignore
                warningiserror=True,
            ).build(
                force_all=sphinxOptions["force"],
                filenames=[],
            )
            with (Path(__file__).parent / "pyproject.toml").open("rb") as f:
                pyproject = tomllib.load(f)
            buildInfo = {
                "project": pyproject,
                "git": get_git_info(),  # Add Git branch and commit info
                "sphinx": {"version": sphinx.__version__, "conf": "__UNKNOWN"},
                "python": sys.version,
                "args": sys.argv,
                "time": datetime.datetime.now().isoformat(),
                "logs": [i.name for i in LOG_DIR.iterdir()],
            }

            try:
                import doc.source.conf as conf

                buildInfo["sphinx"]["conf"] = {
                    "extensions": conf.extensions,
                    "html_theme": conf.html_theme,
                    "html_static_path": conf.html_static_path,
                }
            except Exception as e:
                buildInfo["sphinx"]["conf"] = {
                    "value": "Cannot get the config",
                    "exception": formatError,
                }
                print(f"Cannot get the config: \n{formatError()}", file=sys.stderr)
            with (OUT_DIR / "buildInfo.json").open("w", encoding="utf-8") as f:
                json.dump(
                    buildInfo,
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

        except Exception as e:
            with buildLog.open("w", encoding="utf-8") as f:
                error_message = str(e)
                stack_trace = traceback.format_exc()
                f.write(f"{error_message}\n----------\n{stack_trace}")
            raise
        finally:

            sys.stdout = _stdout  # Restore original stdout
            sys.stderr = _stderr  # Restore original stderr

    # Compress the output directory into a zip file
    zip_path = Path(f"./temp/{pyproject['project']['name']}-{pyproject['project']['version']}.doc.zip")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in OUT_DIR.rglob("*"):
            zipf.write(file, file.relative_to(OUT_DIR))

    print("Documentation build complete.")
    print(f"Logs are available in {LOG_DIR}")
    print(f"Documentation is available in {OUT_DIR}")
    print(f"Build info is available in {OUT_DIR / 'buildInfo.json'}")
    print(f"Compressed documentation is available at {zip_path}")

def createChangeLogFile(src:Path):
    """Create a change log file from the changelogs directory."""
    print("Creating change log file")
    changelogs = src / "changelogs"
    files=list(i.name for i in changelogs.iterdir())
    files.sort(reverse=True)
    res = """
Change Log
~~~~~~~~~~~~

`The change log is automatically generated by the buildDoc.py script.`

"""
    for file in files:
        res += f""".. include:: ./changelogs/{file}

"""
    with (src / "changelog.rst").open("w", encoding="utf-8") as f:
        f.write(res)
    
    print("Change log file created")

def main():
    """Generate API documentation using Sphinx's apidoc."""
    import argparse

    argp = argparse.ArgumentParser()
    argp.add_argument(
        "--apidoc-src",
        help="Source directory for sphinx-apidoc to search for modules",
        default="src/doFolder",
    )
    argp.add_argument(
        "--apidoc-dist",
        help="Destination directory for sphinx-apidoc to create documentation",
        default="doc/source/apis",
    )

    argp.add_argument(
        "--templatedir",
        help="Template directory for sphinx-apidoc",
        default="doc/source/_templates",
    )
    argp.add_argument(
        "--no-force",
        action="store_true",
        help="Force overwriting existing files",
    )
    argp.add_argument(
        "--color",
        action="store_true",
        help="Colorize output",
    )

    argp.add_argument(
        "-b",
        "--build",
        default="html",
        help="Build format (default: %(default)s)",
    )
    argp.add_argument(
        "--dist",
        default="doc-dist",
        help="Path to the directory for the build (default: %(default)s)",
    )
    argp.add_argument(
        "--src",
        default="doc/source",
        help="Path to the directory for the build (default: %(default)s)",
    )

    args = argp.parse_args()
    apiDist = Path(args.apidoc_dist).absolute()
    if not apiDist.exists():
        print("Creating destination directory")
        apiDist.mkdir(parents=True)
    createChangeLogFile(Path(args.src).absolute())
    build(
        {
            "src": Path(args.apidoc_src).absolute(),
            "dist": Path(args.apidoc_dist).absolute(),
            "templatedir": Path(args.templatedir).absolute(),
            "force": not args.no_force,
        },
        {
            "src": Path(args.src).absolute(),
            "dist": Path(args.dist).absolute(),
            "build": args.build,
            "noColor": not args.color,
            "force": not args.no_force,
        },
    )


if __name__ == "__main__":
    main()
