#! /usr/bin/env python3

import typing as tp


def escape(s: str) -> str:
    return ''.join(
        {'\a': '\\a',
         '\b': '\\b',
         '\f': '\\f',
         '\n': '\\n',
         '\r': '\\r',
         '\t': '\\t',
         '\v': '\\v',
         '\'': '\\\'',
         '"': '\\"',
         '\\': '\\\\',
         '[': '\\[',
         ']': '\\]',
         }.get(x, x)
        for x in s)

def unescape(s: str) -> str:
    r = ''
    escape: bool = False
    for c in s:
        if escape:
            r += {'a': '\a',
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
                  ']': ']'}.get(c, c)
            escape = False
        else:
            if c == '\\':
                escape = True
            else:
                r += c
    return r


if __name__ == '__main__':
    s = 'kaka\a\b\f\n\r\t\v\'"\\[]byaka'
    e = escape(s)
    s2 = unescape(e)
    e2 = escape(s2)
    assert s == s2
    assert e == e2
    print(e)
