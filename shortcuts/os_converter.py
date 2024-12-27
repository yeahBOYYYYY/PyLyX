from os import scandir
from string import ascii_letters
from os.path import split, join, isfile
from data.data import USER_DIR, DOWNLOADS_DIR
from bind2lyx import SHIFTED_DICT, KEYS_DICT


SHIFTED_OP = {SHIFTED_DICT[key]: key for key in SHIFTED_DICT if key not in ascii_letters}
KEYS_OP = {KEYS_DICT[key]: key for key in KEYS_DICT}


def win2mac(full_path, dst=None):
    path, name = split(full_path)
    if dst is None:
        dst = path
        new_file = join(dst, f'copy_{name}')
    else:
        new_file = join(dst, name)
    with open(new_file, 'x') as new:
        with open(full_path, 'r') as old:
            for line in old:
                for key in KEYS_DICT:
                    if KEYS_DICT[key] in SHIFTED_OP:
                        line = line.replace(f'S-{key}', f'S-{SHIFTED_OP[KEYS_DICT[key]]}')
                        if SHIFTED_OP[KEYS_DICT[key]] in KEYS_OP:
                            line = line.replace(f'S-{SHIFTED_OP[KEYS_DICT[key]]}', f'S-{KEYS_OP[SHIFTED_OP[KEYS_DICT[key]]]}')
                    line = line.replace('S-\\', 'S-backslash')
                new.write(line)


def main():
    src = join(USER_DIR, 'bind')
    for entry in scandir(src):
        path = join(src, entry)
        if isfile(path) and path.endswith('.bind'):
            win2mac(path, DOWNLOADS_DIR)


if __name__ == '__main__':
    main()
