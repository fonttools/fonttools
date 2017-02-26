from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.varLib import designspace
import os
import unittest


class DesignspaceTest(unittest.TestCase):
    def test_load(self):
        self.assertEqual(
            designspace.load(_getpath("VarLibTest.designspace")),

                # axes
                ([{'map': [{'input': 0.0, 'output': 10.0},
                           {'input': 401.0, 'output': 66.0},
                           {'input': 1000.0, 'output': 990.0}],
                   'name': 'weight',
                   'default': 0.0,
                   'tag': 'wght',
                   'maximum': 1000.0,
                   'minimum': 0.0},
                  {'default': 250.0,
                   'minimum': 0.0,
                   'tag': 'wdth',
                   'maximum': 1000.0,
                   'name': 'width'},
                  {'name': 'contrast',
                   'default': 0.0,
                   'tag': 'cntr',
                   'maximum': 100.0,
                   'minimum': 0.0,
                   'labelname': {'de': 'Kontrast', 'en': 'Contrast'}}],

                 # masters (aka sources)
                 [{'info': {'copy': True},
                   'name': 'master_1',
                   'lib': {'copy': True},
                   'filename': 'VarLibTest-Light.ufo',
                   'location': {'weight': 0.0},
                   'groups': {'copy': True}},
                  {'location': {'weight': 1.0},
                   'name': 'master_2',
                   'filename': 'VarLibTest-Bold.ufo'}],

                 # instances
                 [{'info': {},
                   'familyname': 'VarLibTest',
                   'filename': 'instance/VarLibTest-Medium.ufo',
                   'kerning': {},
                   'location': {'weight': 0.5},
                   'stylename': 'Medium'}])
        )


def _getpath(testfile):
    path, _ = os.path.split(__file__)
    return os.path.join(path, "data", testfile)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
