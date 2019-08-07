from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.textTools import deHexStr
import filecmp
import tempfile
from subprocess import check_call
import sys
import os
import unittest
from io import StringIO, BytesIO

from fontTools.misc.py23 import (
	redirect_stdout, redirect_stderr)


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



class Round3Test(unittest.TestCase):
	""" Same as above but results adapted for Python 3 round() """

	def test_second_argument_type(self):
		# floats should be illegal
		self.assertRaises(TypeError, round, 3.14159, 2.0)

		# None should be allowed
		self.assertEqual(round(1.0, None), 1)
		# the following would raise an error with the built-in Python3.5 round:
		# TypeError: 'NoneType' object cannot be interpreted as an integer
		self.assertEqual(round(1, None), 1)

	def test_halfway_cases(self):
		self.assertAlmostEqual(round(0.125, 2), 0.12)
		self.assertAlmostEqual(round(0.375, 2), 0.38)
		self.assertAlmostEqual(round(0.625, 2), 0.62)
		self.assertAlmostEqual(round(0.875, 2), 0.88)
		self.assertAlmostEqual(round(-0.125, 2), -0.12)
		self.assertAlmostEqual(round(-0.375, 2), -0.38)
		self.assertAlmostEqual(round(-0.625, 2), -0.62)
		self.assertAlmostEqual(round(-0.875, 2), -0.88)

		self.assertAlmostEqual(round(0.25, 1), 0.2)
		self.assertAlmostEqual(round(0.75, 1), 0.8)
		self.assertAlmostEqual(round(-0.25, 1), -0.2)
		self.assertAlmostEqual(round(-0.75, 1), -0.8)

		self.assertEqual(round(-6.5, 0), -6.0)
		self.assertEqual(round(-5.5, 0), -6.0)
		self.assertEqual(round(-1.5, 0), -2.0)
		self.assertEqual(round(-0.5, 0), 0.0)
		self.assertEqual(round(0.5, 0), 0.0)
		self.assertEqual(round(1.5, 0), 2.0)
		self.assertEqual(round(2.5, 0), 2.0)
		self.assertEqual(round(3.5, 0), 4.0)
		self.assertEqual(round(4.5, 0), 4.0)
		self.assertEqual(round(5.5, 0), 6.0)
		self.assertEqual(round(6.5, 0), 6.0)

		# same but without an explicit second argument; in 2.x these
		# will give floats
		self.assertEqual(round(-6.5), -6)
		self.assertEqual(round(-5.5), -6)
		self.assertEqual(round(-1.5), -2.0)
		self.assertEqual(round(-0.5), 0)
		self.assertEqual(round(0.5), 0)
		self.assertEqual(round(1.5), 2)
		self.assertEqual(round(2.5), 2)
		self.assertEqual(round(3.5), 4)
		self.assertEqual(round(4.5), 4)
		self.assertEqual(round(5.5), 6)
		self.assertEqual(round(6.5), 6)

		# no ndigits and input is already an integer: output == input
		rv = round(1)
		self.assertEqual(rv, 1)
		self.assertTrue(isinstance(rv, int))
		rv = round(1.0)
		self.assertEqual(rv, 1)
		self.assertTrue(isinstance(rv, int))

		self.assertEqual(round(-25.0, -1), -20.0)
		self.assertEqual(round(-15.0, -1), -20.0)
		self.assertEqual(round(-5.0, -1), 0.0)
		self.assertEqual(round(5.0, -1), 0.0)
		self.assertEqual(round(15.0, -1), 20.0)
		self.assertEqual(round(25.0, -1), 20.0)
		self.assertEqual(round(35.0, -1), 40.0)
		self.assertEqual(round(45.0, -1), 40.0)
		self.assertEqual(round(55.0, -1), 60.0)
		self.assertEqual(round(65.0, -1), 60.0)
		self.assertEqual(round(75.0, -1), 80.0)
		self.assertEqual(round(85.0, -1), 80.0)
		self.assertEqual(round(95.0, -1), 100.0)
		self.assertEqual(round(12325.0, -1), 12320.0)
		self.assertEqual(round(0, -1), 0.0)

		self.assertEqual(round(350.0, -2), 400.0)
		self.assertEqual(round(450.0, -2), 400.0)

		self.assertAlmostEqual(round(0.5e21, -21), 0.0)
		self.assertAlmostEqual(round(1.5e21, -21), 2e21)
		self.assertAlmostEqual(round(2.5e21, -21), 2e21)
		self.assertAlmostEqual(round(5.5e21, -21), 6e21)
		self.assertAlmostEqual(round(8.5e21, -21), 8e21)

		self.assertAlmostEqual(round(-1.5e22, -22), -2e22)
		self.assertAlmostEqual(round(-0.5e22, -22), 0.0)
		self.assertAlmostEqual(round(0.5e22, -22), 0.0)
		self.assertAlmostEqual(round(1.5e22, -22), 2e22)


class TestRedirectStream:

    redirect_stream = None
    orig_stream = None

    def test_no_redirect_in_init(self):
        orig_stdout = getattr(sys, self.orig_stream)
        self.redirect_stream(None)
        self.assertIs(getattr(sys, self.orig_stream), orig_stdout)

    def test_redirect_to_string_io(self):
        f = StringIO()
        msg = "Consider an API like help(), which prints directly to stdout"
        orig_stdout = getattr(sys, self.orig_stream)
        with self.redirect_stream(f):
            print(msg, file=getattr(sys, self.orig_stream))
        self.assertIs(getattr(sys, self.orig_stream), orig_stdout)
        s = f.getvalue().strip()
        self.assertEqual(s, msg)

    def test_enter_result_is_target(self):
        f = StringIO()
        with self.redirect_stream(f) as enter_result:
            self.assertIs(enter_result, f)

    def test_cm_is_reusable(self):
        f = StringIO()
        write_to_f = self.redirect_stream(f)
        orig_stdout = getattr(sys, self.orig_stream)
        with write_to_f:
            print("Hello", end=" ", file=getattr(sys, self.orig_stream))
        with write_to_f:
            print("World!", file=getattr(sys, self.orig_stream))
        self.assertIs(getattr(sys, self.orig_stream), orig_stdout)
        s = f.getvalue()
        self.assertEqual(s, "Hello World!\n")

    def test_cm_is_reentrant(self):
        f = StringIO()
        write_to_f = self.redirect_stream(f)
        orig_stdout = getattr(sys, self.orig_stream)
        with write_to_f:
            print("Hello", end=" ", file=getattr(sys, self.orig_stream))
            with write_to_f:
                print("World!", file=getattr(sys, self.orig_stream))
        self.assertIs(getattr(sys, self.orig_stream), orig_stdout)
        s = f.getvalue()
        self.assertEqual(s, "Hello World!\n")


class TestRedirectStdout(TestRedirectStream, unittest.TestCase):

    redirect_stream = redirect_stdout
    orig_stream = "stdout"


class TestRedirectStderr(TestRedirectStream, unittest.TestCase):

    redirect_stream = redirect_stderr
    orig_stream = "stderr"


if __name__ == "__main__":
	sys.exit(unittest.main())
