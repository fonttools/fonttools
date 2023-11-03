from fontTools.misc.py23 import tobytes
from fontTools.misc.textTools import deHexStr
import filecmp
from io import StringIO
import tempfile
from subprocess import check_call
import sys
import os
import unittest

from fontTools.misc.py23 import (
    round2,
    round3,
    isclose,
    redirect_stdout,
    redirect_stderr,
)


PIPE_SCRIPT = """\
import sys
binary_stdin = open(sys.stdin.fileno(), mode='rb', closefd=False)
binary_stdout = open(sys.stdout.fileno(), mode='wb', closefd=False)
binary_stdout.write(binary_stdin.read())
"""

# the string contains a mix of line endings, plus the Win "EOF" charater (0x1A)
# 'hello\rworld\r\n\x1a\r\n'
TEST_BIN_DATA = deHexStr("68 65 6c 6c 6f 0d 77 6f 72 6c 64 0d 0a 1a 0d 0a")


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
            with open(datafile, "rb") as infile, tempfile.NamedTemporaryFile(
                delete=False
            ) as outfile:
                env = dict(os.environ)
                env["PYTHONPATH"] = os.pathsep.join(sys.path)
                check_call(
                    [sys.executable, script], stdin=infile, stdout=outfile, env=env
                )
            result = not filecmp.cmp(infile.name, outfile.name, shallow=False)
        finally:
            os.remove(script)
            os.remove(datafile)
            os.remove(outfile.name)
        return result

    def test_binary_pipe_py23_open_wrapper(self):
        if self.diff_piped(TEST_BIN_DATA, "from fontTools.misc.py23 import open"):
            self.fail("Input and output data differ!")

    def test_binary_pipe_built_in_io_open(self):
        if sys.version_info.major < 3 and sys.platform == "win32":
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
        # floats should be illegal
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
    """Same as above but results adapted for Python 3 round()"""

    def test_second_argument_type(self):
        # floats should be illegal
        self.assertRaises(TypeError, round3, 3.14159, 2.0)

        # None should be allowed
        self.assertEqual(round3(1.0, None), 1)
        # the following would raise an error with the built-in Python3.5 round:
        # TypeError: 'NoneType' object cannot be interpreted as an integer
        self.assertEqual(round3(1, None), 1)

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

        # no ndigits and input is already an integer: output == input
        rv = round3(1)
        self.assertEqual(rv, 1)
        self.assertTrue(isinstance(rv, int))
        rv = round3(1.0)
        self.assertEqual(rv, 1)
        self.assertTrue(isinstance(rv, int))

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


NAN = float("nan")
INF = float("inf")
NINF = float("-inf")


