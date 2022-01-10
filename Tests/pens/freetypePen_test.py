import unittest

try:
    from fontTools.pens.freetypePen import FreeTypePen
    FREETYPE_PY_AVAILABLE = True
except ImportError:
    FREETYPE_PY_AVAILABLE = False

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

@unittest.skipUnless(FREETYPE_PY_AVAILABLE, "freetype-py not installed")
class FreeTypePenTest(unittest.TestCase):
    def test_draw(self):
        import base64, zlib
        ZLIB_B64_BIN = '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'
        pen = FreeTypePen(None)
        draw_cubic(pen)
        offset, width, height = (0, 0), 500, 500
        buf1, _ = pen.buffer(offset=offset, width=width, height=height)
        buf2 = zlib.decompress(base64.b64decode(ZLIB_B64_BIN))
        self.assertEqual(buf1, buf2)

    def test_scale(self):
        import base64, zlib
        ZLIB_B64_BIN = 'eJy91r8NgkAUx/FLMHECCLMQC5gGK3UB4gJEXABhAbTAJXAJ7GkoBIornrQif/w2vvo+yXH37vFTqi/5rKYs8jhwDDVdMlp15ttM9NVFE2ZSiLShCYVI5VIhekeFSLKmQhIsZLixZaFdKqQyqZAQi9amQiIsOpsK8bHIsKgNKsTBIsAixiLHosCixKLB4vWHXfEv56fLb5B3Ce5E3u1XRQV+tXwy4OnDJxyeopUFhfYUFHsFRaqgSOGfUx+G65cSgPcNZlPGyRoBM0nmjJJMfdv+mpaa5+N+OW5W44vfouHQiw=='
        pen = FreeTypePen(None)
        draw_cubic(pen)
        offset, width, height = (0, 0), 500, 500
        buf1, size = pen.buffer(offset=offset, width=width, height=height, scale=(0.1, 0.1))
        buf2 = zlib.decompress(base64.b64decode(ZLIB_B64_BIN))
        self.assertEqual(buf1, buf2)
        self.assertEqual(size, (50, 50))

    def test_empty(self):
        pen = FreeTypePen(None)
        offset, width, height = (0, 0), 500, 500
        buf, size = pen.buffer(offset=offset, width=width, height=height)
        self.assertEqual(b'\0' * size[0] * size[1], buf)

    def test_bbox_and_cbox(self):
        pen = FreeTypePen(None)
        draw_cubic(pen)
        self.assertEqual(pen.bbox, (50.0, 0.0, 450.0, 500.0))
        self.assertEqual(pen.cbox, (50.0, 0.0, 450.0, 500.0))

    def test_non_zero_fill(self):
        import base64, zlib
        ZLIB_B64_BIN = 'eJzt2L0NglAUhmESTZxA4yzGAqfRSl3AuABRF/BnAbTAJXAJ7GkoBAqKo4WNhbk3OZ4vknzvAk/g/nC5QcAYY4wxxhhrRfJZmaXJfjXqWBrving6tDZe1dufKV8NkSrqmxsieWhvSDO3N0SOPXtDjgBD9K/LbTShvSG5dgp7GBIBjEq54n0M2QKMWvcgXoZMAUYMMArVR8vPkBHAWAGMPcBIAEYKMDKAUQKMB8BAvCvEmCPmLmINIvYSwJ6I2NvPGuJ/vrWIMwPg7IM4wwHOovnA3GgmSsLDWGgJt3FSE07jZP7P2Sz1gusOQD3cLqPaaCety6h3xncyxWVmd7dU3m/Xw3rc/R3AGGOMsbb3BMrP0Is='
        pen = FreeTypePen(None)
        draw_cubic(pen)
        offset, width, height = (0, 200), 1000, 1000
        buf1, size = pen.buffer(offset=offset, width=width, height=height, scale=(0.1, 0.1), even_odd=False)
        buf2 = zlib.decompress(base64.b64decode(ZLIB_B64_BIN))
        self.assertEqual(buf1, buf2)

    def test_even_odd_fill(self):
        import base64, zlib
        ZLIB_B64_BIN = 'eJzt2L0NglAUhmESTZxA4yzGAqfRSl3AuABRF/BnAbTAJXAJ7GkoBAqKo4WNhbk3OZ4vknzvAk/g/nC5QcAYY4wxxhhrRfJZmaXJfjXqWBrving6tDZe1dufKV8NkSrqmxsieWhvSDO3N0SOPXtDjgBD9K/LbTShvSG5dgp7GBIBjEq54n0M2QKMWvcgXoZMAUYMMArVR8vPkBHAWAGMPcBIAEYKMDKAUQKMB8BAvCvEmCPmLmINIvYSwJ6I2NvPGuJ/vrWIMwPg7IM4wwHOovnA3GgmSsLDWGgJt3FSE07jZP7P2Sz1gusOQD3cLqPaaCety6h3xncyxWVmd7dU3m/Xw3rc/R3AGGOMsbb3BMrP0Is='
        pen = FreeTypePen(None)
        draw_cubic(pen)
        offset, width, height = (0, 200), 1000, 1000
        buf1, size = pen.buffer(offset=offset, width=width, height=height, scale=(0.1, 0.1), even_odd=True)
        buf2 = zlib.decompress(base64.b64decode(ZLIB_B64_BIN))
        self.assertEqual(buf1, buf2)

    def test_cubic_vs_quadratic(self):
        # Assume the buffers are equal when PSNR > 38dB.
        def psnr(b1, b2):
            import math
            mse = sum((c1-c2) * (c1-c2) for c1, c2 in zip(b1, b2)) / float(len(b1))
            return 10.0 * math.log10((255.0 ** 2) / float(mse))
        pen1, pen2 = FreeTypePen(None), FreeTypePen(None)
        draw_cubic(pen1)
        draw_quadratic(pen2)
        offset, width, height = (0, 0), 500, 500
        buf1, _ = pen1.buffer(offset=offset, width=width, height=height)
        buf2, _ = pen2.buffer(offset=offset, width=width, height=height)
        self.assertEqual(len(buf1), len(buf2))
        self.assertGreater(psnr(buf1, buf2), 38.0)

    def test_contain(self):
        import base64, zlib
        ZLIB_B64_BIN = 'eJyVlKtvAkEQh5dHCEG0vQTbJgjOIVqB7VW0BoUsCQqHLElP4VCkV8sfQBpcqzCYYjEIDClNEFiaSxCEEB7bO/aWO2Bn2fmp22G+3ONjhhBxdB34AUzlBUt0v5GAtlpd4YgCpc84okXpBwqI2pTaUQxhUCf3GMJyiTcMMXKJHwSg010Q2iuMQGjvMkJdu7ZihLr2AvWirL3FCVXtrnAWVe0G3UdRu+UTIu2lBUVlUSJ3YwwwvnXuorXVgba2e7BQdaPWv6mG+Ms8/akA08fA+9/0zgO964NPFmucAxqx489cnMv650WBmcwvDIwyQteXXxDweQH9P8y1qH9tQv1OHkSEIQEIeT8FLCnAJzwY+bTzCQ9GPu2FU+DMtLdEhGza/QkPRjbthgiQTntgwodD/1qy5Ef7pnokUt8f4CWv85ZZ3j3mZ/wMLnlvpdNBmp3TA68ALnlPeDPBC4kmq0DamfBlOVgrL90apH0nfJI9LGYnEu2u8E7yuJrsgNod4dta+LQerm0B7Qa1c+Kb52yxdqufEgOEpPpC7WYcAgiJv/rX/4vPJ4U='
        pen = FreeTypePen(None)
        star(pen)
        offset, width, height = (0, 0), 0, 0
        buf1, size = pen.buffer(offset=offset, width=width, height=height, scale=(0.05, 0.05), contain=True)
        buf2 = zlib.decompress(base64.b64decode(ZLIB_B64_BIN))

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
