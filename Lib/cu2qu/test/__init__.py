import os
try:
    from ufoLib.glifLib import GlyphSet
except ImportError:
    from robofab.glifLib import GlyphSet

DATADIR = os.path.join(
    os.path.abspath(os.path.dirname(os.path.realpath(__file__))), 'data')
CUBIC_GLYPHS = GlyphSet(os.path.join(DATADIR, 'cubic'))
QUAD_GLYPHS = GlyphSet(os.path.join(DATADIR, 'quadratic'))

import unittest
# Python 3 renamed 'assertRaisesRegexp' to 'assertRaisesRegex', and fires
# deprecation warnings if a program uses the old name.
if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp
