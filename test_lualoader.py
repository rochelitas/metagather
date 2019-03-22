import pytest
import io

import lualoader


class TestToken:

    def test_create(self):
        token = lualoader.Token(1,2,lualoader.IDENTIFIER, 'kaka231')
        assert(token.line == 1)
        assert(token.pos == 2)
        assert(token.type == lualoader.IDENTIFIER)
        assert(token.value == 'kaka231')


class TestTokenizer:

    def match_empty(self):
        t = [lualoader.Tokenizer(io.StringIO(''))]
        assert(t is None)

    def match_spaces(self):
        t = [lualoader.Tokenizer(io.StringIO('   \t\n     '))]
        assert(t is None)

    def match_number(self):
        t = [lualoader.Tokenizer(io.StringIO('0'))]
        assert(len(t) == 1)
