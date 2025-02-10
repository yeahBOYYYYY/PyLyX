from os.path import join, exists
from importlib import import_module
from PyLyX.data.data import PACKAGE_PATH
from PyLyX.lyx2xhtml.general import CSS_FOLDER
from PyLyX.objects.Environment import Environment


def perform_module(module: str, head: Environment, body: Environment, info: dict, css_folder=CSS_FOLDER):
    path = join(PACKAGE_PATH, 'lyx2xhtml', 'modules', module) + '.py'
    if exists(path):
        module = f'PyLyX.lyx2xhtml.modules.{module}'
        import_module(module).main(head, body, info, css_folder)
    else:
        print(f'unknown module: {module}.')