from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.textTools import deHexStr
import filecmp
import tempfile
from subprocess import check_call
import sys
import os
import unittest

from fontTools.misc.py23 import round2, round3


PIPE_SCRIPT = """\
import sys
binary_stdin = open(sys.stdin.fileno(), mode='rb', closefd=False)
binary_stdout = open(sys.stdout.fileno(), mode='wb', closefd=False)
binary_stdout.write(binary_stdin.read())
"""

# the string contains a mix of line endings, plus the Win "EOF" charater (0x1A)
# 'hello\rworld\r\n\x1a\r\n'
TEST_BIN_DATA = deHexStr(
	"68 65 6c 6c 6f 0d 77 6f 72 6c 64 0d 0a 1a 0d 0a"
)

class OpenFuncWrapperTest(unittest.TestCase):

	@staticmethod
	def make_temp(data):
		with tempfile.NamedTemporaryFile(delete=False) as f:
			f.write(tobytes(data))
		return f.name

	def diff_piped(self, data, import_statement):
		script = self.make_temp("\n".join([import_statement, PIPE_SCRIPT]))
		datafile = self.make_temp(data)
		try:
			with open(datafile, 'rb') as infile, \
					tempfile.NamedTemporaryFile(delete=False) as outfile:
				env = dict(os.environ)
				env["PYTHONPATH"] = os.pathsep.join(sys.path)
				check_call(
					[sys.executable, script], stdin=infile, stdout=outfile,
					env=env)
			result = not filecmp.cmp(infile.name, outfile.name, shallow=False)
		finally:
			os.remove(script)
			os.remove(datafile)
			os.remove(outfile.name)
		return result

	def test_binary_pipe_py23_open_wrapper(self):
		if self.diff_piped(
				TEST_BIN_DATA, "from fontTools.misc.py23 import open"):
			self.fail("Input and output data differ!")

	def test_binary_pipe_built_in_io_open(self):
		if sys.version_info.major < 3 and sys.platform == 'win32':
			# On Windows Python 2.x, the piped input and output data are
			# expected to be different when using io.open, because of issue
			# https://bugs.python.org/issue10841.
			expected = True
		else:
			expected = False
		result = self.diff_piped(TEST_BIN_DATA, "from io import open")
		self.assertEqual(result, expected)


