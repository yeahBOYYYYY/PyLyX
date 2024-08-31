from PyLyX.lyx import LYX, CURRENT_FILE_PATH, join


file = LYX(join(CURRENT_FILE_PATH, 'x.lyx'))
toc = file.load_toc()
new = LYX(join(CURRENT_FILE_PATH, 'y.lyx'), None)
new.write(toc)
