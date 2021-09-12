###########################################
mtiLib: Read Monotype FontDame source files
###########################################

FontTools provides support for reading the OpenType layout tables produced by
Monotype's FontDame and Font Chef font editors. These tables are written in a
simple textual format. The ``mtiLib`` library parses these text files and creates
table objects representing their contents.

Additionally, ``fonttools mtiLib`` will convert a text file to TTX XML.


.. automodule:: fontTools.mtiLib
   :members: build, main
