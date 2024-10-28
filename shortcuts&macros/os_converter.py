from string import ascii_letters
from os.path import split, join
from bind2lyx import SHIFTED_DICT, KEYS_DICT


SHIFTED_OP = {SHIFTED_DICT[key]: key for key in SHIFTED_DICT if key not in ascii_letters}
KEYS_OP = {KEYS_DICT[key]: key for key in KEYS_DICT}


def win2mac(full_path):
    path, name = split(full_path)
    new_file = join(path, f'copy_{name}')
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
