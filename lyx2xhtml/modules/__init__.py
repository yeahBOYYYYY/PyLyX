from os.path import join, exists
from importlib import import_module
from PyLyX.data.data import PACKAGE_PATH
from PyLyX.objects.Environment import Environment


def perform_module(module: str, head: Environment, body: Environment, info: dict):
    path = join(PACKAGE_PATH, 'lyx2xhtml', 'modules', module) + '.py'
    if exists(path):
        module = f'PyLyX.lyx2xhtml.modules.{module}'
        import_module(module).main(head, body, info)
    else:
        print(f'unknown module: {module}.')