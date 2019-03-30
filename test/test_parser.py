import unittest

from lua import parse_text


class TestParser(unittest.TestCase):

    def test_empty(self):
        t = parse_text('')
        self.assertEqual(len(t.keys()), 0)

    def test_simple(self):
        t = parse_text('foo = "bar"')
        self.assertEqual(len(t.keys()), 1)
        self.assertEqual(t.keys()[0].str, 'foo')


if __name__ == '__main__':
    unittest.main()
