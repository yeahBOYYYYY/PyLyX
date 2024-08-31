from os.path import expanduser, splitext, split, join
from sys import argv
from PyLyX.helper import correct_name

BIND, UNBIND, BIND_FILE, SELF = '\\bind ', '\\unbind ', '\\bind_file', 'self-insert'
EXTENSION = '.bind'
TITLE_OPEN, TITLE_CLOSE = '##### ', ' #####\n'
SHORTCUTS, FILES, TABLES, CANCELED = 'shortcuts', 'files', 'tables', 'canceled'


def check_line(line):
    if line.startswith(BIND) or line.startswith(UNBIND):
        command, shortcut, space, latex, *end = line.split('"')
        if latex == SELF:
            sign, shortcut, latex = 0, '', ''
        elif command == BIND:
            sign = 1
        elif command == UNBIND:
            sign = -1
        else:
            sign, shortcut, latex = 0, '', ''
        return sign, shortcut, latex
    elif line.startswith(BIND_FILE):
        command, name, *end = line.split()
        return 0, name, ''
    elif line.startswith(TITLE_OPEN) and line.endswith(TITLE_CLOSE):
        title = line[6:-7]
        return 0, '', title
    else:
        return 0, '', ''


def scan_file(full_path: str):
    full_path = correct_name(full_path, '.bind')

    tables = [['BEGINNING', []]]
    canceled_table = []
    the_table = []
    files = []
    
    with open(full_path, 'r', encoding="utf8") as file:
        for line in file:
            sign, shortcut, latex = check_line(line)
            if not sign and shortcut:  # then shortcut is file's name
                files.append(shortcut)
            elif not sign and latex:  # then latex is a text
                tables.append([latex, []])
            elif sign == 1:
                the_table.append([shortcut, latex])
                tables[-1][1].append([shortcut, latex])
            elif sign == -1:
                canceled_table.append([shortcut, latex])

    if not tables[0][1]:
        tables.pop(0)
    return tables, canceled_table, files


def search_shortcut(shortcut, latex, full_path):
    with open(full_path, 'r', encoding='utf8') as file:
        for line in file:
            sign, command, code = check_line(line)
            if not sign and command:  # then command is file's __name
                value, old_shortcut, new_shortcut = search_shortcut(shortcut, latex, join(split(full_path)[0], command))
                if value or new_shortcut:
                    return value, old_shortcut, new_shortcut
            elif sign == 1:
                if (shortcut == command) ^ (latex == code):
                    return False, (shortcut, latex), (command, code)
                elif shortcut == command and latex == code:
                    return True, (), ()
        return False, (shortcut, latex), ()


def compare_files(old_path, new_path, final_path):
    old_path, new_path, final_path = correct_name(old_path, EXTENSION), correct_name(new_path, EXTENSION),\
                                     correct_name(final_path, EXTENSION)
    miss = []
    diff = []
    macros = []
    with open(old_path, 'r', encoding="utf8") as old:
        for line in old:
            sign, shortcut, latex = check_line(line)
            if sign == 1:
                value, old_shortcut, new_shortcut = search_shortcut(shortcut, latex, new_path)
                if shortcut.startswith('M-o') or shortcut.startswith('M-d o'):  # this will change!
                    pass
                elif old_shortcut and old_shortcut[1].find('\\\\kali') != -1:  # this will change!
                    macros.append(old_shortcut)
                elif not value and new_shortcut:
                    diff.append((old_shortcut, new_shortcut))
                elif not (value or new_shortcut):
                    miss.append(old_shortcut)

    with open(final_path, 'x', encoding="utf8") as file:
        file.write('Format 5\n\n')

        file.write('\n' + TITLE_OPEN + 'MISSED' + TITLE_CLOSE)
        for shortcut, code in miss:
            file.write('# ' + BIND + f'"{shortcut}" "{code}"\n')

        file.write('\n' + TITLE_OPEN + 'DIFFERENCES' + TITLE_CLOSE)
        for row1, row2 in diff:
            file.write(BIND + f'"{row1[0]}" "{row1[1]}"\n')
            file.write('# ' + BIND + f'"{row2[0]}" "{row2[1]}"\n\n')

        file.write('\n' + TITLE_OPEN + 'MACROS' + TITLE_CLOSE)  # this will change!
        for shortcut, code in macros:
            file.write('# ' + BIND + f'"{shortcut}" "{code}"\n')


def main():
    old_path, old_name = splitext(argv[1])
    new_path, new_name = splitext(argv[2])
    if len(argv) == 4:
        final_path, final_name = splitext(argv[3])
    else:
        user = expanduser('~')
        final_path, final_name = f'{user}/Downloads/', 'compare.bind'
    compare_files(old_path, new_path, final_path)
    print('Mission complete')


if __name__ == '__main__':
    main()