class Round2Test(unittest.TestCase):
	"""
	Test cases taken from cpython 2.7 test suite:

	https://github.com/python/cpython/blob/2.7/Lib/test/test_float.py#L748

	Excludes the test cases that are not supported when using the `decimal`
	module's `quantize` method.
	"""

	def test_second_argument_type(self):
		# any type with an __index__ method should be permitted as
		# a second argument
		self.assertAlmostEqual(round2(12.34, True), 12.3)

		class MyIndex(object):
			def __index__(self): return 4
		self.assertAlmostEqual(round2(-0.123456, MyIndex()), -0.1235)
		# but floats should be illegal
		self.assertRaises(TypeError, round2, 3.14159, 2.0)

	def test_halfway_cases(self):
		# Halfway cases need special attention, since the current
		# implementation has to deal with them specially.  Note that
		# 2.x rounds halfway values up (i.e., away from zero) while
		# 3.x does round-half-to-even.
		self.assertAlmostEqual(round2(0.125, 2), 0.13)
		self.assertAlmostEqual(round2(0.375, 2), 0.38)
		self.assertAlmostEqual(round2(0.625, 2), 0.63)
		self.assertAlmostEqual(round2(0.875, 2), 0.88)
		self.assertAlmostEqual(round2(-0.125, 2), -0.13)
		self.assertAlmostEqual(round2(-0.375, 2), -0.38)
		self.assertAlmostEqual(round2(-0.625, 2), -0.63)
		self.assertAlmostEqual(round2(-0.875, 2), -0.88)

		self.assertAlmostEqual(round2(0.25, 1), 0.3)
		self.assertAlmostEqual(round2(0.75, 1), 0.8)
		self.assertAlmostEqual(round2(-0.25, 1), -0.3)
		self.assertAlmostEqual(round2(-0.75, 1), -0.8)

		self.assertEqual(round2(-6.5, 0), -7.0)
		self.assertEqual(round2(-5.5, 0), -6.0)
		self.assertEqual(round2(-1.5, 0), -2.0)
		self.assertEqual(round2(-0.5, 0), -1.0)
		self.assertEqual(round2(0.5, 0), 1.0)
		self.assertEqual(round2(1.5, 0), 2.0)
		self.assertEqual(round2(2.5, 0), 3.0)
		self.assertEqual(round2(3.5, 0), 4.0)
		self.assertEqual(round2(4.5, 0), 5.0)
		self.assertEqual(round2(5.5, 0), 6.0)
		self.assertEqual(round2(6.5, 0), 7.0)

		# same but without an explicit second argument; in 3.x these
		# will give integers
		self.assertEqual(round2(-6.5), -7.0)
		self.assertEqual(round2(-5.5), -6.0)
		self.assertEqual(round2(-1.5), -2.0)
		self.assertEqual(round2(-0.5), -1.0)
		self.assertEqual(round2(0.5), 1.0)
		self.assertEqual(round2(1.5), 2.0)
		self.assertEqual(round2(2.5), 3.0)
		self.assertEqual(round2(3.5), 4.0)
		self.assertEqual(round2(4.5), 5.0)
		self.assertEqual(round2(5.5), 6.0)
		self.assertEqual(round2(6.5), 7.0)

		self.assertEqual(round2(-25.0, -1), -30.0)
		self.assertEqual(round2(-15.0, -1), -20.0)
		self.assertEqual(round2(-5.0, -1), -10.0)
		self.assertEqual(round2(5.0, -1), 10.0)
		self.assertEqual(round2(15.0, -1), 20.0)
		self.assertEqual(round2(25.0, -1), 30.0)
		self.assertEqual(round2(35.0, -1), 40.0)
		self.assertEqual(round2(45.0, -1), 50.0)
		self.assertEqual(round2(55.0, -1), 60.0)
		self.assertEqual(round2(65.0, -1), 70.0)
		self.assertEqual(round2(75.0, -1), 80.0)
		self.assertEqual(round2(85.0, -1), 90.0)
		self.assertEqual(round2(95.0, -1), 100.0)
		self.assertEqual(round2(12325.0, -1), 12330.0)
		self.assertEqual(round2(0, -1), 0.0)

		self.assertEqual(round2(350.0, -2), 400.0)
		self.assertEqual(round2(450.0, -2), 500.0)

		self.assertAlmostEqual(round2(0.5e21, -21), 1e21)
		self.assertAlmostEqual(round2(1.5e21, -21), 2e21)
		self.assertAlmostEqual(round2(2.5e21, -21), 3e21)
		self.assertAlmostEqual(round2(5.5e21, -21), 6e21)
		self.assertAlmostEqual(round2(8.5e21, -21), 9e21)

		self.assertAlmostEqual(round2(-1.5e22, -22), -2e22)
		self.assertAlmostEqual(round2(-0.5e22, -22), -1e22)
		self.assertAlmostEqual(round2(0.5e22, -22), 1e22)
		self.assertAlmostEqual(round2(1.5e22, -22), 2e22)


