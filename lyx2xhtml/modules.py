from PyLyX.data.data import THEOREMS, TRANSLATE
from PyLyX.objects.Environment import Environment
from PyLyX.lyx2xhtml.helper import prefixing


def theorems_ams(head: Environment, body: Environment, info: dict):
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


def theorems_sec(head: Environment, body, info: dict):
    for sec in body.findall('section'):
        if sec.is_category('Section'):
            n, i = sec[0][0].text[:-1], 0
            for e in sec.iter('div'):
                name = e.category()
                if e.category() in THEOREMS and not name.endswith('*') and name != 'Proof':
                    i += 1
                    e[0].text = e[0].text.split()[0] + f' {n}.{i}. '


def theorems_chap(head: Environment, body, info: dict):
    for sec in body.findall('section'):
        n, i = sec[0][0].text[:-1], 0
        if sec.is_category('Chapter'):
            for e in sec.iter('div'):
                name = e.category()
                if e.category() in THEOREMS and not name.endswith('*') and name != 'Proof':
                    i += 1
                    e[0].text = e[0].text.split()[0] + f' {n}.{i}. '


def customHeadersFooters(head: Environment, body, info: dict):
    pass


MODULES = {'theorems-ams': theorems_ams,
           'theorems-sec': theorems_sec,
           'theorems-chap': theorems_chap,
           'customHeadersFooters': customHeadersFooters}
