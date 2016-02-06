from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import tobytes
from fontTools.misc.textTools import deHexStr
import filecmp
import tempfile
from subprocess import check_call
import sys
import os
import unittest


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


if __name__ == "__main__":
	unittest.main()
