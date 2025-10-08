"""
Helper utilities for XHTML generation from LyX documents.

This module provides functions for:
- Scanning document headers for metadata
- Adding CSS and JavaScript to HTML output
- Creating table of contents and section numbering
- Handling language-specific styling (RTL/LTR)
- Numbering figures, footnotes, and captions
"""

from os.path import join
from PyLyX.package_helper import correct_name
from PyLyX.data.data import RTL_LANGS, PACKAGE_PATH, TRANSLATE
from PyLyX.objects.LyXobj import LyXobj
from PyLyX.objects.Environment import Environment
from PyLyX.xhtml.special_objects import prefixing

MATHJAX = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
CSS_FOLDER = join(PACKAGE_PATH, 'xhtml\\css')
BASIC_CSS, RTL_CSS, LTR_CSS = 'basic.css', 'rtl.css', 'ltr.css'
SECTIONS = ('Part', 'Chapter', 'Section', 'Subsection', 'Subsubsection', 'Paragraph', 'Subparagraph')


def scan_head(head: Environment):
    """
    Extract document metadata from the header.
    
    Parses the document header to extract settings like:
    - language: Document language
    - secnumdepth: Section numbering depth
    - tocdepth: Table of contents depth
    - textclass: Document class
    - html_math_output: Math rendering mode
    - html_css_as_file: CSS embedding preference
    - modules: List of LyX modules in use
    
    :param head: Document header Environment
    :return: Dictionary of document metadata
    """
    dictionary = {}
    for e in head:
        lst = e.get('class').split(maxsplit=1)
        if len(lst) == 2:
            class_, value = lst
            if class_ in {'language', 'secnumdepth', 'tocdepth', 'textclass', 'html_math_output', 'html_css_as_file'}:
                if class_ in {'secnumdepth', 'tocdepth', 'html_math_output', 'html_css_as_file'}:
                    value = int(value)
                dictionary[class_] = value
        elif e.tag == 'modules':
            dictionary['modules'] = e.text.split()
    return dictionary


def perform_lang(root: Environment, head: Environment, lang: str, css_folder=CSS_FOLDER):
    """
    Add language-specific CSS and set language attributes.
    
    Adds basic CSS and either RTL (right-to-left) or LTR (left-to-right)
    CSS based on the document language. Sets the lang attribute on the root element.
    
    :param root: Root HTML element
    :param head: HTML head element to add CSS links to
    :param lang: Document language code
    :param css_folder: Path to CSS folder
    """
    head.append(create_css(join(css_folder, BASIC_CSS)))
    if lang in RTL_LANGS:
        root.set('lang', RTL_LANGS[lang])
        head.append(create_css(join(css_folder, RTL_CSS)))
    else:
        head.append(create_css(join(css_folder, LTR_CSS)))


def create_title(head: LyXobj, body: LyXobj):
    """
    Extract document title from body and add to HTML head.
    
    Finds the first Title layout in the document body and creates
    a <title> element in the HTML head.
    
    :param head: HTML head element
    :param body: HTML body element containing the document
    """
    titles = body.findall(".//*[@class='layout Title']")
    if titles:
        title = titles[0]
        while not title.text and len(title):
            title = title[0]
        head_title = LyXobj('title', text=title.text)
        head.append(head_title)


def create_css(path: str):
    """
    Create a CSS link element.
    
    :param path: Path to the CSS file
    :return: Link element with stylesheet attributes
    """
    path = correct_name(path, '.css')
    attrib = {'rel': 'stylesheet', 'type': 'text/css', 'href': path}
    return LyXobj('link', attrib=attrib)


def create_script(source: str, async_=''):
    """
    Create a JavaScript script element.
    
    :param source: URL or path to the JavaScript file
    :param async_: Value for async attribute (empty string for no async)
    :return: Script element
    """
    attrib = {'src': source}
    if async_:
        attrib['async'] = async_
    return LyXobj('script', attrib=attrib)


def mathjax():
    """
    Create a MathJax script element for rendering mathematical formulas.
    
    :return: Script element loading MathJax from CDN
    """
    return create_script(MATHJAX, 'async')


def viewport():
    """
    Create a viewport meta tag for responsive design.
    
    :return: Meta element with viewport settings
    """
    attrib = {'name': 'viewport', 'content': 'width=device-width'}
    return LyXobj('meta', attrib=attrib)


def css_and_js(head, body, css_files=(), js_files=(), js_in_head=False):
    """
    Add CSS and JavaScript files to the HTML document.
    
    CSS files are always added to the head. JavaScript files can be added
    to either the head or the end of the body.
    
    :param head: HTML head element
    :param body: HTML body element
    :param css_files: Tuple of CSS file paths to include
    :param js_files: Tuple of JavaScript file paths to include
    :param js_in_head: Whether to place JS in head (True) or end of body (False)
    """
    for file in css_files:
        head.append(create_css(file))
    js_parent = head if js_in_head else body
    for file in js_files:
        js_parent.append(create_script(file))


def tocing(toc: LyXobj, obj: LyXobj, prefix):
    item = LyXobj('li')
    obj.set('id', obj.attrib['class'].split()[1] + '_' + prefix)
    link = LyXobj('a', attrib={'href': '#' + obj.get('id', '')}, text=prefix+' '+obj.text)
    item.append(link)
    toc.append(item)
    return item


def numbering_and_toc(toc: LyXobj, element, secnumdepth=-1, tocdepth=-1, prefix='', lang='english'):
    i = 0
    for sec in element.findall('section'):
        if sec.rank() <= max(secnumdepth, tocdepth) and sec is not element:
            if len(sec) and sec.attrib.get('class') in {f'layout {s}' for s in SECTIONS}:
                i += 1
                if sec.rank() <= secnumdepth or sec.rank() <= tocdepth:
                    new_prefix = f'{prefix}.{i}' if prefix else f'{i}'
                    if sec.rank() <= 1 and sec.is_in(TRANSLATE):
                        new_prefix = TRANSLATE[sec.command()][sec.category()][sec.details()][lang] + ' ' + new_prefix

                    if sec.rank() <= tocdepth:
                        item = tocing(toc, sec[0], new_prefix)
                        new_toc = LyXobj('ul')
                        item.append(new_toc)
                    else:
                        new_toc = toc
                    if sec.rank() <= secnumdepth:
                        prefixing(sec[0], new_prefix)
                    numbering_and_toc(new_toc, sec, secnumdepth, tocdepth, new_prefix, lang)


def number_foots_and_captions(body: LyXobj, lang: str):
    i = j = k = 0
    for e in body.iter():
        if e.is_category('Foot'):
            i += 1
            text = str(i)
        elif e.is_details('table'):
            j += 1
            text = f'{TRANSLATE[e.command()][e.category()][e.details()][lang]} {j}: '
            e = e.find(".//span/div[@class='inset Caption Standard']")
        elif e.is_details('figure'):
            k += 1
            text = f'{TRANSLATE[e.command()][e.category()][e.details()][lang]} {k}: '
            e = e.find(".//span/div[@class='inset Caption Standard']")
        else:
            continue
        if e is not None:
            prefixing(e, text, '')
