import io
import unittest

import lua


class TestTokenizer(unittest.TestCase):

    def test_tokenize_empty(self):
        text = ''
        obj = lua.Tokenizer(io.StringIO(text).readline)
        g = obj.tokens()
        self.assertEqual(next(g).id, lua.TokenID.END_OF_STREAM)

    def test_tokenize_eol(self):
        text = '\n'
        obj = lua.Tokenizer(io.StringIO(text).readline)
        g = obj.tokens()
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_STREAM)

    def test_tokenize_eols_with_spaces(self):
        text = '\n \n  \n   '
        obj = lua.Tokenizer(io.StringIO(text).readline)
        g = obj.tokens()
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_STREAM)

    def test_single_line_comment(self):
        text = '-- comment \n  -- another comment'
        obj = lua.Tokenizer(io.StringIO(text).readline)
        g = obj.tokens()
        self.assertEqual(next(g).id, lua.TokenID.COMMENT)
        self.assertEqual(next(g).id, lua.TokenID.COMMENT)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_STREAM)

    def test_multiline_comment(self):
        text = '--[[ first line\n second line]]'
        obj = lua.Tokenizer(io.StringIO(text).readline)
        g = obj.tokens()
        self.assertEqual(next(g).id, lua.TokenID.COMMENT)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_STREAM)

    def test_nested_multiline_comment(self):
        text = '--[[ --[==[ first line\n second line ]==] ]]'
        obj = lua.Tokenizer(io.StringIO(text).readline)
        g = obj.tokens()
        self.assertEqual(next(g).id, lua.TokenID.COMMENT)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_STREAM)

    def test_tokenize_keywords(self):
        text = '''\n
nil   \n
false true
and or not
do  end while for in repeat until
break goto
if then else elseif
function local return
        '''
        obj = lua.Tokenizer(io.StringIO(text).readline)
        g = obj.tokens()
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)

        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_NIL)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)

        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_FALSE)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_TRUE)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)

        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_AND)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_OR)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_NOT)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)

        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_DO)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_END)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_WHILE)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_FOR)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_IN)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_REPEAT)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_UNTIL)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)

        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_BREAK)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_GOTO)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)

        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_IF)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_THEN)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_ELSE)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_ELSEIF)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)

        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_FUNCTION)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_LOCAL)
        self.assertEqual(next(g).id, lua.TokenID.KEYWORD_RETURN)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_LINE)
        self.assertEqual(next(g).id, lua.TokenID.END_OF_STREAM)

    def test_simple_strings(self):
        text = '''   'nil' 'hello!'
        "double quoted string"
        '''
        obj = lua.Tokenizer(io.StringIO(text).readline)
        v = [t.value for t in obj.tokens()
             if not t.id == lua.TokenID.END_OF_LINE]
        self.assertEqual(v, ['nil', 'hello!', 'double quoted string', '<EOS>'])

    def test_escapes(self):
        text = '''
"\\a" "\\b" "\\f" "\\n" "\\r" "\\t" "\\v" 
"\\\'" "\\"" "\\\\"
"\\[" "\\]"
'''
        obj = lua.Tokenizer(io.StringIO(text).readline)
        v = [t.value for t in obj.tokens()
             if not t.id == lua.TokenID.END_OF_LINE]
        self.assertEqual(v, ['\a', '\b', '\f', '\n', '\r', '\t', '\v',
                             '\'', '"', '\\', '[', ']', '<EOS>'])


    def test_squared_strings(self):
        text = '''
[[
first
multiline
string
]]
[===[
second
[[multiline]]
string
]===]

        '''
        obj = lua.Tokenizer(io.StringIO(text).readline)
        v = [t.value for t in obj.tokens()
             if not t.id == lua.TokenID.END_OF_LINE]
        self.assertEqual(v, ['first\nmultiline\nstring\n',
                             'second\n[[multiline]]\nstring\n',
                             '<EOS>'])

    def test_label(self):
        text = '::sample_label98::'
        obj = lua.Tokenizer(io.StringIO(text).readline)
        g = obj.tokens()
        t = next(g)
        self.assertEqual(t.id, lua.TokenID.LABEL)
        self.assertEqual(t.value, 'sample_label98')
        self.assertEqual(next(g).value, '<EOS>')

    def test_numbers(self):
        text = '0 +1 -23 4. .5 -6.789 10.11e12 -0.13e-14'
        obj = lua.Tokenizer(io.StringIO(text).readline)
        v = [t.value for t in obj.tokens()
             if not t.id == lua.TokenID.END_OF_LINE]
        self.assertEqual(v, ['0', '+1', '-23', '4.', '.5',
                             '-6.789', '10.11e12', '-0.13e-14',
                             '<EOS>'])

    def test_combos(self):
        text = '... .. ..... <= >= == ~= => =<[](){}=,;:.+-*/^%<>'
        obj = lua.Tokenizer(io.StringIO(text).readline)
        v = [t.id for t in obj.tokens()]
        self.maxDiff = None
        self.assertEqual(v, [lua.TokenID.ELLIPSIS,
                             lua.TokenID.CONCATENATE,
                             lua.TokenID.ELLIPSIS,  # actually there ...
                             lua.TokenID.CONCATENATE,  # ... must be error
                             lua.TokenID.LESS_OR_EQUAL,
                             lua.TokenID.GREATER_OR_EQUAL,
                             lua.TokenID.EQUAL,
                             lua.TokenID.NOT_EQUAL,
                             lua.TokenID.KEY_EQUAL,
                             lua.TokenID.KEY_GT,
                             lua.TokenID.KEY_EQUAL,
                             lua.TokenID.KEY_LT,
                             lua.TokenID.KEY_OPEN_SQUARE_BRACKET,
                             lua.TokenID.KEY_CLOSE_SQUARE_BRACKET,
                             lua.TokenID.KEY_OPEN_ROUND_BRACKET,
                             lua.TokenID.KEY_CLOSE_ROUND_BRACKET,
                             lua.TokenID.KEY_OPEN_CURLY_BRACKET,
                             lua.TokenID.KEY_CLOSE_CURLY_BRACKET,
                             lua.TokenID.KEY_EQUAL,
                             lua.TokenID.KEY_COMMA,
                             lua.TokenID.KEY_SEMICOLON,
                             lua.TokenID.KEY_COLON,
                             lua.TokenID.KEY_DOT,
                             lua.TokenID.KEY_PLUS,
                             lua.TokenID.KEY_MINUS,
                             lua.TokenID.KEY_STAR,
                             lua.TokenID.KEY_SLASH,
                             lua.TokenID.KEY_CARET,
                             lua.TokenID.KEY_PERCENT,
                             lua.TokenID.KEY_LT,
                             lua.TokenID.KEY_GT,
                             lua.TokenID.END_OF_STREAM])

    def test_mix(self):
        text = 'dx=x0+R*sin(angle)--calculate horizontal offset'
        obj = lua.Tokenizer(io.StringIO(text).readline)
        v = [t.value for t in obj.tokens()]
        self.maxDiff = None
        self.assertEqual(v, ['dx', '=', 'x0', '+', 'R', '*',
                             'sin', '(', 'angle', ')',
                             'calculate horizontal offset',
                             '<EOS>'])


if __name__ == '__main__':
    unittest.main()
