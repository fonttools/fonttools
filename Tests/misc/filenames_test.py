from __future__ import unicode_literals
import unittest
from fontTools.misc.filenames import userNameToFileName

class FilenamesTest(unittest.TestCase):

	def test_names(self):
		self.assertEqual(userNameToFileName("a"),"a")
		self.assertEqual(userNameToFileName("A"), "A_")
		self.assertEqual(userNameToFileName("AE"), "A_E_")
		self.assertEqual(userNameToFileName("Ae"), "A_e")
		self.assertEqual(userNameToFileName("ae"), "ae")
		self.assertEqual(userNameToFileName("aE"), "aE_")
		self.assertEqual(userNameToFileName("a.alt"), "a.alt")
		self.assertEqual(userNameToFileName("A.alt"), "A_.alt")
		self.assertEqual(userNameToFileName("A.Alt"), "A_.A_lt")
		self.assertEqual(userNameToFileName("A.aLt"), "A_.aL_t")
		self.assertEqual(userNameToFileName(u"A.alT"), "A_.alT_")
		self.assertEqual(userNameToFileName("T_H"), "T__H_")
		self.assertEqual(userNameToFileName("T_h"), "T__h")
		self.assertEqual(userNameToFileName("t_h"), "t_h")
		self.assertEqual(userNameToFileName("F_F_I"), "F__F__I_")
		self.assertEqual(userNameToFileName("f_f_i"), "f_f_i")
		self.assertEqual(userNameToFileName("Aacute_V.swash"), "A_acute_V_.swash")
		self.assertEqual(userNameToFileName(".notdef"), "_notdef")
		self.assertEqual(userNameToFileName("con"), "_con")
		self.assertEqual(userNameToFileName("CON"), "C_O_N_")
		self.assertEqual(userNameToFileName("con.alt"), "_con.alt")
		self.assertEqual(userNameToFileName("alt.con"), "alt._con")

	def test_prefix_suffix(self):
		PREFIX="TEST_PREFIX"
		SUFFIX="TEST_SUFFIX"
		NAME="NAME"
		NAME_FILE="N_A_M_E_"
		self.assertEqual(userNameToFileName(NAME, prefix=PREFIX, suffix=SUFFIX), PREFIX + NAME_FILE + SUFFIX)

	def test_collide(self):
		PREFIX="TEST_PREFIX"
		SUFFIX="TEST_SUFFIX"
		NAME="NAME"
		NAME_FILE="N_A_M_E_"
		COLLISION_AVOIDANCE1="000000000000001"
		COLLISION_AVOIDANCE2="000000000000002"
		exist = set()
		generated = userNameToFileName(NAME, exist, prefix=PREFIX, suffix=SUFFIX)
		exist.add(generated.lower())
		self.assertEqual(generated, PREFIX + NAME_FILE + SUFFIX)
		generated = userNameToFileName(NAME, exist, prefix=PREFIX, suffix=SUFFIX)
		exist.add(generated.lower())
		self.assertEqual(generated, PREFIX + NAME_FILE + COLLISION_AVOIDANCE1 + SUFFIX)
		generated = userNameToFileName(NAME, exist, prefix=PREFIX, suffix=SUFFIX)
		self.assertEqual(generated, PREFIX + NAME_FILE + COLLISION_AVOIDANCE2+ SUFFIX)

if __name__ == "__main__":
	import sys
	sys.exit(unittest.main())