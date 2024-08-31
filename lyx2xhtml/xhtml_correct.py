from os import rename, remove
from os.path import exists, join, split
from sys import argv
from PyLyX.lyx import LyX
from PyLyX.helper import correct_name, detect_lang, RIGHT, LEFT, LANGUAGES

FLOAT_TAG = "<span class='float-caption-Standard float-caption float-caption-standard'>"
MATHJAX_SOURCE = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
WIDTH_DEVICE = '<meta name="viewport" content="width=device-width" />\n'
INSERT_SQUARE = "<div style='text-align: left; line-height: 100%;'><math xmlns='http://www.w3.org/1998/Math/MathML'>\n<mi>■</mi>\n</math>\n</div>\n"
LATEX, MATHML = 'LaTex', 'MathMl'


def import_script(source, identity='', a=False):
    addition = ''
    if identity:
        addition += f'id="{identity}" '
    if a:
        addition += f'async="async" '
    line = f'<script {addition}src="{source}"></script>\n'
    return line


def correct_paren(line, open_paren):
    if line.count('<mo>') or line.count('<mi>'):
        return line, open_paren
    else:
        new_line = ''
        for char in line:
            if char == '(' or char == ')':
                open_paren = not open_paren
                if open_paren:
                    new_line += '('
                else:
                    new_line += ')'
            else:
                new_line += char
    return new_line, open_paren


def extract_content(line):
    content = []
    open_paren = False
    text = ''
    for char in line:
        if char == '<':
            open_paren = True
            if text:
                content.append(text)
                text = ''
        elif char == '>':
            open_paren = False
        elif not open_paren:
            text += char
    return content


def correct_align(line, default_align):
    start = "<div class='standard'"
    opposite_align = LEFT if default_align == RIGHT else RIGHT
    if line == f'text-align: {opposite_align};\n':
        line = f'text-align: {default_align};\n'
    elif line.startswith(start) and not line.count('text-align'):
        content = extract_content(line)
        if content and detect_lang(content[0]) in LANGUAGES[opposite_align]:
            line = line.replace(start, start + f" style='text-align: {opposite_align}'")
    return line


def one_counter(query, line):
    return line.count(f'<{query}') - line.count(f'</{query}>')


def delete_unnecessary(current_lines: list):
    for side in ('left', 'center', 'right'):
        for loc in ('header', 'footer'):
            if current_lines[2].count(f'class="{side}_{loc}_label"'):
                return False

    start = "<div class='standard'"
    end = ('<br />\n', '</div>\n')
    for i in range(3):
        if current_lines[i].startswith(start) and (current_lines[i + 1], current_lines[i + 2]) == end:
            return False

    if current_lines[2].startswith(start) and (current_lines[2].endswith('><br /></div>\n') or current_lines[2].endswith(' </div>\n')):
        return False

    return True


def correct_math(current_lines: list[str], options: dict):
    current_lines[2] = current_lines[2].replace('&', '&amp;')

    start, end = f"<span class='math'>", '</span>\n'
    if current_lines[2].count(start):
        current_lines[2] = current_lines[2].replace(start, start + '\\(')[:len(end)] + '\\)' + end
        return True

    result = False
    start, end = f"<div class='math'>", '</div>'
    if current_lines[2].count(start):
        current_lines[2] = current_lines[2].replace(start, start + '\\[')

    if options[MATH_OPEN] and current_lines[2].count(end):
        current_lines[2] = current_lines[2].replace(end, '\\]' + end, 1)
        options[MATH_OPEN] = False
    return result





def correct_line(current_lines: list[str], counters: dict, options: dict, addition_func=None, args=()):

    write = delete_unnecessary(current_lines)
    if write:
        if current_lines[2].count("class='math'"):
            options[MATH_OPEN] = True
        if options[MATH_OPEN]:
            correct_math(current_lines, options)
            return write

        if current_lines[2] == '<head>\n':
            current_lines[2] += options[CSS] + WIDTH_DEVICE
        elif current_lines[2] == '</head>\n':
            current_lines[2] = import_script(MATHJAX_SOURCE, 'MathJax-script', True) + current_lines[2]
        elif current_lines[2] == '<section>\n':
            options[OPEN_PAREN] = False
        else:
            current_lines[2], options[OPEN_PAREN] = correct_paren(current_lines[2], options[OPEN_PAREN])
            current_lines[2] = current_lines[2].replace(FLOAT_TAG, FLOAT_TAG + '\n' + '<br />\n')
            current_lines[2] = correct_align(current_lines[2], options[DEFAULT_ALIGN])

        if current_lines[4].count(MATHML):
            options[MATH_CODE] = MATHML

        if options[CSS]:
            if current_lines[2] == '<style>\n':
                options[PAUSE] = True
            elif current_lines[2] == '</style>\n':
                options[PAUSE] = False

        for key in counters:
            if current_lines[2].count(f'<div class="{key}">') or current_lines[2].count(f"<div class='{key}'>"):
                counters[key] = 1
            elif counters[key] > 0:
                counters[key] += one_counter('div', current_lines[2])
        if counters['proof'] == 1 and current_lines[3] == '</div>\n':
            current_lines[2] += INSERT_SQUARE

        if addition_func:
            addition_func(current_lines, counters, options, *args)

    return write


CSS, DEPTH, PAUSE, OPEN_PAREN, DEFAULT_ALIGN, MATH_CODE, MATH_OPEN = 'css', 'depth', 'pause', 'open_paren', 'default_align', 'math_code', 'math_open'


def correct_file(path, css_path='', depth=0, addition_func=None):
    if exists(path + '~'):
        remove(path + '~')

    options = {CSS: css_path, DEPTH: depth, PAUSE: False, OPEN_PAREN: False, DEFAULT_ALIGN: '', MATH_CODE: LATEX, MATH_OPEN: False}

    if options[CSS]:
        options[CSS] = f'<link rel="stylesheet" type="text/css" href="{max(depth, 0)*"../" + css_path}" />\n'

    with open(path, 'r', encoding='utf8') as old:
        with open(path + '~', 'x', encoding='utf8') as new:
            old.seek(17)
            line = old.readline()
            options[DEFAULT_ALIGN] = 'right' if line.endswith('lang="he-IL">\n') else 'left'
            old.seek(0)

            counters = {'proof': 0}
            current_lines = ['', '', '', '', '']
            for line in old:
                current_lines.pop(0)
                current_lines.append(line)
                write = correct_line(current_lines, counters, options, addition_func)
                if write and not options[PAUSE]:
                    new.write(current_lines[2])

            new.write('</body>\n</html>\n')

    if exists(path):
        remove(path)
    rename(path + '~', path)


def export2xhtml(input_path, output_path='', css_path='', depth=0, addition_func=None):
    path, name = split(input_path)
    f = LyX(path, name)
    f.update_version()

    output_path = input_path if not output_path else output_path
    output_path = correct_name(output_path, '.xhtml')

    if f.export('xhtml', output_path):
        correct_file(output_path, css_path, depth, addition_func)
        return True
    else:
        return False


def main():
    if 2 < len(argv) < 6:
        input_path = join(argv[1], argv[2])
        output_path = join(argv[3], argv[4]) if len(argv) == 5 else ''
        export2xhtml(input_path, output_path)
    else:
        raise Exception('The input must contain path and name of file, separate by whitespace.')


if __name__ == '__main__':
    main()
