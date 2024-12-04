##########################
Base table classes and API
##########################

.. contents:: On this page:
    :local:

.. rubric:: Overview:
   :heading-level: 2

The modules documented on this page are the base classes on which the
:mod:`fontTools.ttLib` table converters are built. The
:class:`.DefaultTable` is the most general; :class:`.asciiTable` is a
simpler option for storing text-based data. For OpenType and TrueType
fonts, the :class:`.otBase.BaseTTXConverter` leverages the model used
by the majority of existing OpenType/TrueType converters.


Contributing your own table convertors
--------------------------------------

To add support for a new font table that fontTools does not currently implement,
you must subclass from :py:mod:`fontTools.ttLib.tables.DefaultTable.DefaultTable`.
It provides some default behavior, as well as a constructor method (``__init__``)
that you don't need to override.

Your converter should minimally provide two methods::


    class table_F_O_O_(DefaultTable.DefaultTable): # converter for table 'FOO '

        def decompile(self, data, ttFont):
            # 'data' is the raw table data. Unpack it into a
            # Python data structure.
            # 'ttFont' is a ttLib.TTfile instance, enabling you to
            # refer to other tables. Do ***not*** keep a reference to
            # it: it will cause a circular reference (ttFont saves
            # a reference to us), and that means we'll be leaking
            # memory. If you need to use it in other methods, just
            # pass it around as a method argument.

        def compile(self, ttFont):
            # Return the raw data, as converted from the Python
            # data structure.
            # Again, 'ttFont' is there so you can access other tables.
            # Same warning applies.


If you want to support TTX import/export as well, you need to provide two
additional methods::


   def toXML(self, writer, ttFont):
      # XXX

   def fromXML(self, (name, attrs, content), ttFont):
      # XXX

      

fontTools.ttLib.tables.DefaultTable
-----------------------------------

.. automodule:: fontTools.ttLib.tables.DefaultTable
   :members:
   :undoc-members:


fontTools.ttLib.tables.asciiTable
---------------------------------

.. automodule:: fontTools.ttLib.tables.asciiTable
   :members:
   :undoc-members:


fontTools.ttLib.tables.otBase
-----------------------------

.. automodule:: fontTools.ttLib.tables.otBase
   :members:
   :undoc-members:

