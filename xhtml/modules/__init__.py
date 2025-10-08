"""
LyX module handler for XHTML conversion.

This module provides functionality to process LyX modules during XHTML export.
LyX modules add additional functionality (theorems, custom headers/footers, etc.)
that require special handling during conversion.
"""

from os.path import join, exists
from importlib import import_module
from PyLyX.data.data import PACKAGE_PATH
from PyLyX.xhtml.helper import CSS_FOLDER
from PyLyX.objects.Environment import Environment


def perform_module(module: str, head: Environment, body: Environment, info: dict, css_folder=CSS_FOLDER):
    """
    Process a LyX module during XHTML conversion.
    
    Dynamically loads and executes the module's conversion handler.
    Each module should provide a main() function that modifies the
    HTML head and/or body as needed.
    
    Supported modules include:
    - theorems-ams: AMS theorem environments
    - theorems-starred: Unnumbered theorems
    - theorems-sec, theorems-chap: Section/chapter-numbered theorems
    - customHeadersFooters: Custom page headers and footers
    - tca-style: TCA-specific styling
    
    :param module: Name of the LyX module (without .py extension)
    :param head: HTML head element
    :param body: HTML body element
    :param info: Document metadata dictionary
    :param css_folder: Path to CSS folder for module stylesheets
    """
    path = join(PACKAGE_PATH, 'xhtml', 'modules', module) + '.py'
    if exists(path):
        module = f'PyLyX.xhtml.modules.{module}'
        import_module(module).main(head, body, info, css_folder)
    else:
        print(f'unknown module: {module}.')