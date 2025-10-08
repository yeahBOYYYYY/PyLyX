"""
Main XHTML conversion module for LyX documents.

This module converts LyX document objects to XHTML format by:
- Mapping LyX objects to appropriate HTML tags
- Converting LyX attributes to HTML/CSS styles
- Handling special elements (formulas, tables, images, etc.)
- Generating table of contents and section numbering
- Processing document modules
"""

from os.path import join
from json import load
from xml.etree.ElementTree import Element
from PyLyX.data.data import PAR_SET, PACKAGE_PATH, TRANSLATE
from PyLyX.objects.LyXobj import LyXobj, DEFAULT_RANK
from PyLyX.objects.Environment import Environment, Container
from PyLyX.xhtml.special_objects import perform_table, perform_cell, perform_lists, perform_box, perform_text, \
    perform_image, correct_formula, TEXTS
from PyLyX.xhtml.helper import scan_head, perform_lang, create_title, css_and_js, numbering_and_toc, \
    number_foots_and_captions, mathjax, viewport, CSS_FOLDER
from PyLyX.xhtml.modules import perform_module

with open(join(PACKAGE_PATH, 'xhtml\\data\\tags.json'), 'r', encoding='utf8') as f:
    TAGS = load(f)
with open(join(PACKAGE_PATH, 'xhtml\\data\\tables.json'), 'r', encoding='utf8') as f:
    TABLES = load(f)
with open(join(PACKAGE_PATH, 'xhtml\\data\\light_dark.json'), 'r', encoding='utf8') as f:
    LIGHT_DARK = load(f)


def create_info(obj: LyXobj):
    """
    Determine HTML tag and conversion information for a LyX object.
    
    Maps LyX objects to appropriate HTML tags based on their type and properties.
    Looks up conversion rules in TAGS and TABLES dictionaries.
    
    :param obj: LyX object to get conversion info for
    :return: Dictionary containing 'tag' and optionally other conversion parameters
    """
    if type(obj) is Environment and obj.is_in(TAGS):
        details = '*****' if obj.details() not in TAGS[obj.command()][obj.category()] else obj.details()
        info = TAGS[obj.command()][obj.category()][details]
    elif type(obj) is Environment and obj.tag in TABLES:
        info = TABLES[obj.tag]
    elif type(obj) is Container:
        info = {'tag': 'section'}
    elif (obj.is_command('layout') and not (obj.is_category('Plain') and obj.is_details('Layout'))) or obj.command() in PAR_SET:
        info = {'tag': 'div'}
    else:
        info = {'tag': 'span'}
    return info


def create_attributes(obj: LyXobj, info: dict, keep_data=False):
    """
    Convert LyX object attributes to HTML attributes.
    
    Transforms LyX-specific attributes into appropriate HTML attributes,
    handles special cases (boxes, images, tables, etc.), and optionally
    preserves LyX metadata as data- attributes.
    
    :param obj: LyX object to convert attributes from
    :param info: Conversion information dictionary with attribute mappings
    :param keep_data: Whether to preserve all LyX attributes as data- attributes
    :return: Dictionary of HTML attributes
    """
    old_attrib = obj.attrib.copy()
    new_attrib = {}

    if 'options' in info:
        for key in info['options']:
            if key in old_attrib:
                new_key, value = info['options'][key], old_attrib.pop(key)
                new_attrib[new_key] = value
    if 'class' in old_attrib:
        new_attrib['class'] = old_attrib.pop('class')

    if obj.is_category('Box'):
        perform_box(obj, old_attrib, new_attrib)
    elif obj.is_category('Graphics'):
        perform_image(old_attrib, new_attrib)
    elif obj.tag == 'cell':
        perform_cell(old_attrib, new_attrib)
    elif obj.is_details('ref'):
        new_attrib['href'] = '#' + new_attrib['href']
    elif obj.is_category('other'):
        old_attrib['details'] = obj.details()
    elif obj.is_category('FormulaMacro'):
        lines = obj.text.splitlines()[1:]
        lines = '\n'.join(lines)
        old_attrib['lines'] = lines

    if 'style' in new_attrib:
        for color in LIGHT_DARK:
            light_dark_color = f'light-dark({LIGHT_DARK[color][0]}, {LIGHT_DARK[color][1]})'
            new_attrib['style'] = new_attrib['style'].replace(color, light_dark_color)

    if keep_data:
        for key in old_attrib:
            new_attrib[f'data-{key}'] = old_attrib[key].replace('"', '')
    elif 'filename' in old_attrib:
        new_attrib['data-filename'] = old_attrib['filename'].replace('"', '')
    return new_attrib


