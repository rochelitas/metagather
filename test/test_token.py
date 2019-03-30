import unittest
import lua


class TestToken(unittest.TestCase):
    def setUp(self) -> None:
        self.token = lua.Token(12, 34, lua.TokenID.STRING, 'Quick and dirty')

    def test_properties(self):
        self.assertEqual(self.token.line, 12)
        self.assertEqual(self.token.pos, 34)
        self.assertEqual(self.token.id, lua.TokenID.STRING)
        self.assertEqual(self.token.value, 'Quick and dirty')

    def test_str(self):
        s = str(self.token)
        self.assertEqual(
            s,
            'Token(line=12, pos=34, type=STRING, value=\'Quick and dirty\')',
        )

    def test_repr(self):
        s = repr(self.token)
        self.assertEqual(
            s,
            'Token(line=12, pos=34, type=STRING, value=\'Quick and dirty\')',
        )

if __name__ == '__main__':
    unittest.main()
