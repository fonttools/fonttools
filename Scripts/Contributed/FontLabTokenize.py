# -*- coding: utf-8 -*-

"""FontLab Tokenize

Tokenize FontLab’s preview/metrics text into single characters
respecting escaped glyph names (eg. “/A.smcp”) and providing a
lossless reverse function. Sample usage (and actual test suite):

>>> tokenize('/A/B/C')
['/A', '/B', '/C']
>>> tokenize('abcde/B/C')
['a', 'b', 'c', 'd', 'e', '/B', '/C']
>>> tokenize('foo/A.smcp/B.smcp abc')
['f', 'o', 'o', '/A.smcp', '/B.smcp', 'a', 'b', 'c']
>>> p = ['f', 'o', 'o', '/A.smcp', '/B.smcp', 'a', 'b', 'c']
>>> serialize(p)
'foo/A.smcp/B.smcp abc'
>>> tokenize('/a /b /c')
['/a', '/b', '/c']
>>> tokenize('/a/b c')
['/a', '/b', 'c']
>>> tokenize('@a@b@')
['@', 'a', '@', 'b', '@']
>>> tokenize('abc def ghi ')
['a', 'b', 'c', ' ', 'd', 'e', 'f', ' ', 'g', 'h', 'i', ' ']
>>> p = ['a', 'b', 'c', ' ', 'd', 'e', 'f', ' ', 'g', 'h', 'i', ' ']
>>> serialize(p)
'abc def ghi '
>>> serialize(['/a', 'b', '/c', 'd'])
'/a b/c d'
"""

__author__ = 'Antonio Cavedoni <http://cavedoni.com/>'
__version__ = '0.1'
__svnid__ = '$Id$'
__license__ = 'Python'

def tokenize(input):
   tokens = []
   escaped = []
   for i in range(len(input)):
       x = input[i]
       if x != '/' and not escaped:
           tokens.append(x)
       else:
           if x == '/' and not escaped:
               # append the slash so the escaped list is no longer
               # false: starts capturing elements
               escaped.append(x)
           elif x != '/' and escaped:
               if i == (len(input) - 1):
                   escaped.append(x)
                   tokens.append("".join(escaped))
               else:
                   if x == ' ':
                       tokens.append("".join(escaped))
                       escaped = []
                   else:
                       escaped.append(x)
           elif x == '/' and escaped:
               # starts a new sequence so, flush the escaped buffer
               # and start anew
               tokens.append("".join(escaped))
               escaped = [x]

   return tokens

def serialize(tokens):
   series = []
   for i in range(len(tokens)):
       t = tokens[i]
       if t.startswith('/') and i != (len(tokens) - 1):
           if not tokens[i+1].startswith('/'):
               series.append(t + ' ')
           else:
               series.append(t)
       else:
           series.append(t)

   return "".join(series)

if __name__ == "__main__":
   import doctest
   doctest.testmod()
