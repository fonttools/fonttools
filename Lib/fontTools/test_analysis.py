from fontTools import analysis
from difflib import Differ
import filecmp
import sys
import unittest
import tempfile

from pprint import pprint

class TestAnalysis(unittest.TestCase):
    def assertFileMatches(self, expected, actual):
        areSame = filecmp.cmp(expected, actual)
        if not areSame:
            d = Differ()
            expectedLines = open(expected).readlines()
            actualLines = open(actual).readlines()
            result = list(d.compare(expectedLines, actualLines))
            sys.stdout.writelines(result)
        self.assertTrue(areSame)

    def regressionTest(self, args, expected):
        stdout = sys.stdout
        tf = tempfile.NamedTemporaryFile()
        
        sys.stdout = tf
        analysis.main(args)
        sys.stdout = stdout
        tf.flush()
        
        self.assertFileMatches(expected, tf.name)
        tf.close()

    def test_empty_fdef(self):
        analysis.main(["-s", "TestData/FreeMono-empty-fdef.ttx"])
    def test_call_call_endf_endf(self):
        self.regressionTest(["TestData/FreeMono-call-endf.ttx"], "TestData/empty.output")
    def test_subset_A(self):
        self.regressionTest(["-sc", "TestData/FreeMono-subset-A.ttx"], "TestData/FreeMono-subset-A-state-csv.output")

if __name__ == '__main__':
    unittest.main()
