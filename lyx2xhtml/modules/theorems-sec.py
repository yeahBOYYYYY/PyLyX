from PyLyX.objects.Environment import Environment
from PyLyX.data.data import THEOREMS


def main(head: Environment, body, info: dict):
    for sec in body.findall('section'):
        if sec.is_category('Section'):
            n, i = sec[0][0].text[:-1], 0
            for e in sec.iter('div'):
                name = e.category()
                if e.category() in THEOREMS and not name.endswith('*') and name != 'Proof':
                    i += 1
                    e[0].text = e[0].text.split()[0] + f' {n}.{i}. '
