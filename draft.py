# from PyLyX.helper import ATTRIB
from PyLyX.lyx import LyX, join, DOWNLOADS_DIR, OBJECTS, TAG
# from PyLyX.loader import extract_cmd
# from json import dumps


# def unknown(line, d: dict):
#     if line.startswith('\\'):
#         cmd = line.split()
#         if len(cmd) <= 3:
#             command, category, details, text = extract_cmd(line)
#             if not (command in OBJECTS and category in OBJECTS[command] and details in OBJECTS[command][category]):
#                 d[command] = {category: {details: {TAG: '', ATTRIB: {}}}}
#     return line
#
#
# dic = {}
# file.line_functions(unknown, (dic, ))
# dic = dumps(dic)
# with open(join(DOWNLOADS_DIR, 'unknown.json'), 'w', encoding='utf8') as x:
#     x.write(dic)


file = LyX(join(DOWNLOADS_DIR, 'x.lyx'))
toc = file.load()
new = LyX(join(DOWNLOADS_DIR, 'y.lyx'), None)
new.write(toc)
