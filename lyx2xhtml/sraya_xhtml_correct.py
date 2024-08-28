from sys import argv
from PyLyX.lyx2xhtml.xhtml_correct import import_script, export2xhtml

CSS_FILE = 'main.css'
TREE_VIEW = 'tree_view.js'


def addition_func(current_lines: list[str], counters: dict, pause: bool, depth=0):
    if current_lines[1].startswith('<body'):
        pause = True
    elif current_lines[2] == '<section>\n':
        pause = False

    start, end =  "<ul class='nested'>\n", '</ul>\n'
    if current_lines[2].startswith("<h2 class='section'"):
        current_lines[2] += start
    elif current_lines[2] == '</section>\n' and (current_lines[4].startswith("<h2 class='section'") or current_lines[3] == '</body>\n'):
        current_lines[2] = end + current_lines[2]
    elif current_lines[2].startswith('<div class="proof_item"'):
        if current_lines[3].count('</div>'):
            current_lines[3] += start
        else:
            current_lines[2] += start
    elif counters['proof'] == 1 and current_lines[3] == '</div>\n':
        current_lines[2] += end

    for s in ('סימון:', 'תזכורת:'):
        if current_lines[2].startswith('<li class="labeling_item"') and current_lines[2].endswith(f"<span class='lyxlist'>{s}</span>\n"):
            current_lines[2] = current_lines[2].replace(s, f'<b>{s}</b>')

    if current_lines[3] == '</body>\n':
        current_lines[2] += import_script(max(depth, 0)*'../' + TREE_VIEW)
    return pause


if __name__ == '__main__':
    if len(argv) == 3:
        export2xhtml(argv[1], argv[2], CSS_FILE, -1, addition_func)
    else:
        raise Exception('The input must be a input path and a output path exactly.')