class Round3Test(unittest.TestCase):
	""" Same as above but results adapted for Python 3 round() """

	def test_second_argument_type(self):
		# any type with an __index__ method should be permitted as
		# a second argument
		self.assertAlmostEqual(round3(12.34, True), 12.3)

		class MyIndex(object):
			def __index__(self): return 4
		self.assertAlmostEqual(round3(-0.123456, MyIndex()), -0.1235)
		# but floats should be illegal
		self.assertRaises(TypeError, round3, 3.14159, 2.0)

	def test_halfway_cases(self):
		self.assertAlmostEqual(round3(0.125, 2), 0.12)
		self.assertAlmostEqual(round3(0.375, 2), 0.38)
		self.assertAlmostEqual(round3(0.625, 2), 0.62)
		self.assertAlmostEqual(round3(0.875, 2), 0.88)
		self.assertAlmostEqual(round3(-0.125, 2), -0.12)
		self.assertAlmostEqual(round3(-0.375, 2), -0.38)
		self.assertAlmostEqual(round3(-0.625, 2), -0.62)
		self.assertAlmostEqual(round3(-0.875, 2), -0.88)

		self.assertAlmostEqual(round3(0.25, 1), 0.2)
		self.assertAlmostEqual(round3(0.75, 1), 0.8)
		self.assertAlmostEqual(round3(-0.25, 1), -0.2)
		self.assertAlmostEqual(round3(-0.75, 1), -0.8)

		self.assertEqual(round3(-6.5, 0), -6.0)
		self.assertEqual(round3(-5.5, 0), -6.0)
		self.assertEqual(round3(-1.5, 0), -2.0)
		self.assertEqual(round3(-0.5, 0), 0.0)
		self.assertEqual(round3(0.5, 0), 0.0)
		self.assertEqual(round3(1.5, 0), 2.0)
		self.assertEqual(round3(2.5, 0), 2.0)
		self.assertEqual(round3(3.5, 0), 4.0)
		self.assertEqual(round3(4.5, 0), 4.0)
		self.assertEqual(round3(5.5, 0), 6.0)
		self.assertEqual(round3(6.5, 0), 6.0)

		# same but without an explicit second argument; in 2.x these
		# will give floats
		self.assertEqual(round3(-6.5), -6)
		self.assertEqual(round3(-5.5), -6)
		self.assertEqual(round3(-1.5), -2.0)
		self.assertEqual(round3(-0.5), 0)
		self.assertEqual(round3(0.5), 0)
		self.assertEqual(round3(1.5), 2)
		self.assertEqual(round3(2.5), 2)
		self.assertEqual(round3(3.5), 4)
		self.assertEqual(round3(4.5), 4)
		self.assertEqual(round3(5.5), 6)
		self.assertEqual(round3(6.5), 6)

		self.assertEqual(round3(-25.0, -1), -20.0)
		self.assertEqual(round3(-15.0, -1), -20.0)
		self.assertEqual(round3(-5.0, -1), 0.0)
		self.assertEqual(round3(5.0, -1), 0.0)
		self.assertEqual(round3(15.0, -1), 20.0)
		self.assertEqual(round3(25.0, -1), 20.0)
		self.assertEqual(round3(35.0, -1), 40.0)
		self.assertEqual(round3(45.0, -1), 40.0)
		self.assertEqual(round3(55.0, -1), 60.0)
		self.assertEqual(round3(65.0, -1), 60.0)
		self.assertEqual(round3(75.0, -1), 80.0)
		self.assertEqual(round3(85.0, -1), 80.0)
		self.assertEqual(round3(95.0, -1), 100.0)
		self.assertEqual(round3(12325.0, -1), 12320.0)
		self.assertEqual(round3(0, -1), 0.0)

		self.assertEqual(round3(350.0, -2), 400.0)
		self.assertEqual(round3(450.0, -2), 400.0)

		self.assertAlmostEqual(round3(0.5e21, -21), 0.0)
		self.assertAlmostEqual(round3(1.5e21, -21), 2e21)
		self.assertAlmostEqual(round3(2.5e21, -21), 2e21)
		self.assertAlmostEqual(round3(5.5e21, -21), 6e21)
		self.assertAlmostEqual(round3(8.5e21, -21), 8e21)

		self.assertAlmostEqual(round3(-1.5e22, -22), -2e22)
		self.assertAlmostEqual(round3(-0.5e22, -22), 0.0)
		self.assertAlmostEqual(round3(0.5e22, -22), 0.0)
		self.assertAlmostEqual(round3(1.5e22, -22), 2e22)


if __name__ == "__main__":
	unittest.main()
