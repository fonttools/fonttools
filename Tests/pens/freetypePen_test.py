import unittest
import os
import math

try:
    from fontTools.pens.freetypePen import FreeTypePen

    FREETYPE_PY_AVAILABLE = True
except ImportError:
    FREETYPE_PY_AVAILABLE = False

from fontTools.misc.transform import Scale, Offset

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data")


def box(pen, offset=(0, 0)):
    pen.moveTo((0 + offset[0], 0 + offset[1]))
    pen.lineTo((0 + offset[0], 500 + offset[1]))
    pen.lineTo((500 + offset[0], 500 + offset[1]))
    pen.lineTo((500 + offset[0], 0 + offset[1]))
    pen.closePath()


def draw_cubic(pen):
    pen.moveTo((50, 0))
    pen.lineTo((50, 500))
    pen.lineTo((200, 500))
    pen.curveTo((350, 500), (450, 400), (450, 250))
    pen.curveTo((450, 100), (350, 0), (200, 0))
    pen.closePath()


def draw_quadratic(pen):
    pen.moveTo((50, 0))
    pen.lineTo((50, 500))
    pen.lineTo((200, 500))
    pen.qCurveTo((274, 500), (388, 438), (450, 324), (450, 250))
    pen.qCurveTo((450, 176), (388, 62), (274, 0), (200, 0))
    pen.closePath()


def star(pen):
    pen.moveTo((0, 420))
    pen.lineTo((1000, 420))
    pen.lineTo((200, -200))
    pen.lineTo((500, 800))
    pen.lineTo((800, -200))
    pen.closePath()


# For the PGM format, see the following resources:
#   https://en.wikipedia.org/wiki/Netpbm
#   http://netpbm.sourceforge.net/doc/pgm.html
def load_pgm(filename):
    with open(filename, "rb") as fp:
        assert fp.readline() == "P5\n".encode()
        w, h = (int(c) for c in fp.readline().decode().rstrip().split(" "))
        assert fp.readline() == "255\n".encode()
        return fp.read(), (w, h)


def save_pgm(filename, buf, size):
    with open(filename, "wb") as fp:
        fp.write("P5\n".encode())
        fp.write("{0:d} {1:d}\n".format(*size).encode())
        fp.write("255\n".encode())
        fp.write(buf)


# Assume the buffers are equal when PSNR > 38dB. See also:
#   Peak signal-to-noise ratio
#   https://en.wikipedia.org/wiki/Peak_signal-to-noise_ratio
PSNR_THRESHOLD = 38.0


def psnr(b1, b2):
    import math

    mse = sum((c1 - c2) * (c1 - c2) for c1, c2 in zip(b1, b2)) / float(len(b1))
    return 10.0 * math.log10((255.0**2) / float(mse)) if mse > 0 else math.inf


