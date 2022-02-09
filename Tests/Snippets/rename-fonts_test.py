# coding=utf-8

"""
This test is for checking function within rename-fonts

"""

import unittest
from fontTools.misc.testTools import FakeFont
from fontTools.ttLib.tables._n_a_m_e import (table__n_a_m_e, NameRecord, nameRecordFormat, nameRecordSize, makeName, log)
from fonttools.Snippets.rename-fonts import get_current_family_name


class RenameFontsTest(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.font = FakeFont(['.nodef', 'A', 'B', 'C'])
        name = table__n_a_m_e()
        name.names = [
            makeName("Copyright", 0, 1, 0, 0),
            makeName("Family Name ID 1", 1, 1, 0, 0),
            makeName("SubFamily Name ID 2", 2, 1, 0, 0),
            makeName("Unique Name ID 3", 3, 1, 0, 0),
            makeName("Full Name ID 4", 4, 1, 0, 0),
            makeName("PS Name ID 6", 6, 1, 0, 0),
            makeName("Version Name ID 5", 5, 1, 0, 0),
            makeName("Trademark Name ID 7", 7, 1, 0, 0),
        ]

        self.font['name'] = name

    def test_get_current_family_name(self):

        result_value = get_current_family_name(self.font['name'])
        self.assertEqual("Family Name ID 1", result_value)

        expected_value = "Family Name ID 16"
        self.font['name'].setName(expected_value, 16, 1, 0, 0)
        result_value = get_current_family_name(self.font['name'])
        self.assertEqual(expected_value, result_value)

        expected_value = "Family Name ID 21"
        self.font['name'].setName(expected_value, 21, 1, 0, 0)
        result_value = get_current_family_name(self.font['name'])
        self.assertEqual(expected_value, result_value)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
