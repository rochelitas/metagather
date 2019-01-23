#! /usr/bin/venv python3

import io
import re
import typing as tp


class Dir:
    def __init__(self, parent, key):
        self.__parent_ref = parent
        self.__parent_key = key
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
        for k, v in self.__data.items():
            ret[k] = v.dict() if isinstance(v, Dir) else v
        return ret


class GatherMate:
    def __init__(self):
        self.__db = Dir(None, None)

    @property
    def db(self):
        return self.__db

    def load(self, inp: io.TextIOBase):
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

        for raw_line in inp.readlines():
            lineno += 1
            line = raw_line.strip()
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
            return empty_gathermate()  # wrong file format


def empty_gathermate():
    return {
        'GatherMateDB': {
            'profileKeys': {},
            'profiles': {}
        },
        'GatherMateHerbDB': {},
        'GatherMateMineDB': {},
        'GatherMateFishDB': {},
        'GatherMateGasDB': {},
        'GatherMateTreasureDB': {}
    }


# Statistics = tp.Dict[str, tp.Any]
Statistics = tp.NamedTuple('Statistics', [
    ('profileKeys', tp.Optional[int]),
    ('profiles', tp.Optional[int]),
    ('counts', tp.Dict[str, tp.Optional[int]]),
    ('nodes_total', int),
    ('zones_total', int)
])


def calc_statistics(base: dict) -> Statistics:
    """
    :param base: base for analyse
            'GatherMateDB': {
                'profileKeys': {},
                'profiles': {}
            },
            'GatherMateHerbDB': {},
            'GatherMateMineDB': {},
            'GatherMateFishDB': {},
            'GatherMateGasDB': {},
            'GatherMateTreasureDB': {}
    :return: Statistics
    """
    num_profile_keys: tp.Optional[int] = None
    num_profiles: tp.Optional[int] = None
    counts: tp.Dict[str, tp.Optional[int]] = {}

    if 'GatherMateDB' in base:
        if 'profileKeys' in base['GatherMateDB']:
            num_profile_keys = len(base['GatherMateDB']['profileKeys'])
        if 'profiles' in base['GatherMateDB']:
            num_profiles = len(base['GatherMateDB']['profiles'])
    total_nodes = 0
    zones = set()
    counts: tp.Dict[str, tp.Optional[int]]
    for k in ('Herb', 'Mine', 'Fish', 'Gas', 'Treasure'):
        name = f'GatherMate{k}DB'
        if name in base:
            zones.update(set(base[name].keys()))
            counts[k] = sum(len(base[name][zone]) for zone in base[name])
            total_nodes += counts[k]
        else:
            counts[k] = None
    return Statistics(num_profile_keys,
                      num_profiles,
                      counts,
                      total_nodes,
                      len(zones))


def safe0(v: tp.Optional[int]) -> int:
    return v if v is not None else 0


def calc_grow(before: Statistics, after: Statistics) -> Statistics:
    return Statistics(
        safe0(after.profileKeys) - safe0(before.profileKeys),
        safe0(after.profiles) - safe0(before.profiles),
        {
            'Herb': safe0(after.counts['Herb']) - safe0(before.counts['Herb']),
            'Mine': safe0(after.counts['Mine']) - safe0(before.counts['Mine']),
            'Fish': safe0(after.counts['Fish']) - safe0(before.counts['Fish']),
            'Gas': safe0(after.counts['Gas']) - safe0(before.counts['Gas']),
            'Treasure': safe0(after.counts['Treasure']) - safe0(before.counts['Treasure'])
        },
        safe0(after.nodes_total) - safe0(before.nodes_total),
        safe0(after.zones_total) - safe0(before.zones_total)
    )


def print_statistics_changes(before: Statistics, after: Statistics) -> None:
    grow = calc_grow(before, after)
    dirty = False
    print("Information about base changes")
    for k in ('Herb', 'Mine', 'Fish', 'Gas', 'Treasure'):
        if grow.counts[k] > 0:
            print("{}: {} nodes added".format(k, grow.counts[k]))
            dirty = True
    if grow.nodes_total > 0:
        print("{} nodes added in total".format(grow.nodes_total))
        dirty = True
    if grow.zones_total > 0:
        print("{} zones added".format(grow.zones_total))
        dirty = True
    if not dirty:
        print("... no changes at all")


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


def load_db(filename: str) -> dict:
    try:
        inp: tp.TextIO
        with open(filename, encoding='utf-8') as inp:
            dbx = GatherMate()
            dbx.load(inp)
        return dbx.db.dict()
    except IOError:
        return empty_gathermate()


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
    out: tp.TextIO
    with open(fname, 'wt', encoding='utf-8') as out:
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
