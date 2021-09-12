############################################
macRes: Tools for reading Mac resource forks
############################################

Classic Mac OS files are made up of two parts - the "data fork" which contains the file contents proper, and the "resource fork" which contains a number of structured data items called "resources". Some fonts, such as Mac "font suitcases" and Type 1 LWFN fonts, still use the resource fork for this kind of structured data, and so to read them, fontTools needs to have access to resource forks.

The Inside Macintosh volume `More Macintosh Toolbox <https://developer.apple.com/library/archive/documentation/mac/pdf/MoreMacintoshToolbox.pdf#page=34>`_ explains the structure of resource and data forks.

.. automodule:: fontTools.misc.macRes
   :members: ResourceReader, Resource
   :member-order: bysource