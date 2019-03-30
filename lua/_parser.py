#! /usr/bin/env python3

import io
import typing as tp

from lua._token import Token
from lua._token import TokenID
from lua._tokenizer import Tokenizer
from lua._value import Value
from lua._value import Nil
from lua._value import Boolean
from lua._value import Integer
from lua._value import Numeric
from lua._value import String
from lua._value import Table
from lua._value import Identifier


class ParserError(Exception):
    pass


class TokenBasedError(ParserError):
    def __init__(self, token: Token, text: str):
        msg = 'L:{} C:{}: {}'.format(token.line, token.pos, text)
        super().__init__(msg)


class UnexpectedToken(TokenBasedError):
    def __init__(self,
                 token: Token,
                 expected: tp.Union[TokenID, tp.List[TokenID]] = None):
        if isinstance(expected, (list, tuple)):
            super().__init__(token, 'unexpected token: {}, expects one of {}'.format(
                token.id_str,
                ','.join(x.value for x in expected)))
        elif isinstance(expected, TokenID):
            super().__init__(token, 'unexpected token: {}, expects {}'.format(
                token.id_str, expected.value))
        else:
            super().__init__(token, 'unexpected token: {}'.format(token.id_str))


class UnsupportedToken(TokenBasedError):
    def __init__(self, token: Token):
        super().__init__(token, 'NIY here: {}'.format(token))


class NameMissing(TokenBasedError):
    def __init__(self, token: Token):
        super().__init__(token, 'NAME expected but found {}'.format(token.id_str))


class ExpressionMissing(TokenBasedError):
    def __init__(self, token: Token):
        super().__init__(token, 'exspression expected but found {}'.format(token.id_str))


class FieldMissing(TokenBasedError):
    def __init__(self, token: Token):
        super().__init__(token, 'field expected but found {}'.format(token.id_str))

class CountMismatch(TokenBasedError):
    def __init__(self, token: Token, left: int, right: int):
        super().__init__(token, 'assignment mismatch: left:{}, right:{}'.format(
            left, right
        ))


