########################################
qu2cu: Convert quadratic curves to cubic
########################################

.. rubric:: Overview
   :heading-level: 2


Routines for converting quadratic curves to cubic splines, suitable for use
in TrueType to CFF-flavored OpenType outline conversion.

The basic curve conversion routines are implemented in the
:mod:`fontTools.qu2cu.qu2cu` module.

.. note:: The redundancy in the module name is a workaround made
	  made necessary by :mod:`fontTools.qu2cu`'s usage of
	  `Cython <https://cython.org/>`_. Providing Cython support
	  for the module enables faster execution on systems where
	  Cython is available. However, the module remains fully
	  available on systems without Cython, too.

.. automodule:: fontTools.qu2cu.qu2cu
   :members:
   :undoc-members:

    qu2cu also includes a submodule that implements the
    ``fonttools qu2cu`` command for converting a UFO format font with
    quadratic curves into one with cubic curves:
		   
     .. toctree::
        :maxdepth: 1

        cli

    
     .. rubric:: Package contents
        :heading-level: 2

