########################################
voltLib: Read and write MS VOLT projects
########################################

.. currentmodule:: fontTools.voltLib

.. contents:: On this page:
    :local:
       
.. rubric:: Overview:
   :heading-level: 2

:mod:`fontTools.voltLib` provides support for working with the project
files from Microsoft's Visual OpenType Layout Tool (VOLT), a Windows
GUI utility used to add and edit OpenType Layout tables in fonts.

The primary interface is :mod:`fontTools.voltLib.voltToFea`, which
enables conversion of of VOLT files to the Adobe .fea format:

.. toctree::
   :maxdepth: 2

   voltToFea


.. rubric:: Modules
   :heading-level: 2

voltLib also contains modules that implement lower-level parsing,
lexing, and analysis of VOLT project files.


fontTools.voltLib
-----------------

.. automodule:: fontTools.voltLib
   :members:
   :undoc-members:

      
fontTools.voltLib.ast
---------------------

.. currentmodule:: fontTools.voltLib.ast

.. automodule:: fontTools.voltLib.ast
   :members:
   :undoc-members:

      
fontTools.voltLib.error
-----------------------

.. currentmodule:: fontTools.voltLib.error

.. automodule:: fontTools.voltLib.error
   :members:
   :undoc-members:

      
fontTools.voltLib.lexer
-----------------------

.. currentmodule:: fontTools.voltLib.lexer

.. automodule:: fontTools.voltLib.lexer
   :members:
   :undoc-members:


fontTools.voltLib.parser
------------------------

.. currentmodule:: fontTools.voltLib.parser

.. automodule:: fontTools.voltLib.parser
   :members:
   :undoc-members:
