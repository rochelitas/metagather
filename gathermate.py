#! /usr/bin/venv python3

import io
import re
import typing as tp
import pprint as pp


class Dir:
    def __init__(self, parent, key):
        self.__parent_ref = parent;
        self.__parent_key = key;
        self.__data = {}

    @property
    def parent(self):
        return self.__parent_ref

    @property
    def key(self):
        return self.__parent_key

    @property
    def data(self) -> dict:
        return self.__data

    def add(self, key):
        obj = Dir(self, key)
        self.__data[key] = obj
        return obj

    def dict(self) -> dict:
        ret: dict = {}
        for k,v in self.__data.items():
            ret[k] = v.dict() if isinstance(v, Dir) else v
        return ret


class GatherMate:
    def __init__(self):
        self.__db = Dir(None, None)

    @property
    def db(self):
        return self.__db

    def load(self, input: io.TextIOBase):
        rx_space = re.compile(r'^\s*$')
        rx_opendb = re.compile(r'^\s*(\w+)\s*=\s*{\s*$')  # NameOfBase = {
        rx_open0 = re.compile(r'^\s*{\s*$')  # {
        rx_opennest_num = re.compile(r'^\s*\[(\d+)\]\s*=\s*{\s*$')  # [IntKey] = {
        rx_opennest_str = re.compile(r'^\s*\["(.+?)"\]\s*=\s*{\s*$')  # ["NameOfKey"] = {
        rx_kvpair_num = re.compile(r'^\s*\[(\d+)\]\s*=\s*(\d+),?\s*$')  # [IntKey] = IntVal
        rx_kvpair_str = re.compile(r'^\s*\["(.+?)"\]\s*=\s*"(.*?)",?\s*$')  # [StrKey] = StrVal
        rx_endlvl = re.compile(r'^\s*},?\s*(--.*?|)\s*$')  # }
        level: int = 0
        lineno: int = 0
        in_profiles = False

        self.__db = Dir(None, None)
        ref = self.__db

        for rawline in input.readlines():
            lineno += 1
            line = rawline.strip()
            # print(f'{lineno:04d}|{level:01d} {line}')
            if rx_space.fullmatch(line):
                continue
            rr = rx_opendb.fullmatch(line)
            if rr:  # Main level group
                cur_dbname = rr.group(1)
                ref = ref.add(cur_dbname)
                level += 1
                continue
            rr = rx_open0.fullmatch(line)
            if rr:  # Main level group with no key (?)
                cur_dbname = ''
                ref = ref.add(cur_dbname)
                level += 1
                continue
            rr = rx_opennest_num.fullmatch(line)
            if rr:  # Nested level group with int key
                ref = ref.add(int(rr.group(1)))
                level += 1
                continue
            rr = rx_opennest_str.fullmatch(line)
            if rr:  # Nested level group with str key
                ref = ref.add(rr.group(1))
                level += 1
                continue
            rr = rx_kvpair_num.fullmatch(line)
            if rr:  # Key-Value pair with int key
                ref.data[int(rr.group(1))] = int(rr.group(2))
                continue
            rr = rx_kvpair_str.fullmatch(line)
            if rr:  # Key-Value pair with str key
                ref.data[rr.group(1)] = rr.group(2)
                continue
            rr = rx_endlvl.fullmatch(line)
            if rr:  # End of group
                assert level > 0
                level -= 1
                ref = ref.parent
                continue
            assert False, f'unreachable point, line="{line}"'


def deep_merge(a: dict, b:dict) -> dict:
    if a is None and b is None:
        return {}
    elif a is None:
        return b
    elif b is None:
        return a

    keyset = set(a.keys()) | set(b.keys())
    r = {}
    for k in keyset:
        if k in a and k in b:
            assert isinstance(a[k], dict) == isinstance(b[k], dict)
            if isinstance(a[k], dict):
                r[k] = deep_merge(a[k], b[k])
            elif a[k] == b[k]:
                r[k] = a[k]
            else:
                r[k] = a[k]  # forget b[k]
        elif k in a:
            r[k] = a[k]
        else:
            r[k] = b[k]
    return r


def load_db(fname: str) -> dict:
    with open(fname) as input:
        dbx = GatherMate()
        dbx.load(input)
    return dbx.db.dict()


def _save(out: io.TextIOBase, db: dict, name: str) -> None:
    if name not in db:
        print(f'section "{name}" not exists')
        return
    out.write(f'{name} = {{\n')
    keys = set(db[name].keys())
    if '' in keys:
        keys = keys - {''}
        out.write('\t{\n')
        for k,v in db[name][''].items():
            out.write(f'\t\t[{k}] = {v},\n')
        out.write('\t}, -- [1]\n')
    for g in keys:
        out.write(f'\t[{g}] = {{\n')
        for k,v in db[name][g].items():
            out.write(f'\t\t[{k}] = {v},\n')
        out.write('\t},\n')
    out.write('}\n')


def save_db(db: dict, fname: str) -> None:
    with open(fname, 'wt') as out:
        out.write('\n')
        out.write('GatherMateDB = {\n')
        out.write('\t["profileKeys"] = {\n')
        for k, v in db['GatherMateDB']['profileKeys'].items():
            out.write(f'\t\t["{k}"] = "{v}",\n')
        out.write('\t},\n')
        out.write('\t["profiles"] = {\n')
        for k in db['GatherMateDB']['profiles'].keys():
            out.write(f'\t\t["{k}"] = {{\n')
            out.write('\t\t},\n')
        out.write('\t},\n')
        out.write('}\n')
        for k in ('Herb', 'Mine', 'Fish', 'Gas', 'Treasure'):
            _save(out, db, f'GatherMate{k}DB')


if __name__ == '__main__':
    a = load_db('testdata/GatherMate/3.lua')
    b = load_db('testdata/GatherMate/1.lua')
    c = deep_merge(a, b)
    save_db(c, 'testdata/GatherMate/result.lua')
