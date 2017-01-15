from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.ttLib.tables._v_m_t_x import table__v_m_t_x
import _h_m_t_x_test
import unittest


class VmtxTableTest(_h_m_t_x_test.HmtxTableTest):

    @classmethod
    def setUpClass(cls):
        cls.tableClass = table__v_m_t_x
        cls.tag = "vmtx"


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
