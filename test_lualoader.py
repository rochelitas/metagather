import io

from lua import reader


class TestToken:

    def test_create(self):
        token = reader.Token(1, 2, reader.IDENTIFIER, 'kaka231')
        assert(token.line == 1)
        assert(token.pos == 2)
        assert(token.type == reader.IDENTIFIER)
        assert(token.value == 'kaka231')


class TestTokenizer:

    def match_empty(self):
        t = [reader.Tokenizer(io.StringIO(''))]
        assert(t is None)

    def match_spaces(self):
        t = [reader.Tokenizer(io.StringIO('   \t\n     '))]
        assert(t is None)

    def match_number(self):
        t = [reader.Tokenizer(io.StringIO('0'))]
        assert(len(t) == 1)
