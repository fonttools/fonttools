"""A pen that rasterises outlines with FreeType."""

__all__ = ['FTPen']

import os
import ctypes
import ctypes.util
import platform
import subprocess
import collections
import math

from fontTools.pens.basePen import BasePen
from fontTools.misc.roundTools import otRound

class FT_LibraryRec(ctypes.Structure):
    _fields_ = []

FT_Library = ctypes.POINTER(FT_LibraryRec)
FT_Pos = ctypes.c_long

class FT_Vector(ctypes.Structure):
    _fields_ = [('x', FT_Pos), ('y', FT_Pos)]

class FT_BBox(ctypes.Structure):
    _fields_ = [('xMin', FT_Pos), ('yMin', FT_Pos), ('xMax', FT_Pos), ('yMax', FT_Pos)]

class FT_Bitmap(ctypes.Structure):
    _fields_ = [('rows', ctypes.c_int), ('width', ctypes.c_int), ('pitch', ctypes.c_int), ('buffer', ctypes.POINTER(ctypes.c_ubyte)), ('num_grays', ctypes.c_short), ('pixel_mode', ctypes.c_ubyte), ('palette_mode', ctypes.c_char), ('palette', ctypes.c_void_p)]

class FT_Outline(ctypes.Structure):
    _fields_ = [('n_contours', ctypes.c_short), ('n_points', ctypes.c_short), ('points', ctypes.POINTER(FT_Vector)), ('tags', ctypes.POINTER(ctypes.c_ubyte)), ('contours', ctypes.POINTER(ctypes.c_short)), ('flags', ctypes.c_int)]

class FreeType(object):

    @staticmethod
    def load_freetype_lib():
        lib_path = ctypes.util.find_library('freetype')
        if lib_path:
            return ctypes.cdll.LoadLibrary(lib_path)
        if platform.system() == 'Darwin':
            # Try again by searching inside the installation paths of Homebrew and MacPorts
            # This workaround is needed if Homebrew has been installed to a non-standard location.
            orig_dyld_path = os.environ.get('DYLD_LIBRARY_PATH')
            for dyld_path_func in (
                lambda: os.path.join(subprocess.check_output(('brew', '--prefix'), universal_newlines=True).rstrip(), 'lib'),
                lambda: os.path.join(os.path.dirname(os.path.dirname(subprocess.check_output(('which', 'port'), universal_newlines=True).rstrip())), 'lib')
            ):
                try:
                    dyld_path = dyld_path_func()
                    os.environ['DYLD_LIBRARY_PATH'] = ':'.join(os.environ.get('DYLD_LIBRARY_PATH', '').split(':') + [dyld_path])
                    lib_path = ctypes.util.find_library('freetype')
                    if lib_path:
                        return ctypes.cdll.LoadLibrary(lib_path)
                except CalledProcessError:
                    pass
                finally:
                    if orig_dyld_path:
                        os.environ['DYLD_LIBRARY_PATH'] = orig_dyld_path
                    else:
                        os.environ.pop('DYLD_LIBRARY_PATH', None)
        return None

    def __init__(self):
        lib = self.load_freetype_lib()
        self.handle = FT_Library()
        self.FT_Init_FreeType      = lib.FT_Init_FreeType
        self.FT_Done_FreeType      = lib.FT_Done_FreeType
        self.FT_Library_Version    = lib.FT_Library_Version
        self.FT_Outline_Get_CBox   = lib.FT_Outline_Get_CBox
        self.FT_Outline_Get_BBox   = lib.FT_Outline_Get_BBox
        self.FT_Outline_Get_Bitmap = lib.FT_Outline_Get_Bitmap
        self.raise_error_if_needed(self.FT_Init_FreeType(ctypes.byref(self.handle)))

    def raise_error_if_needed(self, err):
        # See the reference for error codes:
        #   https://freetype.org/freetype2/docs/reference/ft2-error_code_values.html
        if err != 0:
            raise RuntimeError("FT_Error: 0x{0:02X}".format(err))

    def __del__(self):
        if self.handle:
            self.FT_Done_FreeType(self.handle)

    @property
    def version(self):
        major, minor, patch = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
        self.FT_Library_Version(self.handle, ctypes.byref(major), ctypes.byref(minor), ctypes.byref(patch))
        return "{0}.{1}.{2}".format(major.value, minor.value, patch.value)

class FTPen(BasePen):

    ft = None
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
        if not self.__class__.ft:
            self.__class__.ft = FreeType()
        self.contours = []

    def outline(self, offset=None, scale=None, even_odd=False):
        # Convert the current contours to FT_Outline.
        FT_OUTLINE_NONE = 0x0
        FT_OUTLINE_EVEN_ODD_FILL = 0x2
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
        FT_PIXEL_MODE_GRAY = 2
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
        self.ft.raise_error_if_needed(self.ft.FT_Outline_Get_Bitmap(self.ft.handle, ctypes.byref(outline), ctypes.byref(bitmap)))
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
        self.ft.FT_Outline_Get_BBox(ctypes.byref(outline), ctypes.byref(bbox))
        return (bbox.xMin / 64.0, bbox.yMin / 64.0, bbox.xMax / 64.0, bbox.yMax / 64.0)

    @property
    def cbox(self):
        # Return an outline's ‘control box’.
        cbox = FT_BBox()
        outline = self.outline()
        self.ft.FT_Outline_Get_CBox(ctypes.byref(outline), ctypes.byref(cbox))
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
