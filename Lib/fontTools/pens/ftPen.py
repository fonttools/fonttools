"""A pen that rasterises outlines with FreeType."""

__all__ = ['FTPen']

import os
import ctypes
import platform
import subprocess
import collections
import math

import freetype
from freetype.raw import FT_Outline_Get_Bitmap, FT_Outline_Get_BBox, FT_Outline_Get_CBox
from freetype.ft_types import FT_Pos
from freetype.ft_structs import FT_Vector, FT_BBox, FT_Bitmap, FT_Outline
from freetype.ft_enums import FT_OUTLINE_NONE, FT_OUTLINE_EVEN_ODD_FILL, FT_PIXEL_MODE_GRAY
from freetype.ft_errors import FT_Exception

from fontTools.pens.basePen import BasePen
from fontTools.misc.roundTools import otRound

class FTPen(BasePen):

    np = None
    plt = None
    Image = None
    Contour = collections.namedtuple('Contour', ('points', 'tags'))
    LINE      = 0b00000001
    CURVE     = 0b00000011
    OFFCURVE  = 0b00000010
    QCURVE    = 0b00000001
    QOFFCURVE = 0b00000000

    def __init__(self, glyphSet):
        self.contours = []

    def outline(self, offset=None, scale=None, even_odd=False):
        # Convert the current contours to FT_Outline.
        offset = offset or (0, 0)
        scale  = scale  or (1.0, 1.0)
        n_contours = len(self.contours)
        n_points   = sum((len(contour.points) for contour in self.contours))
        points = []
        for contour in self.contours:
            for point in contour.points:
                points.append(FT_Vector(FT_Pos(otRound((point[0] + offset[0]) * scale[0] * 64)), FT_Pos(otRound((point[1] + offset[1]) * scale[1] * 64))))
        tags = []
        for contour in self.contours:
            for tag in contour.tags:
                tags.append(tag)
        contours = []
        contours_sum = 0
        for contour in self.contours:
            contours_sum += len(contour.points)
            contours.append(contours_sum - 1)
        flags = FT_OUTLINE_EVEN_ODD_FILL if even_odd else FT_OUTLINE_NONE
        return FT_Outline(
            (ctypes.c_short)(n_contours),
            (ctypes.c_short)(n_points),
            (FT_Vector      * n_points)(*points),
            (ctypes.c_ubyte * n_points)(*tags),
            (ctypes.c_short * n_contours)(*contours),
            (ctypes.c_int)(flags)
        )

    def buffer(self, width=1000, ascender=880, descender=-120, even_odd=False, scale=None):
        # Return a tuple with the bitmap buffer and its dimension.
        scale  = scale or (1.0, 1.0)
        width  = math.ceil(width * scale[0])
        height = math.ceil((ascender - descender) * scale[1])
        buf = ctypes.create_string_buffer(width * height)
        bitmap = FT_Bitmap(
            (ctypes.c_int)(height),
            (ctypes.c_int)(width),
            (ctypes.c_int)(width),
            (ctypes.POINTER(ctypes.c_ubyte))(buf),
            (ctypes.c_short)(256),
            (ctypes.c_ubyte)(FT_PIXEL_MODE_GRAY),
            (ctypes.c_char)(0),
            (ctypes.c_void_p)(None)
        )
        outline = self.outline(offset=(0, -descender), even_odd=even_odd, scale=scale)
        err = FT_Outline_Get_Bitmap(freetype.get_handle(), ctypes.byref(outline), ctypes.byref(bitmap))
        if err != 0:
            raise FT_Exception(err)
        return buf.raw, (width, height)

    def array(self, width=1000, ascender=880, descender=-120, even_odd=False, scale=None):
        # Return a numpy array. Each element takes values in the range of [0.0, 1.0].
        if not self.np:
            import numpy as np
            self.np = np
        buf, size = self.buffer(width, ascender=ascender, descender=descender, even_odd=even_odd, scale=scale)
        return self.np.frombuffer(buf, 'B').reshape((size[1], size[0])) / 255.0

    def show(self, width=1000, ascender=880, descender=-120, even_odd=False, scale=None):
        # Plot the image with matplotlib.
        if not self.plt:
            from matplotlib import pyplot
            self.plt = pyplot
        a = self.array(width, ascender=ascender, descender=descender, even_odd=even_odd, scale=scale)
        self.plt.imshow(a, cmap='gray_r', vmin=0, vmax=1)
        self.plt.show()

    def image(self, width=1000, ascender=880, descender=-120, even_odd=False, scale=None):
        # Return a PIL image.
        if not self.Image:
            from PIL import Image as PILImage
            self.Image = PILImage
        buf, size = self.buffer(width, ascender=ascender, descender=descender, even_odd=even_odd, scale=scale)
        img = self.Image.new('L', size, 0)
        img.putalpha(self.Image.frombuffer('L', size, buf))
        return img

    def save(self, fp, width=1000, ascender=880, descender=-120, even_odd=False, scale=None, format=None, **kwargs):
        # Save the image as a file.
        img = self.image(width=width, ascender=ascender, descender=descender, even_odd=even_odd, scale=scale)
        img.save(fp, format=format, **kwargs)

    @property
    def bbox(self):
        # Compute the exact bounding box of an outline.
        bbox = FT_BBox()
        outline = self.outline()
        FT_Outline_Get_BBox(ctypes.byref(outline), ctypes.byref(bbox))
        return (bbox.xMin / 64.0, bbox.yMin / 64.0, bbox.xMax / 64.0, bbox.yMax / 64.0)

    @property
    def cbox(self):
        # Return an outline's ‘control box’.
        cbox = FT_BBox()
        outline = self.outline()
        FT_Outline_Get_CBox(ctypes.byref(outline), ctypes.byref(cbox))
        return (cbox.xMin / 64.0, cbox.yMin / 64.0, cbox.xMax / 64.0, cbox.yMax / 64.0)

    def _moveTo(self, pt):
        contour = self.Contour([], [])
        self.contours.append(contour)
        contour.points.append(pt)
        contour.tags.append(self.LINE)

    def _lineTo(self, pt):
        contour = self.contours[-1]
        contour.points.append(pt)
        contour.tags.append(self.LINE)

    def _curveToOne(self, p1, p2, p3):
        t1, t2, t3 = self.OFFCURVE, self.OFFCURVE, self.CURVE
        contour = self.contours[-1]
        for p, t in ((p1, t1), (p2, t2), (p3, t3)):
            contour.points.append(p)
            contour.tags.append(t)

    def _qCurveToOne(self, p1, p2):
        t1, t2 = self.QOFFCURVE, self.QCURVE
        contour = self.contours[-1]
        for p, t in ((p1, t1), (p2, t2)):
            contour.points.append(p)
            contour.tags.append(t)
