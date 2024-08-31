from lyx_reader import *

MATHJAX_SOURCE = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
BODY = 'body'


def import_script(attrib: dict):
    tag = 'src'
    if tag not in attrib:
        print(f'source is not exists, attrib = {attrib}')
        return None
    else:
        return Element('script', attrib)


def create_structure(css_path=''):
    head = Element('head')
    if css_path:
        element = Element('link', {'rel': "stylesheet", 'type': 'text/css', HREF: css_path})
        head.append(element)
    else:
        pass

    mathjax = import_script({'src': MATHJAX_SOURCE, 'async': 'async'})
    head.append(mathjax)
    element = Element('meta', {NAME: 'viewport', 'content':' width=device-width'})
    head.append(element)

    body = Element(BODY)
    root = Element('html', {'xmlns': 'http://www.w3.org/1999/xhtml'})
    root.extend((head, body))
    return root
