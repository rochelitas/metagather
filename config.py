# -*- python3 -*-
import json
import os
import typing as tp

KEY_BASEDIR = 'basedir'
KEY_DATABASE = 'database'

SAVED_VARIABLES = 'SavedVariables'
GATHERMATE = 'GatherMate.lua'
GATHERER = 'Gatherer.lua'

FileNames = tp.NamedTuple('FileNames', [
    ('SavedVariables', tp.List[str]),
    ('GatherMate', tp.List[str]),
    ('Gatherer', tp.List[str])
])

def _gather_filenames(path: str) -> FileNames:
    savedvariable_set = set()
    gathermate_set = set()
    gatherer_set = set()
    for curpath, dirnames, filenames in os.walk(path):
        if 'SavedVariables' in dirnames:
            absname = os.path.abspath(curpath + '/SavedVariables')
            savedvariable_set.add(absname)
        if 'GatherMate.lua' in filenames:
            absname = os.path.abspath(curpath + '/GatherMate.lua')
            gathermate_set.add(absname)
        if 'Gatherer.lua' in filenames:
            absname = os.path.abspath(curpath + '/Gatherer.lua')
            gatherer_set.add(absname)
    return FileNames(list(savedvariable_set),
                     list(gathermate_set),
                     list(gatherer_set))


class Config:
    def __init__(self, name: str = "config.json"):
        self.__cfg: tp.Dict[str, str] = {}
        self.__names: FileNames = FileNames([], [], [])
        if '/' not in name and '\\' not in name:
            name = (
                os.path.dirname(os.path.abspath(__file__)) + '/' + name
            )
        if not self.load(name):
            return
        self.collect()


    def load(self, filename: str) -> bool:
        try:
            with open(filename, 'rt') as input:
                self.__cfg = json.load(input)
                return True
        except IOError:
            self.__cfg = {}
            return False

    def collect(self):
        self.__names = _gather_filenames(self.cfg[KEY_BASEDIR])

    @property
    def cfg(self) -> tp.Dict[str, str]:
        return self.__cfg

    @property
    def dbname(self) -> str:
        return self.__cfg.get(KEY_DATABASE, 'collected-gathermate.lua')

    @property
    def basedir(self) -> str:
        return self.__cfg.get(KEY_BASEDIR, '..')


    @property
    def vardirs(self) -> tp.List[str]:
        return self.__names.SavedVariables

    @property
    def gathermates(self) -> tp.List[str]:
        return self.__names.GatherMate

    @property
    def gatherers(self) -> tp.List[str]:
        return self.__names.Gatherer


if __name__ == '__main__':
    from pprint import pprint
    cfg = Config()
    pprint(cfg.cfg)
    pprint(cfg.basedir)
    pprint(cfg.dbname)
    pprint(cfg.vardirs)
    pprint(cfg.gathermates)
    pprint(cfg.gatherers)
