from os.path import join
from PyLyX.data.data import THEOREMS, TRANSLATE
from PyLyX.objects.Environment import Environment
from PyLyX.xhtml.special_objects import prefixing
from PyLyX.xhtml.helper import create_css, CSS_FOLDER


def main(head: Environment, body: Environment, info: dict, css_folder=CSS_FOLDER):
    head.append(create_css(join(css_folder, 'modules', 'theorems-ams.css')))
    lang = info['language']
    i = 0
    for e in body.iter('div'):
        if e.category() in THEOREMS:
            name = e.category()
            i += 1
            prefix = TRANSLATE['layout'][name][''][lang]
            if not name.endswith('*') and name != 'Proof':
                prefix += f' {i}.'
            else:
                prefix += '.'
            prefixing(e, prefix)