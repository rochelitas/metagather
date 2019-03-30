#! /usr/bin/env python3

import typing as tp
import abc

from lua._token import TokenID
from lua._token import Token
from lua.utils import escape


class Value(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def create(cls, token: Token) -> 'Value':
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def value(self) -> tp.Any:
        raise NotImplementedError()

    @property
    def str(self) -> str:
        return str(self.value)

    def serialize(self, out: tp.TextIO, nested_level: int) -> None:
        out.write(self.str)


class Nil(Value):
    def __init__(self):
        pass

    @classmethod
    def create(cls, token: Token) -> 'Nil':
        assert token.id in (TokenID.KEYWORD_NIL)
        return Nil()

    @property
    def value(self) -> None:
        return None

    @property
    def str(self) -> str:
        return 'nil'


class Boolean(Value):

    def __init__(self, value: bool):
        self._value = value

    @classmethod
    def create(cls, token: Token) -> 'Boolean':
        assert token.id in (TokenID.KEYWORD_FALSE, TokenID.KEYWORD_TRUE)
        return Boolean(token.value == TokenID.KEYWORD_TRUE)

    @property
    def value(self) -> bool:
        return self._value

    @property
    def str(self) -> str:
        return 'true' if self.value else 'false'


class Integer(Value):

    def __init__(self, value: int):
        self._value = value

    @classmethod
    def create(cls, token: Token) -> 'Integer':
        assert token.id == TokenID.NUMBER
        return Integer(int(token.value))

    @property
    def value(self) -> int:
        return self._value


class Numeric(Value):
    def __init__(self, value: float):
        self._value = value

    @classmethod
    def create(cls, token: Token) -> 'Numeric':
        assert token.id == TokenID.NUMBER
        return Numeric(float(token.value))

    @property
    def value(self) -> float:
        return self._value


class String(Value):

    def __init__(self, value: str):
        self._value = value

    @classmethod
    def create(cls, token: Token) -> 'String':
        assert token.id == TokenID.STRING
        return String(token.value)

    @property
    def value(self) -> str:
        return self._value

    @property
    def str(self) -> str:
        return '"' + escape(self.value) + '"'


class Identifier(Value):

    def __init__(self, value: str):
        self._value = value

    @classmethod
    def create(cls, token: Token) -> 'Identifier':
        assert token.id == TokenID.NAME
        return Identifier(token.value)

    @property
    def value(self) -> str:
        return self._value

    @property
    def str(self) -> str:
        return self.value


class Table(Value):
    def __init__(self):
        self._data: tp.Dict[Value, Value] = {}

    def clear(self) -> None:
        self._data.clear()

    @classmethod
    def create(cls, token: Token) -> 'Table':
        raise NotImplementedError

    def serialize(self, out: tp.TextIO, nested_level: int) -> None:
        out.write('{\n')
        keys: tp.List[Value] = sorted(self._data.keys(), key=lambda x: x.str)
        for ix, key in enumerate(keys, 1):
            skip_key: bool = False
            out.write('\t' * (nested_level + 1))
            if isinstance(key, Integer) and key.value == ix:
                # skip key and store only value
                skip_key = True
            else:
                out.write('[')
                key.serialize(out, nested_level=nested_level+1)
                out.write('] = ')
            self._data[key].serialize(out, nested_level=nested_level+1)
            out.write(',')
            if skip_key:
                out.write(' -- [{}]'.format(ix))
            out.write('\n')
        out.write('\t' * nested_level + '}')

    @property
    def value(self) -> tp.Dict[tp.Any, tp.Any]:
        return dict((k.value, v.value) for k, v in self._data.items())

    @property
    def str(self) -> str:
        return str(self.value)

    @property
    def is_array(self) -> bool:
        return all(isinstance(x, Integer) for x in self._data.keys())

    def set(self, key: Value, value: Value) -> 'Table':
        assert isinstance(key, Value)
        assert isinstance(value, Value)
        self._data[key] = value
        return self

    def append(self, value: tp.Any) -> 'Table':
        return self.set(Integer(len(self._data) + 1), value)

    def keys(self) -> tp.List[Value]:
        return sorted(self._data.keys(), key=lambda x: x.str)


if __name__ == '__main__':
    import sys
    import pprint

    b0 = Boolean(False)
    b1 = Boolean(True)
    n = Integer(12345)
    d = Numeric(12345.678)
    s = String('kaka\tbyaka')
    t = Identifier('value_132')

    tt = Table().append(
        Table().append(b0).append(b1).append(n).append(d).set(s, b0)
    ).append(
        Table().set(String('key1'), String('value for key1'))
               .set(String('key2'), String('value for key2'))
               .set(String('key3'), String(''))
               .set(String('key4'), String('[][][][][]'))
    ).append(Table())
    dd = tt.value

    print(b0.value, b0.str)
    print(b1.value, b1.str)
    print(n.value, n.str)
    print(d.value, d.str)
    print(s.value, s.str)
    print(t.value, t.str)
    tt.serialize(sys.stdout, 0)