def create_text(obj, new_attrib: dict):
    """
    Extract and format text content from a LyX object.
    
    Handles special text formatting for:
    - Mathematical formulas (converts LaTeX syntax)
    - Formula macros
    - Special text objects (quotes, accents, etc.)
    - Cross-references
    
    :param obj: LyX object to extract text from
    :param new_attrib: HTML attributes dictionary (may be modified)
    :return: Formatted text string for HTML output
    """
    if obj.is_category('Formula'):
        return correct_formula(obj.text)
    elif obj.is_category('FormulaMacro'):
        macro = obj.text.splitlines()[0]
        return correct_formula(macro)
    elif obj.is_in(TEXTS):
        return perform_text(obj)
    elif obj.is_details('ref'):
        text = new_attrib.get('href', '#')[1:]
        new_txt = ''
        if new_attrib.get('data-LatexCommand') == 'ref':
            for c in text:
                if c in '1234567890.':
                    new_txt += c
        elif new_attrib.get('data-LatexCommand') == 'nameref':
            pass
        if new_txt:
            return new_txt
        else:
            return text
    elif 'text' in new_attrib:
        return new_attrib.pop('text')
    else:
        return obj.text


def one_obj(obj, keep_data=False, replaces: dict | None = None):
    """
    Convert a single LyX object to HTML (non-recursive).
    
    Creates a copy of the object with HTML tag, attributes, and text.
    Does not convert child elements. Handles string replacements in attributes
    and special processing for include insets.
    
    :param obj: LyX object to convert
    :param keep_data: Whether to preserve LyX metadata as data- attributes
    :param replaces: Dictionary of string replacements to apply to attributes
    :return: Converted object with HTML properties
    """
    info = create_info(obj)
    attrib = create_attributes(obj, info, keep_data)
    text = create_text(obj, attrib)
    new_obj = obj.copy()
    new_obj.open()
    for e in new_obj:
        e.open()
    if replaces is not None:
        for old in replaces:
            for key in attrib:
                attrib[key] = attrib[key].replace(old, replaces[old])
    new_obj.tag, new_obj.text, new_obj.attrib = info['tag'], text, attrib
    if 'class' in new_obj.attrib and new_obj.attrib['class'].endswith('*'):
        new_obj.set('class', new_obj.get('class')[:-1] + '_')
    if new_obj.is_details('include'):
        perform_include(new_obj)
    return new_obj


def recursive_convert(obj: LyXobj | Element, lang='english', toc: tuple[LyXobj, LyXobj] | None = None, keep_data=False, replaces: dict | None = None):
    """
    Recursively convert a LyX object and all its children to HTML.
    
    Main conversion function that processes the entire document tree:
    - Tracks document language for RTL/LTR handling
    - Converts each object and its descendants
    - Handles special cases (section titles, lists, tables)
    - Builds table of contents structure
    
    :param obj: LyX object to convert
    :param lang: Document language code (e.g., 'english', 'hebrew')
    :param toc: Tuple of (toc_title, toc_list) for building table of contents
    :param keep_data: Whether to preserve LyX metadata
    :param replaces: Dictionary of string replacements for attributes
    :return: Converted HTML object with all children converted
    """
    if obj.is_command('lang'):
        lang = obj.category()
    new_obj = one_obj(obj, keep_data, replaces)
    is_first = True
    last = None
    for child in obj:
        child = recursive_convert(child, lang, toc, keep_data, replaces)
        if child.is_section_title() and is_first:
            new_obj[0] = child
            last = None
        elif child.is_category({'Labeling', 'Itemize', 'Enumerate', 'Description'}):
            last = perform_lists(new_obj, child, last)
        else:
            new_obj.append(child)
            last = None
        is_first = False

    if new_obj.is_command('lyxtabular'):
        perform_table(new_obj, lang)
    if new_obj.is_details('toc') and toc is not None:
        add_toc(new_obj, toc[0], toc[1])
    return new_obj