class IsCloseTests(unittest.TestCase):
    """
    Tests taken from Python 3.5 test_math.py:
    https://hg.python.org/cpython/file/v3.5.2/Lib/test/test_math.py
    """

    isclose = staticmethod(isclose)

    def assertIsClose(self, a, b, *args, **kwargs):
        self.assertTrue(
            self.isclose(a, b, *args, **kwargs),
            msg="%s and %s should be close!" % (a, b),
        )

    def assertIsNotClose(self, a, b, *args, **kwargs):
        self.assertFalse(
            self.isclose(a, b, *args, **kwargs),
            msg="%s and %s should not be close!" % (a, b),
        )

    def assertAllClose(self, examples, *args, **kwargs):
        for a, b in examples:
            self.assertIsClose(a, b, *args, **kwargs)

    def assertAllNotClose(self, examples, *args, **kwargs):
        for a, b in examples:
            self.assertIsNotClose(a, b, *args, **kwargs)

    def test_negative_tolerances(self):
        # ValueError should be raised if either tolerance is less than zero
        with self.assertRaises(ValueError):
            self.assertIsClose(1, 1, rel_tol=-1e-100)
        with self.assertRaises(ValueError):
            self.assertIsClose(1, 1, rel_tol=1e-100, abs_tol=-1e10)

    def test_identical(self):
        # identical values must test as close
        identical_examples = [
            (2.0, 2.0),
            (0.1e200, 0.1e200),
            (1.123e-300, 1.123e-300),
            (12345, 12345.0),
            (0.0, -0.0),
            (345678, 345678),
        ]
        self.assertAllClose(identical_examples, rel_tol=0.0, abs_tol=0.0)

    def test_eight_decimal_places(self):
        # examples that are close to 1e-8, but not 1e-9
        eight_decimal_places_examples = [
            (1e8, 1e8 + 1),
            (-1e-8, -1.000000009e-8),
            (1.12345678, 1.12345679),
        ]
        self.assertAllClose(eight_decimal_places_examples, rel_tol=1e-8)
        self.assertAllNotClose(eight_decimal_places_examples, rel_tol=1e-9)

    def test_near_zero(self):
        # values close to zero
        near_zero_examples = [(1e-9, 0.0), (-1e-9, 0.0), (-1e-150, 0.0)]
        # these should not be close to any rel_tol
        self.assertAllNotClose(near_zero_examples, rel_tol=0.9)
        # these should be close to abs_tol=1e-8
        self.assertAllClose(near_zero_examples, abs_tol=1e-8)

    def test_identical_infinite(self):
        # these are close regardless of tolerance -- i.e. they are equal
        self.assertIsClose(INF, INF)
        self.assertIsClose(INF, INF, abs_tol=0.0)
        self.assertIsClose(NINF, NINF)
        self.assertIsClose(NINF, NINF, abs_tol=0.0)

    def test_inf_ninf_nan(self):
        # these should never be close (following IEEE 754 rules for equality)
        not_close_examples = [
            (NAN, NAN),
            (NAN, 1e-100),
            (1e-100, NAN),
            (INF, NAN),
            (NAN, INF),
            (INF, NINF),
            (INF, 1.0),
            (1.0, INF),
            (INF, 1e308),
            (1e308, INF),
        ]
        # use largest reasonable tolerance
        self.assertAllNotClose(not_close_examples, abs_tol=0.999999999999999)

    def test_zero_tolerance(self):
        # test with zero tolerance
        zero_tolerance_close_examples = [(1.0, 1.0), (-3.4, -3.4), (-1e-300, -1e-300)]
        self.assertAllClose(zero_tolerance_close_examples, rel_tol=0.0)

        zero_tolerance_not_close_examples = [
            (1.0, 1.000000000000001),
            (0.99999999999999, 1.0),
            (1.0e200, 0.999999999999999e200),
        ]
        self.assertAllNotClose(zero_tolerance_not_close_examples, rel_tol=0.0)

    def test_assymetry(self):
        # test the assymetry example from PEP 485
        self.assertAllClose([(9, 10), (10, 9)], rel_tol=0.1)

    def test_integers(self):
        # test with integer values
        integer_examples = [(100000001, 100000000), (123456789, 123456788)]

        self.assertAllClose(integer_examples, rel_tol=1e-8)
        self.assertAllNotClose(integer_examples, rel_tol=1e-9)

    def test_decimals(self):
        # test with Decimal values
        from decimal import Decimal

        decimal_examples = [
            (Decimal("1.00000001"), Decimal("1.0")),
            (Decimal("1.00000001e-20"), Decimal("1.0e-20")),
            (Decimal("1.00000001e-100"), Decimal("1.0e-100")),
        ]
        self.assertAllClose(decimal_examples, rel_tol=1e-8)
        self.assertAllNotClose(decimal_examples, rel_tol=1e-9)

    def test_fractions(self):
        # test with Fraction values
        from fractions import Fraction

        # could use some more examples here!
        fraction_examples = [(Fraction(1, 100000000) + 1, Fraction(1))]
        self.assertAllClose(fraction_examples, rel_tol=1e-8)
        self.assertAllNotClose(fraction_examples, rel_tol=1e-9)


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
