eexecOp is imported by the fontTools.misc.eexec module, and the latter
provides a (slow) Python implementation in case eexecOp isn't there.
It is designed to be a shared library, to be placed in 
    FontTools/Lib/fontTools/misc/
but it should also work as a (possibly statically linked) top level module.

It is built automatically when you run

   python setup.py build
or
   python setup.py install

in the top level FontTools directory.

Just
