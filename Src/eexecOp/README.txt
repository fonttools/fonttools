eexecOp is imported by the fontTools.misc.eexec module, and the latter
provides a (slow) Python implementation in case eexecOp isn't there.
It is designed to be a shared library, to be placed in 
    FontTools/Lib/fontTools/misc/
but it should also work as a statically linked top level module.

Other files in this directory:
eexecOp.ppc.prj       a Metrowerks CodeWarrior project file for MacOS
eexecOp.ppc.prj.exp   an export file, exporting the initeexecOp symbol.

What else should be in this directory:
Makefiles for other compilers. Any help appreciated, since I'm still 
a Mac-only guy!

Just