class Parser:

    def __init__(self, source: tp.Iterable[Token]):
        self._source: tp.Iterator[Token] = (t for t in source)
        self._t: tp.Optional[Token] = None
        self._r: Table = Table()
        pass

    def parse(self) -> Table:
        # prepare for new run
        self._t = None
        self._r: Table()
        # for each statements to end
        while not self._cur.id == TokenID.END_OF_STREAM:
            # skip all comments and series of the empty lines
            if self._cur.id in (TokenID.END_OF_LINE,
                                TokenID.COMMENT):
                self._consume()
                continue
            # parse statement and update _r
            self._parse_stat()
        return self._r

    def _consume(self) -> None:
        self._t = None

    @property
    def _cur(self) -> Token:
        if not self._t:
            self._t = next(self._source)
        return self._t

    @property
    def _next(self) -> Token:
        self._consume()
        return self._cur

    def _parse_stat(self) -> None:
        names = self._parse_varlist()
        if self._cur.id == TokenID.KEY_EQUAL:
            self._consume()
            values = self._parse_explist(multiline=False)
            if len(names) != len(values):
                raise CountMismatch(self._cur, len(names), len(values))
            for name, value in zip(names, values):
                self._r.set(name, value)
        else:
            for name in names:
                self._r.set(name, Nil())

    def _parse_varlist(self) -> tp.List[Value]:
        names: tp.List[Value] = []
        got_name = False
        while True:
            if self._cur.id == TokenID.NAME:
                if got_name:
                    # Name Name situation
                    raise UnexpectedToken(self._cur, [
                        TokenID.KEY_COMMA,
                        TokenID.KEY_EQUAL
                    ])
                names.append(Identifier.create(self._cur))
                self._consume()
                got_name = True
                continue
            if self._cur.id == TokenID.KEY_COMMA:
                if not got_name:
                    # , or ,,
                    raise NameMissing(self._cur)
                self._consume()
                got_name = False
                continue
            if self._cur.id == TokenID.END_OF_LINE:
                if got_name:
                    # last met token is name, not comma
                    break
                if not names:
                    # no names given so no namelist continues
                    break
                # consume this EOL and continue awaiting for name
                self._consume()
                continue
            if self._cur.id in (TokenID.KEY_EQUAL,
                                TokenID.KEY_SEMICOLON,
                                TokenID.END_OF_STREAM):
                break
            raise UnexpectedToken(self._cur)
        return names

    def _parse_explist(self, multiline: bool) -> tp.List[Value]:
        exprs: tp.List[Value] = []
        wait_for_expr = True
        while True:
            if self._cur.id == TokenID.KEY_COMMA:
                if wait_for_expr:
                    raise ExpressionMissing(self._cur)
                self._consume()
                wait_for_expr = True
                continue
            if self._cur.id == TokenID.END_OF_LINE:
                if multiline:
                    self._consume()
                    continue
                if wait_for_expr:
                    raise ExpressionMissing(self._cur)
                break
            if self._cur.id in (TokenID.KEY_CLOSE_CURLY_BRACKET,
                                TokenID.KEY_CLOSE_ROUND_BRACKET,
                                TokenID.KEY_SEMICOLON,
                                TokenID.END_OF_STREAM):
                if wait_for_expr:
                    raise ExpressionMissing(self._cur)
                break
            if not wait_for_expr:
                raise UnexpectedToken(self._cur)
            exprs.append(self._parse_expression())
            wait_for_expr = False
        return exprs

    def _parse_expression(self) -> Value:
        if self._cur.id in (TokenID.KEYWORD_FALSE,
                            TokenID.KEYWORD_TRUE):
            ret = Boolean.create(self._cur)
            self._consume()
            return ret
        if self._cur.id == TokenID.NUMBER:
            if self._cur.value.find('.') >= 0:
                ret = Numeric.create(self._cur)
            else:
                ret = Integer.create(self._cur)
            self._consume()
            return ret
        if self._cur.id == TokenID.STRING:
            ret = String.create(self._cur)
            self._consume()
            return ret
        if self._cur.id == TokenID.NAME:
            raise UnsupportedToken(self._cur)
        if self._cur.id == TokenID.KEY_OPEN_CURLY_BRACKET:
            return self._parse_table()
        raise UnexpectedToken(self._cur)

    def _parse_table(self) -> Table:
        if self._cur.id != TokenID.KEY_OPEN_CURLY_BRACKET:
            raise UnexpectedToken(self._cur, TokenID.KEY_OPEN_CURLY_BRACKET)
        self._consume()
        fields = self._parse_fields()
        if self._cur.id != TokenID.KEY_CLOSE_CURLY_BRACKET:
            raise UnexpectedToken(self._cur, TokenID.KEY_CLOSE_CURLY_BRACKET)
        self._consume()
        ret = Table()
        for field in fields:
            if len(field) == 1:
                ret.append(field[0])
            else:
                ret.set(field[0], field[1])
        return ret

    def _parse_fields(self) -> tp.List[tp.List[Value]]:
        fields: tp.List[tp.List[Value]] = []
        while True:
            if self._cur.id in (TokenID.END_OF_LINE,
                                TokenID.COMMENT):
                self._consume()
                continue
            if self._cur.id in (TokenID.KEY_CLOSE_CURLY_BRACKET,
                                TokenID.KEY_CLOSE_ROUND_BRACKET,
                                TokenID.END_OF_STREAM):
                break
            fields.append(self._parse_field())
            if self._cur.id in (TokenID.KEY_COMMA,
                                TokenID.KEY_SEMICOLON):
                self._consume()
                continue
            break  # no continue-of-list
        return fields

    def _parse_field(self) -> tp.List[Value]:
        if self._cur.id == TokenID.KEY_OPEN_SQUARE_BRACKET:
            # [exp] = exp
            self._consume()
            key = self._parse_expression()
            if self._cur.id != TokenID.KEY_CLOSE_SQUARE_BRACKET:
                raise UnexpectedToken(self._cur,
                                      TokenID.KEY_CLOSE_SQUARE_BRACKET)
            self._consume()
            if self._cur.id != TokenID.KEY_EQUAL:
                raise UnexpectedToken(self._cur, TokenID.KEY_EQAL)
            self._consume()
            val = self._parse_expression()
            return [key, val]
        if self._cur.id == TokenID.NAME:  # name = exp
            raise UnsupportedToken(self._cur)
            # name = self._cur.value
            # self._consume()
            # if self._cur.id == TokenID.KEY_EQUAL:
            #     self._consume()
            #     val = self._parse_expression()
            #     return name, val
            # else:
            #     return name
        return [self._parse_expression()]  # list in one item


def parse_tokens(source: tp.Iterable[Token]) -> Table:
    return Parser(source).parse()


def parse_stream(stream: tp.TextIO) -> Table:
    return parse_tokens(Tokenizer(stream.readline).tokens())


def parse_text(text: str) -> Table:
    return parse_stream(io.StringIO(text))


def _test(text: str) -> None:
    print('--- text ---')
    print(text)
    result = parse_text(text)
    print("--- serialised ---")
    import sys
    result.serialize(sys.stdout, 0)
    print("--- end ---")


def _test_file(name:str) -> None:
    _test(open(name, mode='r', encoding='utf-8').read())


def _test1():
    _test('''
foo = {["bar"]="baz"; [10]=23, "kaka byaka"}
''')


def _test2():
    # _test_file('../testdata/GatherMate/test1.lua')
    _test_file('../testdata/MobInfo2/1.lua')


if __name__ == '__main__':
    _test2()
