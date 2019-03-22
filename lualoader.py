#! /usr/bin/venv python3

import io
import re
import typing as tp

NIL = 1
BOOLEAN = 2
NUMBER = 3
STRING = 4
TABLE = 5
IDENTIFIER = 6
ASSIGNMENT = 7
COMMA = 8
TABLE_BEGIN = 9
TABLE_END = 10
ERROR = -1

BOOLEAN_TRUE = 'true'
BOOLEAN_FALSE = 'false'

rx_SPACE = re.compile(r'^\s+')
rx_NUMERIC = re.compile(
    r'^([+-]?(\d+\.\d+|\d+\.|\d+|\.\d+)([eE][+-]?\d+|))'
)
rx_IDENTIFIER = re.compile(r'^([A-Za-z]\w*)')


class Token:
    def __init__(self, line: int, pos: int, type: int, value: tp.Any):
        self._line: int = line
        self._pos: int = pos
        self._type: int = type
        self._value: tp.Any = value

    @property
    def line(self) -> int:
        return self._line

    @property
    def pos(self) -> int:
        return self._pos

    @property
    def type(self) -> int:
        return self._type

    @property
    def type_name(self) -> str:
        return {
            NIL: 'NIL',
            BOOLEAN: 'BOOLEAN',
            NUMBER: 'NUMBER',
            STRING: 'STRING',
            TABLE: 'TABLE',
            IDENTIFIER: 'IDENTIFIER',
            ASSIGNMENT: 'ASSIGNMENT',
            COMMA: 'COMMA',
            TABLE_BEGIN: 'TABLE_BEGIN',
            TABLE_END: 'TABLE_END',
            ERROR: 'ERROR',
        }.get(self._type, 'UNKNOWN')

    @property
    def value(self) -> tp.Any:
        return self._value


    def __str__(self) -> str:
        return 'Token(line={}, pos={}, type={}, value=\'{}\')'.format(
            self.line, self.pos, self.type_name, self.value
        )


class Tokenizer:

    def __init__(self, readline):
        self._readline = readline
        self._line: str = None
        self._line_no: int = 0
        self._pos_no: int = 0
        self._ok: bool = True

    def _token(self, type: int, value: tp.Any) -> Token:
        if type == ERROR:
            self._ok = False
        return Token(self._line_no, self._pos_no, type, value)

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
        if not self._test(s, True):
            raise ValueError(f'{self._line} has badly terminated number')
        _ = float(s)  # will raise error if line is bad
        return s

    def _get_identifier(self) -> str:
        s = self._match(rx_IDENTIFIER)
        if not s:
            raise ValueError(f'not match as a identifier: "{self._line}"')
        return s

    def _get_string_ends_by(self, terminator: str) -> str:
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

    def tokens(self) -> tp.Generator[Token, None, None]:
        while self._ok:
            if not self._line:
                try:
                    self._line = self._readline()
                    if not self._line:
                        print("NULL LINE")
                        return
                    print("LINE: " + self._line)
                    self._line_no += 1
                    self._pos_no = 1
                except StopIteration:
                    return
            # skip trailing spaces
            self._skip_spaces()
            if not self._line:  # readline if there is no token
                continue
            # Check for boolean value: true
            if self._test(BOOLEAN_TRUE, True):
                self._skip(len(BOOLEAN_TRUE))
                yield self._token(BOOLEAN, True)
                continue
            # Check for boolean value: false
            if self._test(BOOLEAN_FALSE, True):
                self._skip(len(BOOLEAN_FALSE))
                yield self._token(BOOLEAN, False)
                continue
            # Check for numeric value
            try:
                value = self._get_number()
                self._skip(len(value))
                yield self._token(NUMBER, float(value))
                continue
            except ValueError:
                pass
            # Check for identifier
            try:
                value = self._get_identifier()
                self._skip(len(value))
                yield self._token(IDENTIFIER, value)
                continue
            except ValueError:
                pass
            # Check for string "..."
            if self._line.startswith('"'):
                try:
                    self._skip(1)
                    value, rawsize = self._get_string_ends_by('"')
                    self._skip(rawsize)
                    yield self._token(STRING, value)
                    continue
                except ValueError:
                    yield self._token(ERROR, f'bad "-string: f{self._line}')
                    self._ok = False
                    break
            # Check for string '...'
            if self._line.startswith('\''):
                try:
                    self._skip(1)
                    value, rawsize = self._get_string_ends_by('\'')
                    self._skip(rawsize)
                    yield self._token(STRING, value)
                    continue
                except ValueError:
                    yield self._token(ERROR, f'bad \'-string: f{self._line}')
                    break
            # Check for string ['...']
            if self._line.startswith('[\''):
                try:
                    self._skip(2)
                    value, rawsize = self._get_string_ends_by('\']')
                    self._skip(rawsize)
                    yield self._token(STRING, value)
                    continue
                except ValueError:
                    yield self._token(ERROR, f'bad [\'-string: f{self._line}')
                    break
            # Check for string ["..."]
            if self._line.startswith('["'):
                try:
                    self._skip(2)
                    value, rawsize = self._get_string_ends_by('"]')
                    self._skip(rawsize)
                    yield self._token(STRING, value)
                    continue
                except ValueError:
                    yield self._token(ERROR, f'bad ["-string: f{self._line}')
                    break
            # Check for string [[...]]
            if self._line.startswith('[['):
                try:
                    self._skip(2)
                    value, rawsize = self._get_string_ends_by(']]')
                    self._skip(rawsize)
                    yield self._token(STRING, value)
                    continue
                except ValueError:
                    yield self._token(ERROR, f'bad [[-string: f{self._line}')
                    break
            # Check for assignment
            if self._line.startswith('='):
                self._skip(1)
                yield self._token(ASSIGNMENT, '=')
                continue
            # Check for begin of comma
            if self._line.startswith(','):
                self._skip(1)
                yield self._token(COMMA, ',')
                continue
            # Check for begin of table
            if self._line.startswith('{'):
                self._skip(1)
                yield self._token(TABLE_BEGIN, '{')
                continue
            # Check for end of table
            if self._line.startswith('}'):
                self._skip(1)
                yield self._token(TABLE_END, '}')
                continue
            yield self._token(ERROR, f'bad string: {self._line}')


def split(stream: io.IOBase) -> tp.List[Token]:
    return [t for t in Tokenizer(stream.readline).tokens()]


def split_text(text: str) -> tp.List[Token]:
    return split(io.StringIO(text))


if __name__ == '__main__':
    print("---- start ----")
    for t in split_text('value1 = {["foo"] = 12.0e1, ["bar"] = Sample}'):
        print(str(t))
    print("---- done ----")
