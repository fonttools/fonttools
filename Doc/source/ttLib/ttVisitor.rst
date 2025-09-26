###################################################################
ttVisitor: Specialization of the visitor module to work with TTFont
###################################################################

.. rubric:: Overview
   :heading-level: 2

The :mod:`ttLib.ttVisitor <fontTools.ttLib.ttVisitor>` module is a helper for
:mod:`ttLib.ttFont <fontTools.ttLib.ttFont>`.

It supports the use of the :mod:`fontTools.misc.visitor` module by extending
:class:`Visitor <fontTools.misc.visitor.Visitor>` to handle common
:class:`TTFont <fontTools.ttLib.ttFont.TTFont>` edge-cases. Primarily, the extra
handling is to avoid traversing cyclical back-references to the root font
object.


Package contents
----------------

.. automodule:: fontTools.ttLib.ttVisitor
   :members:
   :undoc-members:
