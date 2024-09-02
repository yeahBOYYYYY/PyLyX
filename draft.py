from PyLyX.helper import ENVIRONMENTS, LAYOUT, BODY
from PyLyX.lyx import LyX, join, USER, DOWNLOADS_DIR


file = LyX(join(USER, 'Documents', 'newfile1.lyx'))
toc = file.load()
new = LyX(join(DOWNLOADS_DIR, 'y.lyx'), None)
new.write(toc)
