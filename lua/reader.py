#! /usr/bin/env python3

import io
import typing as tp
from lua import _token
from lua import _tokenizer


class ParserError(Exception):
    pass


class TokenBasedError(ParserError):
    def __init__(self, token: _token.Token, text: str):
        msg = 'L:{} C:{}: {}'.format(token.line, token.pos, text)
        super().__init__(msg)


class UnexpectedToken(TokenBasedError):
    def __init__(self,
                 token: _token.Token,
                 expected: tp.Union[_token.TokenID, tp.List[_token.TokenID]] = None):
        if isinstance(expected, (list, tuple)):
            super().__init__(token, 'unexpected token: {}, expects one of {}'.format(
                token.id_str,
                ','.join(x.value for x in expected)))
        elif isinstance(expected, _token.TokenID):
            super().__init__(token, 'unexpected token: {}, expects {}'.format(
                token.id_str, expected.value))
        else:
            super().__init__(token, 'unexpected token: {}'.format(token.id_str))


class UnsupportedToken(TokenBasedError):
    def __init__(self, token: _token.Token):
        super().__init__(token, 'NIY here: {}'.format(token))


class NameMissing(TokenBasedError):
    def __init__(self, token: _token.Token):
        super().__init__(token, 'NAME expected but found {}'.format(token.id_str))


class ExpressionMissing(TokenBasedError):
    def __init__(self, token: _token.Token):
        super().__init__(token, 'exspression expected but found {}'.format(token.id_str))


class FieldMissing(TokenBasedError):
    def __init__(self, token: _token.Token):
        super().__init__(token, 'field expected but found {}'.format(token.id_str))

class CountMismatch(TokenBasedError):
    def __init__(self, token: _token.Token, left: int, right: int):
        super().__init__(token, 'assignment mismatch: left:{}, right:{}'.format(
            left, right
        ))


class Value:
    def __init__(self, type_name: str, raw_value: str):
        self._type_name = type_name
        self._raw_value = raw_value

    @property
    def type_name(self) -> str:
        return self._type_name

    @property
    def raw_value(self) -> str:
        return self._raw_value


class BooleanValue(Value):
    def __init__(self, raw_value: str):
        super().__init__('bool', raw_value)
        self._value: bool = raw_value == 'true'

    @property
    def value(self) -> bool:
        return self._value


class NumericValue(Value):
    def __init__(self, raw_value: str):
        super().__init__('numeric', raw_value)
        self._value: float = float(raw_value)

    @property
    def value(self) -> float:
        return self._value


class StringValue(Value):
    def __init__(self, raw_value: str):
        super().__init__('str', raw_value)

    @property
    def value(self) -> str:
        return self._raw_value

# class Field:
#
# class FieldList:
#
# class TableValue(Value):
#     def __init__(self, raw_value: dict):
#         super().__init__('table', )
#
#     @property
#     def value(self) -> float:
#         return self._raw_value
#
#


