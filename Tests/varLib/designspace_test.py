from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.varLib import designspace
import os
import unittest


class DesignspaceTest(unittest.TestCase):
    def test_load(self):
        self.maxDiff = None
        self.assertEqual(
            designspace.load(_getpath("Designspace.designspace")),

                {'sources':
                  [{'location': {'weight': 0.0},
                    'groups': {'copy': True},
                    'filename': 'DesignspaceTest-Light.ufo',
                    'info': {'copy': True},
                    'name': 'master_1',
                    'lib': {'copy': True}},
                   {'location': {'weight': 1.0},
                    'name': 'master_2',
                    'filename': 'DesignspaceTest-Bold.ufo'}],

                 'instances':
                  [{'location': {'weight': 0.5},
                    'familyname': 'DesignspaceTest',
                    'filename': 'instance/DesignspaceTest-Medium.ufo',
                    'kerning': {},
                    'info': {},
                    'stylename': 'Medium'}],

                 'axes':
                  [{'name': 'weight',
                    'map': [{'input': 0.0, 'output': 10.0},
                            {'input': 401.0, 'output': 66.0},
                            {'input': 1000.0, 'output': 990.0}],
                    'tag': 'wght',
                    'maximum': 1000.0,
                    'minimum': 0.0,
                    'default': 0.0},
                   {'maximum': 1000.0,
                    'default': 250.0,
                    'minimum': 0.0,
                    'name': 'width',
                    'tag': 'wdth'},
                   {'name': 'contrast',
                    'tag': 'cntr',
                    'maximum': 100.0,
                    'minimum': 0.0,
                    'default': 0.0,
                    'labelname': {'de': 'Kontrast', 'en': 'Contrast'}}]
                }
        )

    def test_load2(self):
        self.assertEqual(
            designspace.load(_getpath("Designspace2.designspace")),
                    {'sources': [], 'instances': [{}]})


def _getpath(testfile):
    path, _ = os.path.split(__file__)
    return os.path.join(path, "data", testfile)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
