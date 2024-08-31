from PyLyX.lyx import LyX, CURRENT_FILE_PATH, join


file = LyX(join(CURRENT_FILE_PATH, 'x.lyx'))
toc = file.load_toc()
new = LyX(join(CURRENT_FILE_PATH, 'y.lyx'), None)
new.write(toc)
