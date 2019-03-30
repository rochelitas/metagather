import io
import unittest

from lua import Value
from lua import Nil
from lua import Identifier
from lua import Boolean
from lua import Integer
from lua import Numeric
from lua import String
from lua import Table
from lua import make_table


class TestValue(unittest.TestCase):

    def test_nil(self):
        v = Nil()
        self.assertIsNone(v.value)
        self.assertEqual(v.str, 'nil')
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(s.getvalue(), 'nil')

    def test_bool_false(self):
        v = Boolean(False)
        self.assertEqual(v.value, False)
        self.assertEqual(v.str, 'false')
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(s.getvalue(), 'false')

    def test_bool_true(self):
        v = Boolean(True)
        self.assertEqual(v.value, True)
        self.assertEqual(v.str, 'true')
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(s.getvalue(), 'true')

    def test_int(self):
        v = Integer(123)
        self.assertEqual(v.value, 123)
        self.assertEqual(v.str, '123')
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(s.getvalue(), '123')

    def test_float(self):
        v = Numeric(123.456)
        self.assertEqual(v.value, 123.456)
        self.assertEqual(v.str, '123.456')
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(s.getvalue(), '123.456')

    def test_str(self):
        v = String('[Hello, World]')
        self.assertEqual(v.value, '[Hello, World]')
        self.assertEqual(v.str, '"\\[Hello, World\\]"')
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(s.getvalue(), '"\\[Hello, World\\]"')

    def test_identifier(self):
        v = Identifier('Sample_123')
        self.assertEqual(v.value, 'Sample_123')
        self.assertEqual(v.str, 'Sample_123')
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(s.getvalue(), 'Sample_123')

    def test_table_empty(self):
        v = Table()
        self.assertEqual(v.value, {})
        self.assertEqual(v.str, '{}')
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(s.getvalue(), '')
        s = io.StringIO()
        v.serialize(s, 1)
        self.assertEqual(s.getvalue(), '{\n}')

    def test_table_mix(self):
        v = (Table().set(Identifier('alpha'),
                         Table().append(Integer(100))
                                .append(Numeric(234.5)))
                                .set(Identifier('beta'),
                                     String('foo bar'))
                                .set(Identifier('gamma'),
                                     Table())
                                .set(Identifier('omega'),
                                     Table().set(String('Key 1'),
                                                 String('Value 1'))
                                            .set(String('Key 2'),
                                                 String('Value 2')))
        )
        self.assertEqual(
            {
                'alpha': {
                    1: 100,
                    2: 234.5,
                },
                'beta': 'foo bar',
                'gamma': {},
                'omega': {
                    'Key 1': 'Value 1',
                    'Key 2': 'Value 2',
                },
            },
            v.value)
        self.assertEqual(
            '{\'alpha\': {1: 100, 2: 234.5}, ' +
            '\'beta\': \'foo bar\', ' +
            '\'gamma\': {}, ' +
            '\'omega\': {\'Key 1\': \'Value 1\', ' +
            '\'Key 2\': \'Value 2\'' +
            '}}',
            v.str
        )
        s = io.StringIO()
        v.serialize(s, 0)
        self.assertEqual(
            'alpha = {\n' +
            '\t100, -- [1]\n' +
            '\t234.5, -- [2]\n' +
            '}\n' +
            'beta = "foo bar"\n' +
            'gamma = {\n' +
            '}\n'
            'omega = {\n' +
            '\t["Key 1"] = "Value 1",\n'
            '\t["Key 2"] = "Value 2",\n'
            '}\n',
            s.getvalue()
        )
        s = io.StringIO()
        v.serialize(s, 1)
        self.assertEqual(
            '{\n' +
            '\talpha = {\n' +
            '\t\t100, -- [1]\n' +
            '\t\t234.5, -- [2]\n' +
            '\t},\n' +
            '\tbeta = "foo bar",\n' +
            '\tgamma = {\n' +
            '\t},\n' +
            '\tomega = {\n' +
            '\t\t["Key 1"] = "Value 1",\n' +
            '\t\t["Key 2"] = "Value 2",\n' +
            '\t},\n' +
            '}',
            s.getvalue()
        )

    def test_make_table_empty(self):
        d = {}
        t = make_table(d)
        self.assertTrue(isinstance(t, Table))
        self.assertEqual({}, t.value)

    def test_make_table_foo_bar(self):
        d = {'foo': 'bar'}
        t = make_table(d)
        s = io.StringIO()
        t.serialize(s, 0)
        self.assertEqual('foo = "bar"\n', s.getvalue())

    def test_make_table_foo_bar2(self):
        d = {'foo': ['bar']}
        t = make_table(d)
        s = io.StringIO()
        t.serialize(s, 0)
        self.assertEqual('foo = {\n\t"bar", -- [1]\n}\n', s.getvalue())

    def test_make_table(self):
        d = {
            'bools': {False: 'F', True: 'T'},
            'mix': ['sss', 123.456, False, {}],
            'L1': {
                'L2': {
                    'L3': 'Val'
                },
            },
            'zero': 0,
        }
        t = make_table(d)
        s = io.StringIO()
        t.serialize(s, 0)
        self.assertEqual(
            'L1 = {\n' +
            '\t["L2"] = {\n' +
            '\t\t["L3"] = "Val",\n' +
            '\t},\n' +
            '}\n' +
            'bools = {\n' +
            '\t[false] = "F",\n' +
            '\t[true] = "T",\n' +
            '}\n' +
            'mix = {\n' +
            '\t"sss", -- [1]\n' +
            '\t123.456, -- [2]\n' +
            '\tfalse, -- [3]\n' +
            '\t{\n' +
            '\t}, -- [4]\n' +
            '}\n' +
            'zero = 0\n',
            s.getvalue()
        )


if __name__ == '__main__':
    unittest.main()
