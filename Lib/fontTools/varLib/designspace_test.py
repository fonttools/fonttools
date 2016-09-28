from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.varLib import designspace
import os
import unittest


class DesignspaceTest(unittest.TestCase):
    def test_load(self):
        self.assertEqual(
            designspace.load(_getpath("VarLibTest.designspace")),
                ([{'filename': 'VarLibTest-Light.ufo',
                   'groups': {'copy': True},
                   'info': {'copy': True},
                   'lib': {'copy': True},
                   'location': {'weight': 0.0},
                   'name': 'master_1'},
                  {'filename': 'VarLibTest-Bold.ufo',
                   'location': {'weight': 1.0},
                   'name': 'master_2'}],
                 [{'filename': 'instance/VarLibTest-Medium.ufo',
                   'location': {'weight': 0.5},
                   'familyname': 'VarLibTest',
                   'stylename': 'Medium',
                   'info': {},
                   'kerning': {}}])
        )


def _getpath(testfile):
    path, _ = os.path.split(__file__)
    return os.path.join(path, "testdata", testfile)


if __name__ == "__main__":
    unittest.main()
