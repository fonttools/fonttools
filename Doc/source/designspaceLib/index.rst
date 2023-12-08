#######################################################
designspaceLib: Read, write, and edit designspace files
#######################################################

Implements support for reading and manipulating ``designspace`` files.
Allows the users to define axes, rules, sources, variable fonts and instances,
and their STAT information.

.. toctree::
   :maxdepth: 1

   python
   xml
   scripting


Notes
=====

Paths and filenames
-------------------

A designspace file needs to store many references to UFO files.

-  designspace files can be part of versioning systems and appear on
   different computers. This means it is not possible to store absolute
   paths.
-  So, all paths are relative to the designspace document path.
-  Using relative paths allows designspace files and UFO files to be
   **near** each other, and that they can be **found** without enforcing
   one particular structure.
-  The **filename** attribute in the ``SourceDescriptor`` and
   ``InstanceDescriptor`` classes stores the preferred relative path.
-  The **path** attribute in these objects stores the absolute path. It
   is calculated from the document path and the relative path in the
   filename attribute when the object is created.
-  Only the **filename** attribute is written to file.
-  Both **filename** and **path** must use forward slashes (``/``) as
   path separators, even on Windows.

Right before we save we need to identify and respond to the following
situations:

In each descriptor, we have to do the right thing for the filename
attribute. Before writing to file, the ``documentObject.updatePaths()``
method prepares the paths as follows:

**Case 1**

::

    descriptor.filename == None
    descriptor.path == None

**Action**

-  write as is, descriptors will not have a filename attr. Useless, but
   no reason to interfere.

**Case 2**

::

    descriptor.filename == "../something"
    descriptor.path == None

**Action**

-  write as is. The filename attr should not be touched.

**Case 3**

::

    descriptor.filename == None
    descriptor.path == "~/absolute/path/there"

**Action**

-  calculate the relative path for filename. We're not overwriting some
   other value for filename, it should be fine.

**Case 4**

::

    descriptor.filename == '../somewhere'
    descriptor.path == "~/absolute/path/there"

**Action**

-  There is a conflict between the given filename, and the path. The
   difference could have happened for any number of reasons. Assuming
   the values were not in conflict when the object was created, either
   could have changed. We can't guess.
-  Assume the path attribute is more up to date. Calculate a new value
   for filename based on the path and the document path.

Recommendation for editors
--------------------------

-  If you want to explicitly set the **filename** attribute, leave the
   path attribute empty.
-  If you want to explicitly set the **path** attribute, leave the
   filename attribute empty. It will be recalculated.
-  Use ``documentObject.updateFilenameFromPath()`` to explicitly set the
   **filename** attributes for all instance and source descriptors.


Common Lib Key Registry
=======================

public.skipExportGlyphs
-----------------------

This lib key works the same as the UFO lib key with the same name. The
difference is that applications using a Designspace as the corner stone of the
font compilation process should use the lib key in that Designspace instead of
any of the UFOs. If the lib key is empty or not present in the Designspace, all
glyphs should be exported, regardless of what the same lib key in any of the
UFOs says.

public.fontInfo
-----------------------

This lib key, when included in the ``<lib>`` element inside an ``<instance>`` 
or ``<variable-font>`` tag, or the ``<lib>`` element at the root of a 
designspace document, allows for direct manipulation of font info data in 
instances and variable fonts. The lib value must follow the 
`UFO3 fontinfo.plist specification <https://unifiedfontobject.org/versions/ufo3/fontinfo.plist/>`_,
and should functionally appear to be a property list dictionary with the same 
structure as the ``fontinfo.plist`` file in a UFO.

All font info items in the UFO fontinfo.plist specification should be able to 
be defined in the ``public.fontInfo`` lib. Checking validity of the data using 
``fontTools.ufoLib.validators`` is recommended but not required. 

All font info items for a variable font or an instance must be inherited using 
the following order, in order of descending priority:

#. The ``public.fontInfo`` key in the ``<lib>`` element of the ``<variable-font>``
   or ``<instance>`` elements.
#. XML attributes for names (i.e. ``familyname``, ``stylename``, etc.), if the
   target is an ``<instance>`` element.
#. The ``public.fontInfo`` key found in the ``<lib>`` element of the designspace
   document's root.
#. The ``fontinfo.plist`` in the UFO source at the origin of the interpolation 
   space.

