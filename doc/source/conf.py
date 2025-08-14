# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import datetime
import os
import sys
from pathlib import Path
import tomllib
import importlib

pkgDir = Path(__file__).parent.parent

sys.path.insert(0, (str(pkgDir)))

with (Path(__file__).parent.parent.parent / "pyproject.toml").open("rb") as f:
    pyproject = tomllib.load(f)

project = pyproject["project"]["name"]
author = pyproject["project"]["authors"][0]["name"]
copyright = f"2023-{datetime.datetime.now().year}, {author}"
release = importlib.import_module("tools.getInfo").getInfo().version

# Add src/doFolder to sys.path
sys.path.insert(0, os.path.abspath("../../src"))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "myst_parser",
    "sphinx.ext.autosummary",
]

autosummary_generate = True  # Automatically generate summary files
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}


source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
html_logo = "_static/logo.svg"
html_favicon = "_static/logo.svg"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "ksphinx"  # 自定义主题名称
html_static_path = ["_static"]


# html_domain_indices = False
