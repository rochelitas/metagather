# -*- python3 -*-

class Config:
    def __init__(self):
        self.__cfg = {}

    @property
    def __getitem__(self, key):
        return self.__cfg.get(key, None)