class Parser:

    def __init__(self, source: tp.Iterable[_token.Token]):
        self._source: tp.Iterator[_token.Token] = (t for t in source)
        self._t: _token.Token = None
        self._r: dict = {}
        pass

    def parse(self) -> dict:
        while not self._cur.id == _token.TokenID.END_OF_STREAM:
            if self._cur.id in (_token.TokenID.END_OF_LINE,
                                _token.TokenID.COMMENT):
                self._consume()
                continue
            self._parse_stat()
        return self._r

    def _consume(self) -> None:
        self._t = None

    @property
    def _cur(self) -> _token.Token:
        if not self._t:
            self._t = next(self._source)
        return self._t

    @property
    def _next(self) -> _token.Token:
        self._consume()
        return self._cur

    def _parse_stat(self):
        names = self._parse_varlist()
        if self._cur.id != _token.TokenID.KEY_EQUAL:
            raise UnexpectedToken(self._cur, _token.TokenID.KEY_EQUAL)
        self._consume()
        values = self._parse_explist(multiline=False)
        if len(names) != len(values):
            raise CountMismatch(self._cur, len(names), len(values))
        for name, value in zip(names, values):
            self._r[name] = value

    def _parse_varlist(self) -> tp.List[str]:
        names: tp.List[str] = []
        wait_for_name = True
        while True:
            if self._cur.id == _token.TokenID.NAME:
                if not wait_for_name:
                    raise UnexpectedToken(self._cur, [
                        _token.TokenID.KEY_COMMA,
                        _token.TokenID.KEY_EQUAL
                    ])
                names.append(self._cur.value)
                self._consume()
                wait_for_name = False
                continue
            if self._cur.id == _token.TokenID.KEY_COMMA:
                if wait_for_name:
                    raise NameMissing(self._cur)
                self._consume()
                wait_for_name = True
                continue
            if self._cur.id == _token.TokenID.KEY_EQUAL:
                if wait_for_name:
                    raise NameMissing(self._cur)
                break
            raise UnexpectedToken(self._cur)
        return names

    def _parse_explist(self, multiline: bool) -> tp.List[str]:
        exprs: tp.List[str] = []
        wait_for_expr = True
        while True:
            if self._cur.id == _token.TokenID.KEY_COMMA:
                if wait_for_expr:
                    raise ExpressionMissing(self._cur)
                self._consume()
                wait_for_expr = True
                continue
            if self._cur.id == _token.TokenID.END_OF_LINE:
                if multiline:
                    self._consume()
                    continue
                if wait_for_expr:
                    raise ExpressionMissing(self._cur)
                break
            if self._cur.id in (_token.TokenID.KEY_CLOSE_CURLY_BRACKET,
                                _token.TokenID.KEY_CLOSE_ROUND_BRACKET,
                                _token.TokenID.KEY_SEMICOLON,
                                _token.TokenID.END_OF_STREAM):
                if wait_for_expr:
                    raise ExpressionMissing(self._cur)
                break
            if not wait_for_expr:
                raise UnexpectedToken(self._cur)
            exprs.append(self._parse_expression())
            wait_for_expr = False
        return exprs

    def _parse_expression(self) -> tp.Any:
            if self._cur.id == _token.TokenID.KEYWORD_TRUE:
                self._consume()
                return True
            if self._cur.id == _token.TokenID.KEYWORD_FALSE:
                self._consume()
                return False
            if self._cur.id == _token.TokenID.NUMBER:
                if self._cur.value.find('.') >= 0:
                    ret = float(self._cur.value)
                else:
                    ret = int(self._cur.value)
                self._consume()
                return ret
            if self._cur.id == _token.TokenID.STRING:
                ret = self._cur.value
                self._consume()
                return ret
            if self._cur.id == _token.TokenID.NAME:
                raise UnsupportedToken(self._cur)
            if self._cur.id == _token.TokenID.KEY_OPEN_CURLY_BRACKET:
                return self._parse_table()

    def _parse_table(self) -> tp.List[tp.Any]:
        if self._cur.id != _token.TokenID.KEY_OPEN_CURLY_BRACKET:
            raise UnexpectedToken(self._cur, _token.TokenID.KEY_OPEN_CURLY_BRACKET)
        self._consume()
        fields = self._parse_fields()
        if self._cur.id != _token.TokenID.KEY_CLOSE_CURLY_BRACKET:
            raise UnexpectedToken(self._cur, _token.TokenID.KEY_CLOSE_CURLY_BRACKET)
        self._consume()
        return fields

    def _parse_fields(self) -> tp.List[tp.Any]:
        fields: tp.List[tp.Any] = []
        while True:
            if self._cur.id in (_token.TokenID.END_OF_LINE,
                                _token.TokenID.COMMENT):
                self._consume()
                continue
            if self._cur.id in (_token.TokenID.KEY_CLOSE_CURLY_BRACKET,
                                _token.TokenID.KEY_CLOSE_ROUND_BRACKET,
                                _token.TokenID.END_OF_STREAM):
                break
            fields.append(self._parse_field())
            if self._cur.id in (_token.TokenID.KEY_COMMA,
                                _token.TokenID.KEY_SEMICOLON):
                self._consume()
                continue
            break  # no continue-of-list
        return fields

    def _parse_field(self) -> tp.Any:
        if self._cur.id == _token.TokenID.KEY_OPEN_SQUARE_BRACKET:  # [exp] = exp
            self._consume()
            key = self._parse_expression()
            if self._cur.id != _token.TokenID.KEY_CLOSE_SQUARE_BRACKET:
                raise UnexpectedToken(self._cur, _token.TokenID.KEY_CLOSE_SQUARE_BRACKET)
            self._consume()
            if self._cur.id != _token.TokenID.KEY_EQUAL:
                raise UnexpectedToken(self._cur, _token.TokenID.KEY_EQAL)
            self._consume()
            val = self._parse_expression()
            return key, val
        if self._cur.id == _token.TokenID.NAME:  # name = exp
            raise UnsupportedToken(self._cur)
            # name = self._cur.value
            # self._consume()
            # if self._cur.id == _token.TokenID.KEY_EQUAL:
            #     self._consume()
            #     val = self._parse_expression()
            #     return name, val
            # else:
            #     return name
        return self._parse_expression()


def parse_tokens(source: tp.Iterable[_token.Token]) -> dict:
    return Parser(source).parse()


def parse_stream(stream: tp.TextIO) -> dict:
    tokens = [t for t in _tokenizer.Tokenizer(stream.readline).tokens()]
    return parse_tokens(tokens)


def _test(text: str) -> None:
    import pprint
    tokens = list(t for t in _tokenizer.Tokenizer(io.StringIO(text).readline).tokens())
    for t in tokens:
        print(str(t))
    result = parse_tokens(tokens)
    pprint.pprint(result)


def _test_file(name:str) -> None:
    _test(open(name, mode='r', encoding='utf-8').read())


def _test1():
    _test('''
foo = {["bar"]="baz"; [10]=23, "kaka byaka"}
''')


def _test2():
    _test_file('../testdata/GatherMate/test1.lua')
    # _test_file('../testdata/MobInfo2/1.lua')


if __name__ == '__main__':
    _test2()
