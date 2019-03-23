#! /usr/bin/venv python3

# see
# http://parrot.github.io/parrot-docs0/0.4.7/html/languages/lua/doc/lua51.bnf.html
# https://www.lua.org/manual/5.1/manual.html

import enum


class AutoName(enum.Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


@enum.unique
class TokenID(AutoName):
    KEYWORD_NIL = enum.auto()
    KEYWORD_FALSE = enum.auto()
    KEYWORD_TRUE = enum.auto()
    KEYWORD_DO = enum.auto()
    KEYWORD_END = enum.auto()
    KEYWORD_WHILE = enum.auto()
    KEYWORD_FOR = enum.auto()
    KEYWORD_IN = enum.auto()
    KEYWORD_REPEAT = enum.auto()
    KEYWORD_UNTIL = enum.auto()
    KEYWORD_IF = enum.auto()
    KEYWORD_THEN = enum.auto()
    KEYWORD_ELSE = enum.auto()
    KEYWORD_ELSEIF = enum.auto()
    KEYWORD_LOCAL = enum.auto()
    KEYWORD_RETURN = enum.auto()
    KEYWORD_AND = enum.auto()
    KEYWORD_OR = enum.auto()
    KEYWORD_NOT = enum.auto()

    ELLIPSIS = enum.auto()
    COMMENT = enum.auto()
    LONG_COMMENT = enum.auto()

    KEY_OPEN_SQUARE_BRACKET = enum.auto()  # [
    KEY_CLOSE_SQUARE_BRACKET = enum.auto()  # ]
    KEY_OPEN_ROUND_BRACKET = enum.auto()  # (
    KEY_CLOSE_ROUND_BRACKET = enum.auto()  # )
    KEY_OPEN_CURLY_BRACKET = enum.auto()  # {
    KEY_CLOSE_CURLY_BRACKET = enum.auto()  # }
    KEY_EQUAL = enum.auto()
    KEY_COMMA = enum.auto()
    KEY_SEMICOLON = enum.auto()
    KEY_COLON = enum.auto()
    KEY_DOT = enum.auto()
    KEY_PLUS = enum.auto()
    KEY_MINUS = enum.auto()
    KEY_STAR = enum.auto()
    KEY_SLASH = enum.auto()
    KEY_ROOF = enum.auto()
    KEY_PERCENT = enum.auto()
    KEY_LT = enum.auto()
    KEY_LE = enum.auto()
    KEY_GE = enum.auto()
    KEY_GT = enum.auto()
    KEY_EQ = enum.auto()
    KEY_NE = enum.auto()

    NUMBER = enum.auto()
    STRING = enum.auto()
    NAME = enum.auto()

    END = enum.auto()
    ERROR = enum.auto()


class Token:
    def __init__(self, line: int, pos: int, id: TokenID, value: str):
        self._line: int = line
        self._pos: int = pos
        self._id: TokenID = id
        self._value: str = value

    @property
    def line(self) -> int:
        return self._line

    @property
    def pos(self) -> int:
        return self._pos

    @property
    def id(self) -> TokenID:
        return self._id

    @property
    def id_str(self) -> str:
        return self.id.name

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return 'Token(line={}, pos={}, type={}, value=\'{}\')'.format(
            self.line, self.pos, self.id_str, self.value
        )

    def __repr__(self) -> str:
        return self.__str__()


if __name__ == '__main__':
    token = Token(10, 22, TokenID.NUMBER, '-23.543e-4')
    print(str(token))