def add_toc(toc_obj: LyXobj, toc_title: LyXobj, toc: LyXobj):
    """
    Add table of contents elements to a TOC container object.
    
    :param toc_obj: Container object for the table of contents
    :param toc_title: Title element (e.g., "Table of Contents" heading)
    :param toc: List element containing TOC entries
    """
    toc_obj.append(toc_title)
    toc_obj.append(toc)


def convert(root, css_files=(), css_folder=CSS_FOLDER, js_files=(), js_in_head=False, keep_data=False, replaces: dict | None = None):
    """
    Convert a complete LyX document to XHTML.
    
    Main entry point for XHTML conversion. Processes the entire document:
    1. Extracts document metadata from header
    2. Converts header to HTML head with metadata, CSS, and scripts
    3. Converts body to HTML with proper structure
    4. Generates table of contents
    5. Numbers sections, figures, and footnotes
    6. Applies language-specific styling (RTL/LTR)
    7. Processes LyX modules
    
    :param root: Root document Environment containing [header, body]
    :param css_files: Additional CSS files to include
    :param css_folder: Path to default CSS folder
    :param js_files: JavaScript files to include
    :param js_in_head: Whether to place JS in <head> (True) or end of body (False)
    :param keep_data: Whether to preserve LyX metadata in output
    :param replaces: Dictionary for string replacements in paths/attributes
    :return: Tuple of (root_element, info_dict)
    :raises Exception: If root doesn't have exactly 2 elements (header and body)
    """
    if len(root) == 2:
        info = scan_head(root[0])
        lang = info.get('language', 'english')
        if keep_data:
            head = recursive_convert(root[0])
            for e in head.iter():
                e.tag = 'meta'
        else:
            head = one_obj(root[0])
        head.extend((mathjax(), viewport()))
        perform_lang(root, head, lang, css_folder)

        toc = LyXobj('ul')
        toc_title = TRANSLATE['inset']['CommandInset']['toc'].get(lang, 'Table of Contents')
        toc_title = LyXobj('h2', text=toc_title)
        body = recursive_convert(root[1], lang, (toc_title, toc), keep_data, replaces)
        create_title(head, body)
        css_and_js(head, body, css_files, js_files, js_in_head)
        numbering_and_toc(toc, body, info.get('secnumdepth', -1), info.get('tocdepth', -1), '', lang)
        info['toc'] = LyXobj('inset', 'CommandInset', 'toc')
        add_toc(info['toc'], toc_title, toc)
        number_foots_and_captions(body, lang)
        if 'modules' in info:
            for module in info['modules']:
                perform_module(module, head, body, info, css_folder)

        root = one_obj(root, keep_data, replaces)
        root.set('xmlns', 'http://www.w3.org/1999/xhtml')
        root.extend((head, body))
        return root, info
    else:
        raise Exception(f'root must contain 2 subelements exactly, not {len(root)}.')


def perform_include(obj: LyXobj):
    if 'data-filename' in obj.attrib:
        path = obj.get('data-filename')
        if path.endswith('.lyx'):
            from PyLyX import LyX
            root = LyX(path).get_doc()
            root, info = convert(root)
            body = root[1]
            include_body = LyXobj('div', attrib={'class': 'include body'}, rank=-DEFAULT_RANK)
            obj.append(include_body)
            for element in body:
                include_body.append(element)
