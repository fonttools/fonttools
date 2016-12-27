from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.misc.testTools import MockFont
from fontTools import mtiLib
import difflib
import os
import sys
import unittest


class BuilderTest(unittest.TestCase):
    # Feature files in testdata/*.txt; output gets compared to testdata/*.ttx.
    TESTS = {
        None: (
            #'mti/cmap',
        ),
        'cmap': (
            #'mti/cmap',
        ),
        'GSUB': (
            'featurename-backward',
            'featurename-forward',
            'lookupnames-backward',
            'lookupnames-forward',
            'mixed-toplevels',

            'mti/scripttable',
            'mti/chainedclass',
            'mti/chainedcoverage',
            'mti/chained-glyph',
            'mti/gsubalternate',
            'mti/gsubligature',
            'mti/gsubmultiple',
            'mti/gsubreversechanined',
            'mti/gsubsingle',
        ),
        'GPOS': (
            'mti/scripttable',
            'mti/chained-glyph',
            'mti/gposcursive',
            'mti/gposkernset',
            'mti/gposmarktobase',
            'mti/gpospairclass',
            'mti/gpospairglyph',
            'mti/gpossingle',
            'mti/mark-to-ligature',
        ),
        'GDEF': (
            'mti/gdefattach',
            'mti/gdefclasses',
            'mti/gdefligcaret',
            'mti/gdefmarkattach',
            'mti/gdefmarkfilter',
        ),
    }
    # TODO:
    # https://github.com/Monotype/OpenType_Table_Source/issues/12
    #
    #        'mti/featuretable'
    #        'mti/contextclass'
    #        'mti/contextcoverage'
    #        'mti/context-glyph'

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @staticmethod
    def getpath(testfile):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "testdata", testfile)

    def expect_ttx(self, expected_ttx, actual_ttx, fromfile=None, tofile=None):
        expected = [l+'\n' for l in expected_ttx.split('\n')]
        actual = [l+'\n' for l in actual_ttx.split('\n')]
        if actual != expected:
            print('\n')
            for line in difflib.unified_diff(
                    expected, actual, fromfile=fromfile, tofile=tofile):
                sys.stdout.write(line)
            self.fail("TTX output is different from expected")

    def check_mti_file(self, name, tableTag=None):

        xml_expected_path = self.getpath("%s.ttx" % name + ('.'+tableTag if tableTag is not None else ''))
        with open(xml_expected_path, 'rt', encoding="utf-8") as xml_expected_file:
            xml_expected = xml_expected_file.read()

        font = MockFont()

        with open(self.getpath("%s.txt" % name), 'rt', encoding="utf-8") as f:
            table = mtiLib.build(f, font, tableTag=tableTag)

        if tableTag is not None:
            self.assertEqual(tableTag, table.tableTag)
        tableTag = table.tableTag

        # Make sure it compiles.
        blob = table.compile(font)

        # Make sure it decompiles.
        decompiled = table.__class__()
        decompiled.decompile(blob, font)

        # XML from built object.
        writer = XMLWriter(StringIO(), newlinestr='\n')
        writer.begintag(tableTag); writer.newline()
        table.toXML(writer, font)
        writer.endtag(tableTag); writer.newline()
        xml_built = writer.file.getvalue()

        # XML from decompiled object.
        writer = XMLWriter(StringIO(), newlinestr='\n')
        writer.begintag(tableTag); writer.newline()
        decompiled.toXML(writer, font)
        writer.endtag(tableTag); writer.newline()
        xml_binary = writer.file.getvalue()

        self.expect_ttx(xml_binary,   xml_built, fromfile='decompiled',      tofile='built')
        self.expect_ttx(xml_expected, xml_built, fromfile=xml_expected_path, tofile='built')

def generate_mti_file_test(name, tableTag=None):
    return lambda self: self.check_mti_file(os.path.join(*name.split('/')), tableTag=tableTag)


for tableTag,tests in BuilderTest.TESTS.items():
    for name in tests:
        setattr(BuilderTest, "test_MtiFile_%s" % name,
                generate_mti_file_test(name, tableTag=tableTag))


if __name__ == "__main__":
    unittest.main()
