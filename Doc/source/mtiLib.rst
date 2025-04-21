###########################################
mtiLib: Read Monotype FontDame source files
###########################################

.. rubric:: Overview
   :heading-level: 2

FontTools provides support for reading the OpenType Layout tables produced by
Monotype's FontDame and Font Chef font editors. These tables are written in a
simple textual format. The :py:mod:`mtiLib` library parses these text files and creates
table objects representing their contents.

Additionally, running the ``fonttools mtiLib`` command will convert a text file to TTX XML.


.. rubric:: Module members:
   :heading-level: 2

		   
.. autofunction:: fontTools.mtiLib.build

.. autofunction:: fontTools.mtiLib.main

		       
.. automodule:: fontTools.mtiLib
   :members: 
   :undoc-members:
   :exclude-members: build, main
