#! /usr/bin/env python3

import io
import re
import typing as tp
from lua import _token

KEYWORDS = {
    'nil': _token.TokenID.KEYWORD_NIL,
    'false': _token.TokenID.KEYWORD_FALSE,
    'true': _token.TokenID.KEYWORD_TRUE,
    'do': _token.TokenID.KEYWORD_DO,
    'end': _token.TokenID.KEYWORD_END,
    'while': _token.TokenID.KEYWORD_WHILE,
    'for':  _token.TokenID.KEYWORD_FOR,
    'in': _token.TokenID.KEYWORD_IN,
    'repeat': _token.TokenID.KEYWORD_REPEAT,
    'until': _token.TokenID.KEYWORD_UNTIL,
    'if': _token.TokenID.KEYWORD_IF,
    'then': _token.TokenID.KEYWORD_THEN,
    'else': _token.TokenID.KEYWORD_ELSE,
    'elseif': _token.TokenID.KEYWORD_ELSEIF,
    'local': _token.TokenID.KEYWORD_LOCAL,
    'return': _token.TokenID.KEYWORD_RETURN,
    'and': _token.TokenID.KEYWORD_AND,
    'or': _token.TokenID.KEYWORD_OR,
    'not': _token.TokenID.KEYWORD_NOT,
}

COMMENT = '--'

EOLS: tp.Tuple[str] = (
    '\n\r',
    '\r\n',
    '\n'
)

COMBOS: tp.Tuple[tp.Tuple[str, _token.TokenID]] = (
    ('...', _token.TokenID.ELLIPSIS),
    ('<=', _token.TokenID.KEY_LE),
    ('>=', _token.TokenID.KEY_GE),
    ('==', _token.TokenID.KEY_EQ),
    ('~=', _token.TokenID.KEY_NE),
    ('[', _token.TokenID.KEY_OPEN_SQUARE_BRACKET),
    (']', _token.TokenID.KEY_CLOSE_SQUARE_BRACKET),
    ('(', _token.TokenID.KEY_OPEN_ROUND_BRACKET),
    (')', _token.TokenID.KEY_CLOSE_ROUND_BRACKET),
    ('{', _token.TokenID.KEY_OPEN_CURLY_BRACKET),
    ('}', _token.TokenID.KEY_CLOSE_CURLY_BRACKET),
    ('=', _token.TokenID.KEY_EQUAL),
    (',', _token.TokenID.KEY_COMMA),
    (';', _token.TokenID.KEY_SEMICOLON),
    (':', _token.TokenID.KEY_COLON),
    ('.', _token.TokenID.KEY_DOT),
    ('+', _token.TokenID.KEY_PLUS),
    ('-', _token.TokenID.KEY_MINUS),
    ('*', _token.TokenID.KEY_STAR),
    ('/', _token.TokenID.KEY_SLASH),
    ('^', _token.TokenID.KEY_ROOF),
    ('%', _token.TokenID.KEY_PERCENT),
    ('<', _token.TokenID.KEY_LT),
    ('>', _token.TokenID.KEY_GT),
)

rx_SPACE = re.compile(r'^\s+')
rx_NUMERIC = re.compile(r'^([+-]?(\d+\.\d+|\.\d+|\d+\.?)([eE][+-]?\d+|))')
rx_IDENTIFIER = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*)')
rx_OPEN_LONG_BRACKET = re.compile(r'^\[=*\[')
rx_CLOSE_LONG_BRACKET = re.compile(r'^\]=*\]')


def _eol_check(text: str) -> int:
    for s in EOLS:
        if text.startswith(s):
            return len(s)
    return 0