@unittest.skipUnless(FREETYPE_PY_AVAILABLE, "freetype-py not installed")
class FreeTypePenTest(unittest.TestCase):
    def test_draw(self):
        pen = FreeTypePen(None)
        box(pen)
        width, height = 500, 500
        buf1, _ = pen.buffer(width=width, height=height)
        buf2 = b"\xff" * width * height
        self.assertEqual(buf1, buf2)

    def test_empty(self):
        pen = FreeTypePen(None)
        width, height = 500, 500
        buf, size = pen.buffer(width=width, height=height)
        self.assertEqual(b"\0" * size[0] * size[1], buf)

    def test_bbox_and_cbox(self):
        pen = FreeTypePen(None)
        draw_cubic(pen)
        self.assertEqual(pen.bbox, (50.0, 0.0, 450.0, 500.0))
        self.assertEqual(pen.cbox, (50.0, 0.0, 450.0, 500.0))

    def test_non_zero_fill(self):
        pen = FreeTypePen(None)
        star(pen)
        t = Scale(0.05, 0.05)
        width, height = t.transformPoint((1000, 1000))
        t = t.translate(0, 200)
        buf1, size1 = pen.buffer(width=width, height=height, transform=t, evenOdd=False)
        buf2, size2 = load_pgm(os.path.join(DATA_DIR, "test_non_zero_fill.pgm"))
        self.assertEqual(len(buf1), len(buf2))
        self.assertEqual(size1, size2)
        self.assertGreater(psnr(buf1, buf2), PSNR_THRESHOLD)

    def test_even_odd_fill(self):
        pen = FreeTypePen(None)
        star(pen)
        t = Scale(0.05, 0.05)
        width, height = t.transformPoint((1000, 1000))
        t = t.translate(0, 200)
        buf1, size1 = pen.buffer(width=width, height=height, transform=t, evenOdd=True)
        buf2, size2 = load_pgm(os.path.join(DATA_DIR, "test_even_odd_fill.pgm"))
        self.assertEqual(len(buf1), len(buf2))
        self.assertEqual(size1, size2)
        self.assertGreater(psnr(buf1, buf2), PSNR_THRESHOLD)

    def test_cubic_vs_quadratic(self):
        pen1, pen2 = FreeTypePen(None), FreeTypePen(None)
        draw_cubic(pen1)
        draw_quadratic(pen2)
        width, height = 500, 500
        buf1, _ = pen1.buffer(width=width, height=height)
        buf2, _ = pen2.buffer(width=width, height=height)
        self.assertEqual(len(buf1), len(buf2))
        self.assertGreater(psnr(buf1, buf2), PSNR_THRESHOLD)

    def test_contain(self):
        pen = FreeTypePen(None)
        star(pen)
        t = Scale(0.05, 0.05)
        width, height = 0, 0
        buf1, size1 = pen.buffer(width=width, height=height, transform=t, contain=True)
        buf2, size2 = load_pgm(os.path.join(DATA_DIR, "test_non_zero_fill.pgm"))
        self.assertEqual(len(buf1), len(buf2))
        self.assertEqual(size1, size2)
        self.assertGreater(psnr(buf1, buf2), PSNR_THRESHOLD)

    def test_rotate(self):
        pen = FreeTypePen(None)
        box(pen)
        t = Scale(0.05, 0.05).rotate(math.pi / 4.0).translate(1234, 5678)
        width, height = None, None
        buf1, size1 = pen.buffer(width=width, height=height, transform=t)
        buf2, size2 = load_pgm(os.path.join(DATA_DIR, "test_rotate.pgm"))
        self.assertEqual(len(buf1), len(buf2))
        self.assertEqual(size1, size2)
        self.assertGreater(psnr(buf1, buf2), PSNR_THRESHOLD)

    def test_skew(self):
        pen = FreeTypePen(None)
        box(pen)
        t = Scale(0.05, 0.05).skew(math.pi / 4.0).translate(1234, 5678)
        width, height = None, None
        buf1, size1 = pen.buffer(width=width, height=height, transform=t)
        buf2, size2 = load_pgm(os.path.join(DATA_DIR, "test_skew.pgm"))
        self.assertEqual(len(buf1), len(buf2))
        self.assertEqual(size1, size2)
        self.assertGreater(psnr(buf1, buf2), PSNR_THRESHOLD)

    def test_none_size(self):
        pen = FreeTypePen(None)
        star(pen)
        width, height = None, None
        buf1, size = pen.buffer(width=width, height=height, transform=Offset(0, 200))
        buf2, _ = pen.buffer(width=1000, height=1000, transform=Offset(0, 200))
        self.assertEqual(size, (1000, 1000))
        self.assertEqual(buf1, buf2)

        pen = FreeTypePen(None)
        box(pen, offset=(250, 250))
        width, height = None, None
        buf1, size = pen.buffer(width=width, height=height)
        buf2, _ = pen.buffer(width=500, height=500, transform=Offset(-250, -250))
        self.assertEqual(size, (500, 500))
        self.assertEqual(buf1, buf2)

        pen = FreeTypePen(None)
        box(pen, offset=(-1234, -5678))
        width, height = None, None
        buf1, size = pen.buffer(width=width, height=height)
        buf2, _ = pen.buffer(width=500, height=500, transform=Offset(1234, 5678))
        self.assertEqual(size, (500, 500))
        self.assertEqual(buf1, buf2)

    def test_zero_size(self):
        pen = FreeTypePen(None)
        star(pen)
        width, height = 0, 0
        buf1, size = pen.buffer(
            width=width, height=height, transform=Offset(0, 200), contain=True
        )
        buf2, _ = pen.buffer(
            width=1000, height=1000, transform=Offset(0, 200), contain=True
        )
        self.assertEqual(size, (1000, 1000))
        self.assertEqual(buf1, buf2)

        pen = FreeTypePen(None)
        box(pen, offset=(250, 250))
        width, height = 0, 0
        buf1, size = pen.buffer(width=width, height=height, contain=True)
        buf2, _ = pen.buffer(
            width=500, height=500, transform=Offset(0, 0), contain=True
        )
        self.assertEqual(size, (750, 750))
        self.assertEqual(buf1, buf2)

        pen = FreeTypePen(None)
        box(pen, offset=(-1234, -5678))
        width, height = 0, 0
        buf1, size = pen.buffer(width=width, height=height, contain=True)
        buf2, _ = pen.buffer(
            width=500, height=500, transform=Offset(1234, 5678), contain=True
        )
        self.assertEqual(size, (500, 500))
        self.assertEqual(buf1, buf2)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