Absence of a font info key from the value of a ``public.fontInfo`` lib does 
**not** mean a that piece of font info should be interpreted as being undefined. 
A tool generating the variable font or instance should recursively continue on 
to the next level of the inheritence order and apply the value found there, if 
any. If the tool makes it to the end of the inheritence order without finding a 
valid value for a given font info key, it should then be considered undefined. 
In the case of any conflicting values for a font info key, the value highest in 
the inheritance order must be chosen over the others.

Implementation and differences
==============================

The designspace format has gone through considerable development.

 -  the format was originally written for MutatorMath.
 -  the format is now also used in fontTools.varLib.
 -  not all values are be required by all implementations.

varLib vs. MutatorMath
----------------------

There are some differences between the way MutatorMath and fontTools.varLib handle designspaces.

 -  varLib does not support anisotropic interpolations.
 -  MutatorMath will extrapolate over the boundaries of
    the axes. varLib can not (at the moment).
 -  varLib requires much less data to define an instance than
    MutatorMath.
 -  The goals of varLib and MutatorMath are different, so not all
    attributes are always needed.


Rules and generating static UFO instances
-----------------------------------------

When making instances as UFOs from a designspace with rules, it can
be useful to evaluate the rules so that the characterset of the UFO
reflects, as much as possible, the state of a variable font when seen
at the same location. This can be done by some swapping and renaming of
glyphs.

While useful for proofing or development work, it should be noted that
swapping and renaming leaves the UFOs with glyphnames that are no longer
descriptive. For instance, after a swap ``dollar.bar`` could contain a shape
without a bar. Also, when the swapped glyphs are part of other GSUB variations
it can become complex very quickly. So proceed with caution.

 -  Assuming ``rulesProcessingLast = True``:
 -  We need to swap the glyphs so that the original shape is still available.
    For instance, if a rule swaps ``a`` for ``a.alt``, a glyph
    that references ``a`` in a component would then show the new ``a.alt``.
 -  But that can lead to unexpected results, the two glyphs may have different
    widths or height. So, glyphs that are not specifically referenced in a rule
    **should not change appearance**. That means that the implementation that swaps
    ``a`` and ``a.alt`` also swap all components that reference these
    glyphs in order to preserve their appearance.
 -  The swap function also needs to take care of swapping the names in
    kerning data and any GPOS code.

Version history
===============

Version 5.1
-----------

The format was extended to support arbitrary mapping between input and output
designspace locations. The ``<axes>`` elements now can have a ``<mappings>``
element that specifies such mappings, which when present carries data that is
used to compile to an ``avar`` version 2 table.

Version 5.0
-----------

The format was extended to describe the entire design space of a reasonably
regular font family in one file, with global data about the family to reduce
repetition in sub-sections. "Reasonably regular" means that the sources and
instances across the previously multiple Designspace files are positioned on a
grid and derive their metadata (like style name) in a way that's compatible with
the STAT model, based on their axis positions. Axis mappings must be the same
across the entire space.

1. Each axis can have labels attached to stops within the axis range, analogous to the
   `OpenType STAT <https://docs.microsoft.com/en-us/typography/opentype/spec/stat>`_
   table. Free-standing labels for locations are also allowed. The data is intended
   to be compiled into a ``STAT`` table.
2. The axes can be discrete, to say that they do not interpolate, like a distinctly
   constructed upright and italic variant of a family.
3. The data can be used to derive style and PostScript names for instances.
4. A new ``variable-fonts`` element can subdivide the Designspace into multiple subsets that
   mix and match the globally available axes. It is possible for these sub-spaces to have
   a different default location from the global default location. It is required if the
   Designspace contains a discrete axis and you want to produce a variable font.

What is currently not supported is e.g.

1. A setup where different sources sit at the same logical location in the design space,
   think "MyFont Regular" and "MyFont SmallCaps Regular". (this situation could be
   encoded by adding a "SmallCaps" discrete axis, if that makes sense).
2. Anisotropic locations for axis labels.

Older versions
--------------

-  In some implementations that preceed Variable Fonts, the `copyInfo`
   flag in a source indicated the source was to be treated as the default.
   This is no longer compatible with the assumption that the default font
   is located on the default value of each axis.
-  Older implementations did not require axis records to be present in
   the designspace file. The axis extremes for instance were generated
   from the locations used in the sources. This is no longer possible.