class Tokenizer:

    def __init__(self, readline: tp.Callable[[], str]):
        self._readline: tp.Callable[[], str] = readline
        self._closing_bracket: bool = False
        self._block_is_comment: bool = False
        self._block_content: str = None
        self._line: str = None
        self._line_no: int = 0
        self._pos_no: int = 0
        self._ok: bool = True

    def _token(self, type: _token.TokenID, value: tp.Any) -> _token.Token:
        if type == _token.TokenID.ERROR:
            self._ok = False
        return _token.Token(self._line_no, self._pos_no, type, value)

    def _match(self, matcher) -> str:
        x = matcher.match(self._line)
        if not x:
            return ''
        return x.group(0)

    def _skip_spaces(self) -> None:
        s = self._match(rx_SPACE)
        if s:
            self._skip(len(s))

    def _skip(self, num: int) -> None:
        self._pos_no += num
        self._line = self._line[num:]

    def _test(self, text: str, term: bool) -> bool:
        if not self._line.startswith(text):
            return False
        if not term:
            return True
        text_len = len(text)
        if len(self._line) == text_len:
            return True
        if re.match(r'\W', self._line[text_len]):
            return True
        return False

    def _get_number(self) -> str:
        s = self._match(rx_NUMERIC)
        if s and self._test(s, True):
            _ = float(s)  # will raise error if line is bad
            return s
        raise ValueError(f'{self._line} is not a valid number')

    def _get_identifier(self) -> str:
        s = self._match(rx_IDENTIFIER)
        if not s:
            raise ValueError(f'not match as a identifier: "{self._line}"')
        return s

    def _get_string_ends_by(self, terminator: str) -> tp.Tuple[str, int]:
        escape_next = False
        s = self._line
        ret = ''
        num = 0
        while True:
            if not s:
                raise ValueError(f"missing terminator: {terminator}")
            if escape_next:
                x = {'a': '\a',
                     'b': '\b',
                     'f': '\f',
                     'n': '\n',
                     'r': '\r',
                     't': '\t',
                     'v': '\v',
                     '\'': '\'',
                     '"': '"',
                     '\\': '\\',
                     '[': '[',
                     ']': ']',
                     }.get(s[0], None)
                if not x:
                    raise ValueError(f"bad escape: {s[0]}")
                ret += x
                escape_next = False
                num += 1
                s = s[1:]
                continue
            if s.startswith(terminator):
                return ret, num + len(terminator)
            if s[0] == '\\':
                escape_next = True
                num += 1
                s = s[1:]
                continue
            ret += s[0]
            num += 1
            s = s[1:]

    def tokens(self):  # -> tp.Generator[_token.Token, None, None]:
        while self._ok:
            if not self._line:
                try:
                    self._line = self._readline()
                    if not self._line:
                        self._line = None
                    # print(f'LINE: {self._line}')
                    self._line_no += 1
                    self._pos_no = 1
                except StopIteration:
                    self._line = None
                if self._line is None:
                    if self._closing_bracket:
                        yield self._token(_token.TokenID.ERROR, 'Missing closing bracket')
                    yield self._token(_token.TokenID.END_OF_STREAM, 'NULL LINE')
                    return
            if self._closing_bracket:
                pos = self._line.find(self._closing_bracket)
                if pos >= 0:
                    self._block_content += self._line[:pos]
                    self._skip(pos + len(self._closing_bracket))
                    # skip first CR[LF]
                    n = _eol_check(self._block_content)
                    if n:
                        self._block_content = self._block_content[n:]
                    if self._block_is_comment:
                        yield self._token(_token.TokenID.COMMENT, self._block_content)
                    else:
                        yield self._token(_token.TokenID.STRING, self._block_content)
                    self._block_content = None
                    self._block_is_comment = None
                    self._closing_bracket = None
                else:
                    self._block_content += self._line
                    self._skip(len(self._line))
                    continue
            # check for end of line
            n = _eol_check(self._line)
            if n:
                self._skip(n)
                yield self._token(_token.TokenID.END_OF_LINE, '')
            # skip trailing spaces
            self._skip_spaces()
            if not self._line:  # readline if there is no token
                continue
            # check for comment
            if self._test(COMMENT, False):
                self._skip(len(COMMENT))
                s = self._match(rx_OPEN_LONG_BRACKET)
                if s:
                    self._closing_bracket = s.replace('[', ']')
                    self._block_is_comment = True
                    self._block_content = ''
                    self._skip(len(s))
                    continue  # search for closing bracket
                else:
                    s = self._line
                    self._skip(len(s))
                    yield self._token(_token.TokenID.COMMENT, s)
                    continue
            # Check for keyword or identifier
            try:
                value = self._get_identifier()
                self._skip(len(value))
                if value in KEYWORDS:
                    yield self._token(KEYWORDS[value], value)
                else:
                    yield self._token(_token.TokenID.NAME, value)
                continue
            except ValueError:
                pass
            # Check for multichar or singlechar combinations
            key = None
            tok = None
            for k, v in COMBOS:
                if self._line.startswith(k):
                    key = k
                    tok = v
                    break
            if key:
                yield self._token(tok, key)
                self._skip(len(key))
                continue
            # Check for numeric value
            try:
                value = self._get_number()
                self._skip(len(value))
                yield self._token(_token.TokenID.NUMBER, value)
                continue
            except ValueError:
                pass
            # check for long string [====[.....]====]
            s = self._match(rx_OPEN_LONG_BRACKET)
            if s:
                self._closing_bracket = s.replace('[', ']')
                self._block_is_comment = False
                self._block_content = ''
                self._skip(len(s))
                continue  # search for closing bracket
            # Check for string "..."
            if self._line.startswith('"'):
                try:
                    self._skip(1)
                    value, rawsize = self._get_string_ends_by('"')
                    self._skip(rawsize)
                    yield self._token(_token.TokenID.STRING, value)
                    continue
                except ValueError:
                    yield self._token(_token.TokenID.ERROR, f'bad "-string: f{self._line}')
                    self._ok = False
                    break
            # Check for string '...'
            if self._line.startswith('\''):
                try:
                    self._skip(1)
                    value, rawsize = self._get_string_ends_by('\'')
                    self._skip(rawsize)
                    yield self._token(_token.TokenID.STRING, value)
                    continue
                except ValueError:
                    yield self._token(_token.TokenID.ERROR, f'bad \'-string: f{self._line}')
                    break
            yield self._token(_token.TokenID.ERROR, f'bad string: {self._line}')


def split(stream: tp.TextIO) -> tp.List[_token.Token]:
    return [t for t in Tokenizer(stream.readline).tokens()]


def split_text(text: str) -> tp.List[_token.Token]:
    return split(io.StringIO(text))


def _test(stream: tp.TextIO) -> None:
    print("---- start ----")
    for t in split(stream):
        print(str(t))
    print("---- done ----")


def _test_file(fname: str) -> None:
    _test(open(fname, mode='r', encoding='utf-8'))


def test1():
    _test_file('../testdata/GatherMate/1.lua')


def test2():
    _test_file('../testdata/Gatherer/1.lua')


def test3():
    _test_file('../testdata/MobInfo2/1.lua')


if __name__ == '__main__':
    test3()