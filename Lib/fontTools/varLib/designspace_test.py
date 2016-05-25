from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.varLib import designspace_load
import os
import unittest


class DesignspaceTest(unittest.TestCase):
    def test_load(self):
        self.assertEqual(
            designspace_load(_getpath("VarLibTest.designspace")),
            (
                [
                    ('VarLibTest-Light.ufo', {'weight': 0.0}, 'master_1'),
                    ('VarLibTest-Bold.ufo', {'weight': 1.0}, 'master_2')
                ],
                [('instance/VarLibTest-Medium.ufo', {'weight': 0.5},
                  'master_2', 'VarLibTest', 'Medium')],
                0
            )
        )


def _getpath(testfile):
    path, _ = os.path.split(__file__)
    return os.path.join(path, "testdata", testfile)


if __name__ == "__main__":
    unittest.main()
