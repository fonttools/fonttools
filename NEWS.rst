3.9.1 (released 2017-03-20)
---------------------------

- [varLib.merger] Fixed issue while recombining multiple PairPosFormat2
  subtables if they were split because of offset overflows (9798c30).
- [varLib.merger] Only merge multiple PairPosFormat1 subtables if there is
  at least one of the fonts with a non-empty Format1 subtable (0f5a46b).
- [varLib.merger] Fixed IndexError with empty ClassDef1 in PairPosFormat2
  (aad0d46).
- [varLib.merger] Avoid reusing Class2Record (mutable) objects (e6125b3).
- [varLib.merger] Calculate ClassDef1 and ClassDef2's Format when merging
  PairPosFormat2 (23511fd).
- [macUtils] Added missing ttLib import (b05f203).

3.9.0 (released 2017-03-13)
---------------------------

- [feaLib] Added (partial) support for parsing feature file comments ``# ...``
  appearing in between statements (#879).
- [feaLib] Cleaned up syntax tree for FeatureNames.
- [ttLib] Added support for reading/writing ``CFF2`` table (thanks to
  @readroberts at Adobe), and ``TTFA`` (ttfautohint) table.
- [varLib] Fixed regression introduced with 3.8.0 in the calculation of
  ``NumShorts``, i.e. the number of deltas in ItemVariationData's delta sets
  that use a 16-bit representation (b2825ff).

3.8.0 (released 2017-03-05)
---------------------------

- New pens: MomentsPen, StatisticsPen, RecordingPen, and TeePen.
- [misc] Added new ``fontTools.misc.symfont`` module, for symbolic font
  statistical analysis; requires ``sympy`` (http://www.sympy.org/en/index.html)
- [varLib] Added experimental ``fontTools.varLib.interpolatable`` module for
  finding wrong contour order between different masters
- [varLib] designspace.load() now returns a dictionary, instead of a tuple,
  and supports <axes> element (#864); the 'masters' item was renamed 'sources',
  like the <sources> element in the designspace document
- [ttLib] Fixed issue with recalculating ``head`` modified timestamp when
  saving CFF fonts
- [ttLib] In TupleVariation, round deltas before compiling (#861, fixed #592)
- [feaLib] Ignore duplicate glyphs in classes used as MarkFilteringSet and
  MarkAttachmentType (#863)
- [merge] Changed the ``gasp`` table merge logic so that only the one from
  the first font is retained, similar to other hinting tables (#862)
- [Tests] Added tests for the ``varLib`` package, as well as test fonts
  from the "Annotated OpenType Specification" (AOTS) to exercise ``ttLib``'s
  table readers/writers (<https://github.com/adobe-type-tools/aots>)

3.7.2 (released 2017-02-17)
---------------------------

- [subset] Keep advance widths when stripping ".notdef" glyph outline in
  CID-keyed CFF fonts (#845)
- [feaLib] Zero values now produce the same results as makeotf (#633, #848)
- [feaLib] More compact encoding for “Contextual positioning with in-line
  single positioning rules” (#514)

3.7.1 (released 2017-02-15)
---------------------------

- [subset] Fixed issue with ``--no-hinting`` option whereby advance widths in
  Type 2 charstrings were also being stripped (#709, #343)
- [feaLib] include statements now resolve relative paths like makeotf (#838)
- [feaLib] table ``name`` now handles Unicode codepoints beyond the Basic
  Multilingual Plane, also supports old-style MacOS platform encodings (#842)
- [feaLib] correctly escape string literals when emitting feature syntax (#780)

3.7.0 (released 2017-02-11)
---------------------------

- [ttx, mtiLib] Preserve ordering of glyph alternates in GSUB type 3 (#833).
- [feaLib] Glyph names can have dashes, as per new AFDKO syntax v1.20 (#559).
- [feaLib] feaLib.Parser now needs the font's glyph map for parsing.
- [varLib] Fix regression where GPOS values were stored as 0.
- [varLib] Allow merging of class-based kerning when ClassDefs are different

3.6.3 (released 2017-02-06)
---------------------------

- [varLib] Fix building variation of PairPosFormat2 (b5c34ce).
- Populate defaults even for otTables that have postRead (e45297b).
- Fix compiling of MultipleSubstFormat1 with zero 'out' glyphs (b887860).

3.6.2 (released 2017-01-30)
---------------------------

- [varLib.merger] Fixed "TypeError: reduce() of empty sequence with no
  initial value" (3717dc6).

3.6.1 (released 2017-01-28)
---------------------------

-  [py23] Fixed unhandled exception occurring at interpreter shutdown in
   the "last resort" logging handler (972b3e6).
-  [agl] Ensure all glyph names are of native 'str' type; avoid mixing
   'str' and 'unicode' in TTFont.glyphOrder (d8c4058).
-  Fixed inconsistent title levels in README.rst that caused PyPI to
   incorrectly render the reStructuredText page.

3.6.0 (released 2017-01-26)
---------------------------

-  [varLib] Refactored and improved the variation-font-building process.
-  Assembly code in the fpgm, prep, and glyf tables is now indented in
   XML output for improved readability. The ``instruction`` element is
   written as a simple tag if empty (#819).
-  [ttx] Fixed 'I/O operation on closed file' error when dumping
   multiple TTXs to standard output with the '-o -' option.
-  The unit test modules (``*_test.py``) have been moved outside of the
   fontTools package to the Tests folder, thus they are no longer
   installed (#811).

3.5.0 (released 2017-01-14)
---------------------------

-  Font tables read from XML can now be written back to XML with no
   loss.
-  GSUB/GPOS LookupType is written out in XML as an element, not
   comment. (#792)
-  When parsing cmap table, do not store items mapped to glyph id 0.
   (#790)
-  [otlLib] Make ClassDef sorting deterministic. Fixes #766 (7d1ddb2)
-  [mtiLib] Added unit tests (#787)
-  [cvar] Implemented cvar table
-  [gvar] Renamed GlyphVariation to TupleVariation to match OpenType
   terminology.
-  [otTables] Handle gracefully empty VarData.Item array when compiling
   XML. (#797)
-  [varLib] Re-enabled generation of ``HVAR`` table for fonts with
   TrueType outlines; removed ``--build-HVAR`` command-line option.
-  [feaLib] The parser can now be extended to support non-standard
   statements in FEA code by using a customized Abstract Syntax Tree.
   See, for example, ``feaLib.builder_test.test_extensions`` and
   baseClass.feax (#794, fixes #773).
-  [feaLib] Added ``feaLib`` command to the 'fonttools' command-line
   tool; applies a feature file to a font. ``fonttools feaLib -h`` for
   help.
-  [pens] The ``T2CharStringPen`` now takes an optional
   ``roundTolerance`` argument to control the rounding of coordinates
   (#804, fixes #769).
-  [ci] Measure test coverage on all supported python versions and OSes,
   combine coverage data and upload to
   https://codecov.io/gh/fonttools/fonttools (#786)
-  [ci] Configured Travis and Appveyor for running tests on Python 3.6
   (#785, 55c03bc)
-  The manual pages installation directory can be customized through
   ``FONTTOOLS_MANPATH`` environment variable (#799, fixes #84).
-  [Snippets] Added otf2ttf.py, for converting fonts from CFF to
   TrueType using the googlei18n/cu2qu module (#802)

3.4.0 (released 2016-12-21)
---------------------------

-  [feaLib] Added support for generating FEA text from abstract syntax
   tree (AST) objects (#776). Thanks @mhosken
-  Added ``agl.toUnicode`` function to convert AGL-compliant glyph names
   to Unicode strings (#774)
-  Implemented MVAR table (b4d5381)

3.3.1 (released 2016-12-15)
---------------------------

-  [setup] We no longer use versioneer.py to compute fonttools version
   from git metadata, as this has caused issues for some users (#767).
   Now we bump the version strings manually with a custom ``release``
   command of setup.py script.

3.3.0 (released 2016-12-06)
---------------------------

-  [ttLib] Implemented STAT table from OpenType 1.8 (#758)
-  [cffLib] Fixed decompilation of CFF fonts containing non-standard
   key/value pairs in FontDict (issue #740; PR #744)
-  [py23] minor: in ``round3`` function, allow the second argument to be
   ``None`` (#757)
-  The standalone ``sstruct`` and ``xmlWriter`` modules, deprecated
   since vesion 3.2.0, have been removed. They can be imported from the
   ``fontTools.misc`` package.

3.2.3 (released 2016-12-02)
---------------------------

-  [py23] optimized performance of round3 function; added backport for
   py35 math.isclose() (9d8dacb)
-  [subset] fixed issue with 'narrow' (UCS-2) Python 2 builds and
   ``--text``/``--text-file`` options containing non-BMP chararcters
   (16d0e5e)
-  [varLib] fixed issuewhen normalizing location values (8fa2ee1, #749)
-  [inspect] Made it compatible with both python2 and python3 (167ee60,
   #748). Thanks @pnemade

3.2.2 (released 2016-11-24)
---------------------------

-  [varLib] Do not emit null axes in fvar (1bebcec). Thanks @robmck-ms
-  [varLib] Handle fonts without GPOS (7915a45)
-  [merge] Ignore LangSys if None (a11bc56)
-  [subset] Fix subsetting MathVariants (78d3cbe)
-  [OS/2] Fix "Private Use (plane 15)" range (08a0d55). Thanks @mashabow

3.2.1 (released 2016-11-03)
---------------------------

-  [OS/2] fix checking ``fsSelection`` bits matching ``head.macStyle``
   bits
-  [varLib] added ``--build-HVAR`` option to generate ``HVAR`` table for
   fonts with TrueType outlines. For ``CFF2``, it is enabled by default.

3.2.0 (released 2016-11-02)
---------------------------

-  [varLib] Improve support for OpenType 1.8 Variable Fonts:
-  Implement GDEF's VariationStore
-  Implement HVAR/VVAR tables
-  Partial support for loading MutatorMath .designspace files with
   varLib.designspace module
-  Add varLib.models with Variation fonts interpolation models
-  Implement GSUB/GPOS FeatureVariations
-  Initial support for interpolating and merging OpenType Layout tables
   (see ``varLib.interpolate_layout`` and ``varLib.merger`` modules)
-  [API change] Change version to be an integer instead of a float in
   XML output for GSUB, GPOS, GDEF, MATH, BASE, JSTF, HVAR, VVAR, feat,
   hhea and vhea tables. Scripts that set the Version for those to 1.0
   or other float values also need fixing. A warning is emitted when
   code or XML needs fix.
-  several bug fixes to the cffLib module, contributed by Adobe's
   @readroberts
-  The XML output for CFF table now has a 'major' and 'minor' elements
   for specifying whether it's version 1.0 or 2.0 (support for CFF2 is
   coming soon)
-  [setup.py] remove undocumented/deprecated ``extra_path`` Distutils
   argument. This means that we no longer create a "FontTools" subfolder
   in site-packages containing the actual fontTools package, as well as
   the standalone xmlWriter and sstruct modules. The latter modules are
   also deprecated, and scheduled for removal in upcoming releases.
   Please change your import statements to point to from fontTools.misc
   import xmlWriter and from fontTools.misc import sstruct.
-  [scripts] Add a 'fonttools' command-line tool that simply runs
   ``fontTools.*`` sub-modules: e.g. ``fonttools ttx``,
   ``fonttools subset``, etc.
-  [hmtx/vmts] Read advance width/heights as unsigned short (uint16);
   automatically round float values to integers.
-  [ttLib/xmlWriter] add 'newlinestr=None' keyword argument to
   ``TTFont.saveXML`` for overriding os-specific line endings (passed on
   to ``XMLWriter`` instances).
-  [versioning] Use versioneer instead of ``setuptools_scm`` to
   dynamically load version info from a git checkout at import time.
-  [feaLib] Support backslash-prefixed glyph names.

3.1.2 (released 2016-09-27)
---------------------------

-  restore Makefile as an alternative way to build/check/install
-  README.md: update instructions for installing package from source,
   and for running test suite
-  NEWS: Change log was out of sync with tagged release

3.1.1 (released 2016-09-27)
---------------------------

-  Fix ``ttLibVersion`` attribute in TTX files still showing '3.0'
   instead of '3.1'.
-  Use ``setuptools_scm`` to manage package versions.

3.1.0 (released 2016-09-26)
---------------------------

-  [feaLib] New library to parse and compile Adobe FDK OpenType Feature
   files.
-  [mtiLib] New library to parse and compile Monotype 'FontDame'
   OpenType Layout Tables files.
-  [voltLib] New library to parse Microsoft VOLT project files.
-  [otlLib] New library to work with OpenType Layout tables.
-  [varLib] New library to work with OpenType Font Variations.
-  [pens] Add ttGlyphPen to draw to TrueType glyphs, and t2CharStringPen
   to draw to Type 2 Charstrings (CFF); add areaPen and perimeterPen.
-  [ttLib.tables] Implement 'meta' and 'trak' tables.
-  [ttx] Add --flavor option for compiling to 'woff' or 'woff2'; add
   ``--with-zopfli`` option to use Zopfli to compress WOFF 1.0 fonts.
-  [subset] Support subsetting 'COLR'/'CPAL' and 'CBDT'/'CBLC' color
   fonts tables, and 'gvar' table for variation fonts.
-  [Snippets] Add ``symfont.py``, for symbolic font statistics analysis;
   interpolatable.py, a preliminary script for detecting interpolation
   errors; ``{merge,dump}_woff_metadata.py``.
-  [classifyTools] Helpers to classify things into classes.
-  [CI] Run tests on Windows, Linux and macOS using Appveyor and Travis
   CI; check unit test coverage with Coverage.py/Coveralls; automatic
   deployment to PyPI on tags.
-  [loggingTools] Use Python built-in logging module to print messages.
-  [py23] Make round() behave like Python 3 built-in round(); define
   round2() and round3().

3.0 (released 2015-09-01)
-------------------------

-  Add Snippet scripts for cmap subtable format conversion, printing
   GSUB/GPOS features, building a GX font from two masters
-  TTX WOFF2 support and a ``-f`` option to overwrite output file(s)
-  Support GX tables: ``avar``, ``gvar``, ``fvar``, ``meta``
-  Support ``feat`` and gzip-compressed SVG tables
-  Upgrade Mac East Asian encodings to native implementation if
   available
-  Add Roman Croatian and Romanian encodings, codecs for mac-extended
   East Asian encodings
-  Implement optimal GLYF glyph outline packing; disabled by default

2.5 (released 2014-09-24)
-------------------------

-  Add a Qt pen
-  Add VDMX table converter
-  Load all OpenType sub-structures lazily
-  Add support for cmap format 13.
-  Add pyftmerge tool
-  Update to Unicode 6.3.0d3
-  Add pyftinspect tool
-  Add support for Google CBLC/CBDT color bitmaps, standard EBLC/EBDT
   embedded bitmaps, and ``SVG`` table (thanks to Read Roberts at Adobe)
-  Add support for loading, saving and ttx'ing WOFF file format
-  Add support for Microsoft COLR/CPAL layered color glyphs
-  Support PyPy
-  Support Jython, by replacing numpy with array/lists modules and
   removed it, pure-Python StringIO, not cStringIO
-  Add pyftsubset and Subsetter object, supporting CFF and TTF
-  Add to ttx args for -q for quiet mode, -z to choose a bitmap dump
   format

2.4 (released 2013-06-22)
-------------------------

-  Option to write to arbitrary files
-  Better dump format for DSIG
-  Better detection of OTF XML
-  Fix issue with Apple's kern table format
-  Fix mangling of TT glyph programs
-  Fix issues related to mona.ttf
-  Fix Windows Installer instructions
-  Fix some modern MacOS issues
-  Fix minor issues and typos

2.3 (released 2009-11-08)
-------------------------

-  TrueType Collection (TTC) support
-  Python 2.6 support
-  Update Unicode data to 5.2.0
-  Couple of bug fixes

2.2 (released 2008-05-18)
-------------------------

-  ClearType support
-  cmap format 1 support
-  PFA font support
-  Switched from Numeric to numpy
-  Update Unicode data to 5.1.0
-  Update AGLFN data to 1.6
-  Many bug fixes

2.1 (released 2008-01-28)
-------------------------

-  Many years worth of fixes and features

2.0b2 (released 2002-??-??)
---------------------------

-  Be "forgiving" when interpreting the maxp table version field:
   interpret any value as 1.0 if it's not 0.5. Fixes dumping of these
   GPL fonts: http://www.freebsd.org/cgi/pds.cgi?ports/chinese/wangttf
-  Fixed ttx -l: it turned out this part of the code didn't work with
   Python 2.2.1 and earlier. My bad to do most of my testing with a
   different version than I shipped TTX with :-(
-  Fixed bug in ClassDef format 1 subtable (Andreas Seidel bumped into
   this one).

2.0b1 (released 2002-09-10)
---------------------------

-  Fixed embarrassing bug: the master checksum in the head table is now
   calculated correctly even on little-endian platforms (such as Intel).
-  Made the cmap format 4 compiler smarter: the binary data it creates
   is now more or less as compact as possible. TTX now makes more
   compact data than in any shipping font I've tested it with.
-  Dump glyph names as a separate "GlyphOrder" pseudo table as opposed
   to as part of the glyf table (obviously needed for CFF-OTF's).
-  Added proper support for the CFF table.
-  Don't barf on empty tables (questionable, but "there are font out
   there...")
-  When writing TT glyf data, align glyphs on 4-byte boundaries. This
   seems to be the current recommendation by MS. Also: don't barf on
   fonts which are already 4-byte aligned.
-  Windows installer contributed bu Adam Twardoch! Yay!
-  Changed the command line interface again, now by creating one new
   tool replacing the old ones: ttx It dumps and compiles, depending on
   input file types. The options have changed somewhat.
-  The -d option is back (output dir)
-  ttcompile's -i options is now called -m (as in "merge"), to avoid
   clash with dump's -i.
-  The -s option ("split tables") no longer creates a directory, but
   instead outputs a small .ttx file containing references to the
   individual table files. This is not a true link, it's a simple file
   name, and the referenced file should be in the same directory so
   ttcompile can find them.
-  compile no longer accepts a directory as input argument. Instead it
   can parse the new "mini-ttx" format as output by "ttx -s".
-  all arguments are input files
-  Renamed the command line programs and moved them to the Tools
   subdirectory. They are now installed by the setup.py install script.
-  Added OpenType support. BASE, GDEF, GPOS, GSUB and JSTF are (almost)
   fully supported. The XML output is not yet final, as I'm still
   considering to output certain subtables in a more human-friendly
   manner.
-  Fixed 'kern' table to correctly accept subtables it doesn't know
   about, as well as interpreting Apple's definition of the 'kern' table
   headers correctly.
-  Fixed bug where glyphnames were not calculated from 'cmap' if it was
   (one of the) first tables to be decompiled. More specifically: it
   cmap was the first to ask for a glyphID -> glyphName mapping.
-  Switched XML parsers: use expat instead of xmlproc. Should be faster.
-  Removed my UnicodeString object: I now require Python 2.0 or up,
   which has unicode support built in.
-  Removed assert in glyf table: redundant data at the end of the table
   is now ignored instead of raising an error. Should become a warning.
-  Fixed bug in hmtx/vmtx code that only occured if all advances were
   equal.
-  Fixed subtle bug in TT instruction disassembler.
-  Couple of fixes to the 'post' table.
-  Updated OS/2 table to latest spec.

1.0b1 (released 2001-08-10)
---------------------------

-  Reorganized the command line interface for ttDump.py and
   ttCompile.py, they now behave more like "normal" command line tool,
   in that they accept multiple input files for batch processing.
-  ttDump.py and ttCompile.py don't silently override files anymore, but
   ask before doing so. Can be overridden by -f.
-  Added -d option to both ttDump.py and ttCompile.py.
-  Installation is now done with distutils. (Needs work for environments
   without compilers.)
-  Updated installation instructions.
-  Added some workarounds so as to handle certain buggy fonts more
   gracefully.
-  Updated Unicode table to Unicode 3.0 (Thanks Antoine!)
-  Included a Python script by Adam Twardoch that adds some useful stuff
   to the Windows registry.
-  Moved the project to SourceForge.

1.0a6 (released 2000-03-15)
---------------------------

-  Big reorganization: made ttLib a subpackage of the new fontTools
   package, changed several module names. Called the entire suite
   "FontTools"
-  Added several submodules to fontTools, some new, some older.
-  Added experimental CFF/GPOS/GSUB support to ttLib, read-only (but XML
   dumping of GPOS/GSUB is for now disabled)
-  Fixed hdmx endian bug
-  Added -b option to ttCompile.py, it disables recalculation of
   bounding boxes, as requested by Werner Lemberg.
-  Renamed tt2xml.pt to ttDump.py and xml2tt.py to ttCompile.py
-  Use ".ttx" as file extension instead of ".xml".
-  TTX is now the name of the XML-based *format* for TT fonts, and not
   just an application.

1.0a5
-----

Never released

-  More tables supported: hdmx, vhea, vmtx

1.0a3 & 1.0a4
-------------

Never released

-  fixed most portability issues
-  retracted the "Euro_or_currency" change from 1.0a2: it was
   nonsense!

1.0a2 (released 1999-05-02)
---------------------------

-  binary release for MacOS
-  genenates full FOND resources: including width table, PS font name
   info and kern table if applicable.
-  added cmap format 4 support. Extra: dumps Unicode char names as XML
   comments!
-  added cmap format 6 support
-  now accepts true type files starting with "true" (instead of just
   0x00010000 and "OTTO")
-  'glyf' table support is now complete: I added support for composite
   scale, xy-scale and two-by-two for the 'glyf' table. For now,
   component offset scale behaviour defaults to Apple-style. This only
   affects the (re)calculation of the glyph bounding box.
-  changed "Euro" to "Euro_or_currency" in the Standard Apple Glyph
   order list, since we cannot tell from the 'post' table which is
   meant. I should probably doublecheck with a Unicode encoding if
   available. (This does not affect the output!)

Fixed bugs: - 'hhea' table is now recalculated correctly - fixed wrong
assumption about sfnt resource names

1.0a1 (released 1999-04-27)
---------------------------

-  initial binary release for MacOS
