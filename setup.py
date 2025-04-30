import os

from setuptools import setup, Extension

###
# Force distutils to use py_compile.compile() function with 'doraise' argument
# set to True, in order to raise an exception on compilation errors
import py_compile

orig_py_compile = py_compile.compile


def doraise_py_compile(file, cfile=None, dfile=None, doraise=False):
    orig_py_compile(file, cfile=cfile, dfile=dfile, doraise=True)


py_compile.compile = doraise_py_compile
###


should_use_cython = os.environ.get("FONTTOOLS_WITH_CYTHON") is not None
ext_modules = []
if should_use_cython:
    ext_modules.append(
        Extension("fontTools.cu2qu.cu2qu", ["Lib/fontTools/cu2qu/cu2qu.py"]),
    )
    ext_modules.append(
        Extension("fontTools.qu2cu.qu2cu", ["Lib/fontTools/qu2cu/qu2cu.py"]),
    )
    ext_modules.append(
        Extension("fontTools.misc.bezierTools", ["Lib/fontTools/misc/bezierTools.py"]),
    )
    ext_modules.append(
        Extension("fontTools.pens.momentsPen", ["Lib/fontTools/pens/momentsPen.py"]),
    )
    ext_modules.append(
        Extension("fontTools.varLib.iup", ["Lib/fontTools/varLib/iup.py"]),
    )
    ext_modules.append(
        Extension("fontTools.feaLib.lexer", ["Lib/fontTools/feaLib/lexer.py"]),
    )


setup(
    ext_modules=ext_modules,
)
