4.16.1 (released 2020-10-05)
----------------------------

- [varLib.instancer] Fixed ``TypeError`` exception when instantiating a VF with
  a GSUB table 1.1 in which ``FeatureVariations`` attribute is present but set to
  ``None`` -- indicating that optional ``FeatureVariations`` is missing (#2077).
- [glifLib] Make ``x`` and ``y`` attributes of the ``point`` element required
  even when validation is turned off, and raise a meaningful ``GlifLibError``
  message when that happens (#2075).

4.16.0 (released 2020-09-30)
----------------------------

- [removeOverlaps] Added new module and ``removeOverlaps`` function that merges
  overlapping contours and components in TrueType glyphs. It requires the
  `skia-pathops <https://github.com/fonttools/skia-pathops>`__ module.
  Note that removing overlaps invalidates the TrueType hinting (#2068).
- [varLib.instancer] Added ``--remove-overlaps`` command-line option.
  The ``overlap`` option in ``instantiateVariableFont`` now takes an ``OverlapMode``
  enum: 0: KEEP_AND_DONT_SET_FLAGS, 1: KEEP_AND_SET_FLAGS (default), and 2: REMOVE.
  The latter is equivalent to calling ``removeOverlaps`` on the generated static
  instance. The option continues to accept ``bool`` value for backward compatibility.


4.15.0 (released 2020-09-21)
----------------------------

- [plistlib] Added typing annotations to plistlib module. Set up mypy static
  typechecker to run automatically on CI (#2061).
- [ttLib] Implement private ``Debg`` table, a reverse-DNS namespaced JSON dict.
- [feaLib] Optionally add an entry into the ``Debg`` table with the original
  lookup name (if any), feature name / script / language combination (if any),
  and original source filename and line location. Annotate the ttx output for
  a lookup with the information from the Debg table (#2052).
- [sfnt] Disabled checksum checking by default in ``SFNTReader`` (#2058).
- [Docs] Document ``mtiLib`` module (#2027).
- [varLib.interpolatable] Added checks for contour node count and operation type
  of each node (#2054).
- [ttLib] Added API to register custom table packer/unpacker classes (#2055).

4.14.0 (released 2020-08-19)
----------------------------

- [feaLib] Allow anonymous classes in LookupFlags definitions (#2037).
- [Docs] Better document DesignSpace rules processing order (#2041).
- [ttLib] Fixed 21-year old bug in ``maxp.maxComponentDepth`` calculation (#2044,
  #2045).
- [varLib.models] Fixed misspelled argument name in CLI entry point (81d0042a).
- [subset] When subsetting GSUB v1.1, fixed TypeError by checking whether the
  optional FeatureVariations table is present (e63ecc5b).
- [Snippets] Added snippet to show how to decompose glyphs in a TTF (#2030).
- [otlLib] Generate GSUB type 5 and GPOS type 7 contextual lookups where appropriate
  (#2016).

4.13.0 (released 2020-07-10)
----------------------------

- [feaLib/otlLib] Moved lookup subtable builders from feaLib to otlLib; refactored
  some common code (#2004, #2007).
- [docs] Document otlLib module (#2009).
- [glifLib] Fixed bug with some UFO .glif filenames clashing on case-insensitive
  filesystems (#2001, #2002).
- [colorLib] Updated COLRv1 implementation following changes in the draft spec:
  (#2008, googlefonts/colr-gradients-spec#24).

4.12.1 (released 2020-06-16)
----------------------------

- [_n_a_m_e] Fixed error in ``addMultilingualName`` with one-character names.
  Only attempt to recovered malformed UTF-16 data from a ``bytes`` string,
  not from unicode ``str`` (#1997, #1998).

4.12.0 (released 2020-06-09)
----------------------------

- [otlLib/varLib] Ensure that the ``AxisNameID`` in the ``STAT`` and ``fvar``
  tables is grater than 255 as per OpenType spec (#1985, #1986).
- [docs] Document more modules in ``fontTools.misc`` package: ``filenames``,
  ``fixedTools``, ``intTools``, ``loggingTools``, ``macCreatorType``, ``macRes``,
  ``plistlib`` (#1981).
- [OS/2] Don't calculate whole sets of unicode codepoints, use faster and more memory
  efficient ranges and bisect lookups (#1984).
- [voltLib] Support writing back abstract syntax tree as VOLT data (#1983).
- [voltLib] Accept DO_NOT_TOUCH_CMAP keyword (#1987).
- [subset/merge] Fixed a namespace clash involving a private helper class (#1955).

4.11.0 (released 2020-05-28)
----------------------------

- [feaLib] Introduced ``includeDir`` parameter on Parser and IncludingLexer to
  explicitly specify the directory to search when ``include()`` statements are
  encountered (#1973).
- [ufoLib] Silently delete duplicate glyphs within the same kerning group when reading
  groups (#1970).
- [ttLib] Set version of COLR table when decompiling COLRv1 (commit 9d8a7e2).

4.10.2 (released 2020-05-20)
----------------------------

- [sfnt] Fixed ``NameError: SimpleNamespace`` while reading TTC header. The regression
  was introduced with 4.10.1 after removing ``py23`` star import.

4.10.1 (released 2020-05-19)
----------------------------

- [sfnt] Make ``SFNTReader`` pickleable even when TTFont is loaded with lazy=True
  option and thus keeps a reference to an external file (#1962, #1967).
- [feaLib.ast] Restore backward compatibility (broken in 4.10 with #1905) for
  ``ChainContextPosStatement`` and ``ChainContextSubstStatement`` classes.
  Make them accept either list of lookups or list of lists of lookups (#1961).
- [docs] Document some modules in ``fontTools.misc`` package: ``arrayTools``,
  ``bezierTools`` ``cliTools`` and ``eexec`` (#1956).
- [ttLib._n_a_m_e] Fixed ``findMultilingualName()`` when name record's ``string`` is
  encoded as bytes sequence (#1963).

4.10.0 (released 2020-05-15)
----------------------------

- [varLib] Allow feature variations to be active across the entire space (#1957).
- [ufoLib] Added support for ``formatVersionMinor`` in UFO's ``fontinfo.plist`` and for
  ``formatMinor`` attribute in GLIF file as discussed in unified-font-object/ufo-spec#78.
  No changes in reading or writing UFOs until an upcoming (non-0) minor update of the
  UFO specification is published (#1786).
- [merge] Fixed merging fonts with different versions of ``OS/2`` table (#1865, #1952).
- [subset] Fixed ``AttributeError`` while subsetting ``ContextSubst`` and ``ContextPos``
  Format 3 subtable (#1879, #1944).
- [ttLib.table._m_e_t_a] if data happens to be ascii, emit comment in TTX (#1938).
- [feaLib] Support multiple lookups per glyph position (#1905).
- [psCharStrings] Use inheritance to avoid repeated code in initializer (#1932).
- [Doc] Improved documentation for the following modules: ``afmLib`` (#1933), ``agl``
  (#1934), ``cffLib`` (#1935), ``cu2qu`` (#1937), ``encodings`` (#1940), ``feaLib``
  (#1941), ``merge`` (#1949).
- [Doc] Split off developer-centric info to new page, making front page of docs more
  user-focused. List all utilities and sub-modules with brief descriptions.
  Make README more concise and focused (#1914).
- [otlLib] Add function to build STAT table from high-level description (#1926).
- [ttLib._n_a_m_e] Add ``findMultilingualName()`` method (#1921).
- [unicodedata] Update ``RTL_SCRIPTS`` for Unicode 13.0 (#1925).
- [gvar] Sort ``gvar`` XML output by glyph name, not glyph order (#1907, #1908).
- [Doc] Added help options to ``fonttools`` command line tool (#1913, #1920).
  Ensure all fonttools CLI tools have help documentation (#1948).
- [ufoLib] Only write fontinfo.plist when there actually is content (#1911).

4.9.0 (released 2020-04-29)
---------------------------

- [subset] Fixed subsetting of FeatureVariations table. The subsetter no longer drops
  FeatureVariationRecords that have empty substitutions as that will keep the search
  going and thus change the logic. It will only drop empty records that occur at the
  end of the FeatureVariationRecords array (#1881).
- [subset] Remove FeatureVariations table and downgrade GSUB/GPOS to version 0x10000
  when FeatureVariations contain no FeatureVariationRecords after subsetting (#1903).
- [agl] Add support for legacy Adobe Glyph List of glyph names in ``fontTools.agl``
  (#1895).
- [feaLib] Ignore superfluous script statements (#1883).
- [feaLib] Hide traceback by default on ``fonttools feaLib`` command line.
  Use ``--traceback`` option to show (#1898).
- [feaLib] Check lookup index in chaining sub/pos lookups and print better error
  message (#1896, #1897).
- [feaLib] Fix building chained alt substitutions (#1902).
- [Doc] Included all fontTools modules in the sphinx-generated documentation, and
  published it to ReadTheDocs for continuous documentation of the fontTools project
  (#1333). Check it out at https://fonttools.readthedocs.io/. Thanks to Chris Simpkins!
- [transform] The ``Transform`` class is now subclass of ``typing.NamedTuple``. No
  change in functionality (#1904).


4.8.1 (released 2020-04-17)
---------------------------

- [feaLib] Fixed ``AttributeError: 'NoneType' has no attribute 'getAlternateGlyphs'``
  when ``aalt`` feature references a chain contextual substitution lookup
  (googlefonts/fontmake#648, #1878).

4.8.0 (released 2020-04-16)
---------------------------

- [feaLib] If Parser is initialized without a ``glyphNames`` parameter, it cannot
  distinguish between a glyph name containing an hyphen, or a range of glyph names;
  instead of raising an error, it now interprets them as literal glyph names, while
  also outputting a logging warning to alert user about the ambiguity (#1768, #1870).
- [feaLib] When serializing AST to string, emit spaces around hyphens that denote
  ranges. Also, fixed an issue with CID ranges when round-tripping AST->string->AST
  (#1872).
- [Snippets/otf2ttf] In otf2ttf.py script update LSB in hmtx to match xMin (#1873).
- [colorLib] Added experimental support for building ``COLR`` v1 tables as per
  the `colr-gradients-spec <https://github.com/googlefonts/colr-gradients-spec/blob/master/colr-gradients-spec.md>`__
  draft proposal. **NOTE**: both the API and the XML dump of ``COLR`` v1 are
  susceptible to change while the proposal is being discussed and formalized (#1822).

4.7.0 (released 2020-04-03)
---------------------------

- [cu2qu] Added ``fontTools.cu2qu`` package, imported from the original
  `cu2qu <https://github.com/googlefonts/cu2qu>`__ project. The ``cu2qu.pens`` module
  was moved to ``fontTools.pens.cu2quPen``. The optional cu2qu extension module
  can be compiled by installing `Cython <https://cython.org/>`__ before installing
  fonttools from source (i.e. git repo or sdist tarball). The wheel package that
  is published on PyPI (i.e. the one ``pip`` downloads, unless ``--no-binary``
  option is used), will continue to be pure-Python for now (#1868).

4.6.0 (released 2020-03-24)
---------------------------

- [varLib] Added support for building variable ``BASE`` table version 1.1 (#1858).
- [CPAL] Added ``fromRGBA`` method to ``Color`` class (#1861).


4.5.0 (released 2020-03-20)
---------------------------

- [designspaceLib] Added ``add{Axis,Source,Instance,Rule}Descriptor`` methods to
  ``DesignSpaceDocument`` class, to initialize new descriptor objects using keyword
  arguments, and at the same time append them to the current document (#1860).
- [unicodedata] Update to Unicode 13.0 (#1859).

4.4.3 (released 2020-03-13)
---------------------------

- [varLib] Always build ``gvar`` table for TrueType-flavored Variable Fonts,
  even if it contains no variation data. The table is required according to
  the OpenType spec (#1855, #1857).

4.4.2 (released 2020-03-12)
---------------------------

- [ttx] Annotate ``LookupFlag`` in XML dump with comment explaining what bits
  are set and what they mean (#1850).
- [feaLib] Added more descriptive message to ``IncludedFeaNotFound`` error (#1842).

4.4.1 (released 2020-02-26)
---------------------------

- [woff2] Skip normalizing ``glyf`` and ``loca`` tables if these are missing from
  a font (e.g. in NotoColorEmoji using ``CBDT/CBLC`` tables).
- [timeTools] Use non-localized date parsing in ``timestampFromString``, to fix
  error when non-English ``LC_TIME`` locale is set (#1838, #1839).
- [fontBuilder] Make sure the CFF table generated by fontBuilder can be used by varLib
  without having to compile and decompile the table first. This was breaking in
  converting the CFF table to CFF2 due to some unset attributes (#1836).

4.4.0 (released 2020-02-18)
---------------------------

- [colorLib] Added ``fontTools.colorLib.builder`` module, initially with ``buildCOLR``
  and ``buildCPAL`` public functions. More color font formats will follow (#1827).
- [fontBuilder] Added ``setupCOLR`` and ``setupCPAL`` methods (#1826).
- [ttGlyphPen] Quantize ``GlyphComponent.transform`` floats to ``F2Dot14`` to fix
  round-trip issue when computing bounding boxes of transformed components (#1830).
- [glyf] If a component uses reference points (``firstPt`` and ``secondPt``) for
  alignment (instead of X and Y offsets), compute the effective translation offset
  *after* having applied any transform (#1831).
- [glyf] When all glyphs have zero contours, compile ``glyf`` table data as a single
  null byte in order to pass validation by OTS and Windows (#1829).
- [feaLib] Parsing feature code now ensures that referenced glyph names are part of
  the known glyph set, unless a glyph set was not provided.
- [varLib] When filling in the default axis value for a missing location of a source or
  instance, correctly map the value forward.
- [varLib] The avar table can now contain mapping output values that are greater than
  OR EQUAL to the preceeding value, as the avar specification allows this.
- [varLib] The errors of the module are now ordered hierarchically below VarLibError. 
  See #1821.

4.3.0 (released 2020-02-03)
---------------------------

- [EBLC/CBLC] Fixed incorrect padding length calculation for Format 3 IndexSubTable
  (#1817, #1818).
- [varLib] Fixed error when merging OTL tables and TTFonts were loaded as ``lazy=True``
  (#1808, #1809).
- [varLib] Allow to use master fonts containing ``CFF2`` table when building VF (#1816).
- [ttLib] Make ``recalcBBoxes`` option work also with ``CFF2`` table (#1816).
- [feaLib] Don't reset ``lookupflag`` in lookups defined inside feature blocks.
  They will now inherit the current ``lookupflag`` of the feature. This is what
  Adobe ``makeotf`` also does in this case (#1815).
- [feaLib] Fixed bug with mixed single/multiple substitutions. If a single substitution
  involved a glyph class, we were incorrectly using only the first glyph in the class
  (#1814).

4.2.5 (released 2020-01-29)
---------------------------

- [feaLib] Do not fail on duplicate multiple substitutions, only warn (#1811).
- [subset] Optimize SinglePos subtables to Format 1 if all ValueRecords are the same
  (#1802).

4.2.4 (released 2020-01-09)
---------------------------

- [unicodedata] Update RTL_SCRIPTS for Unicode 11 and 12.

4.2.3 (released 2020-01-07)
---------------------------

- [otTables] Fixed bug when splitting `MarkBasePos` subtables as offsets overflow.
  The mark class values in the split subtable were not being updated, leading to
  invalid mark-base attachments (#1797, googlefonts/noto-source#145).
- [feaLib] Only log a warning instead of error when features contain duplicate
  substitutions (#1767).
- [glifLib] Strip XML comments when parsing with lxml (#1784, #1785).

4.2.2 (released 2019-12-12)
---------------------------

- [subset] Fixed issue with subsetting FeatureVariations table when the index
  of features changes as features get dropped. The feature index need to be
  remapped to point to index of the remaining features (#1777, #1782).
- [fontBuilder] Added `addFeatureVariations` method to `FontBuilder` class. This
  is a shorthand for calling `featureVars.addFeatureVariations` on the builder's
  TTFont object (#1781).
- [glyf] Fixed the flags bug in glyph.drawPoints() like we did for glyph.draw()
  (#1771, #1774).

4.2.1 (released 2019-12-06)
---------------------------

- [glyf] Use the ``flagOnCurve`` bit mask in ``glyph.draw()``, so that we ignore
  the ``overlap`` flag that may be set when instantiating variable fonts (#1771).

4.2.0 (released 2019-11-28)
---------------------------

- [pens] Added the following pens:

  * ``roundingPen.RoundingPen``: filter pen that rounds coordinates and components'
    offsets to integer;
  * ``roundingPen.RoundingPointPen``: like the above, but using PointPen protocol.
  * ``filterPen.FilterPointPen``: base class for filter point pens;
  * ``transformPen.TransformPointPen``: filter point pen to apply affine transform;
  * ``recordingPen.RecordingPointPen``: records and replays point-pen commands.

- [ttGlyphPen] Always round float coordinates and component offsets to integers
  (#1763).
- [ufoLib] When converting kerning groups from UFO2 to UFO3, avoid confusing
  groups with the same name as one of the glyphs (#1761, #1762,
  unified-font-object/ufo-spec#98).

4.1.0 (released 2019-11-18)
---------------------------

- [instancer] Implemented restricting axis ranges (level 3 partial instancing).
  You can now pass ``{axis_tag: (min, max)}`` tuples as input to the
  ``instantiateVariableFont`` function. Note that changing the default axis
  position is not supported yet. The command-line script also accepts axis ranges
  in the form of colon-separated float values, e.g. ``wght=400:700`` (#1753, #1537).
- [instancer] Never drop STAT ``DesignAxis`` records, but only prune out-of-range
  ``AxisValue`` records.
- [otBase/otTables] Enforce that VarStore.RegionAxisCount == fvar.axisCount, even
  when regions list is empty to appease OTS < v8.0 (#1752).
- [designspaceLib] Defined new ``processing`` attribute for ``<rules>`` element,
  with values "first" or "last", plus other editorial changes to DesignSpace
  specification. Bumped format version to 4.1 (#1750).
- [varLib] Improved error message when masters' glyph orders do not match (#1758,
  #1759).
- [featureVars] Allow to specify custom feature tag in ``addFeatureVariations``;
  allow said feature to already exist, in which case we append new lookup indices
  to existing features. Implemented ``<rules>`` attribute ``processing`` according to
  DesignSpace specification update in #1750. Depending on this flag, we generate
  either an 'rvrn' (always processed first) or a 'rclt' feature (follows lookup order,
  therefore last) (#1747, #1625, #1371).
- [ttCollection] Added support for context manager auto-closing via ``with`` statement
  like with ``TTFont`` (#1751).
- [unicodedata] Require unicodedata2 >= 12.1.0.
- [py2.py3] Removed yet more PY2 vestiges (#1743).
- [_n_a_m_e] Fixed issue when comparing NameRecords with different string types (#1742).
- [fixedTools] Changed ``fixedToFloat`` to not do any rounding but simply return
  ``value / (1 << precisionBits)``. Added ``floatToFixedToStr`` and
  ``strToFixedToFloat`` functions to be used when loading from or dumping to XML.
  Fixed values (e.g. fvar axes and instance coordinates, avar mappings, etc.) are
  are now stored as un-rounded decimal floats upon decompiling (#1740, #737).
- [feaLib] Fixed handling of multiple ``LigatureCaret`` statements for the same glyph.
  Only the first rule per glyph is used, additional ones are ignored (#1733).

4.0.2 (released 2019-09-26)
---------------------------

- [voltLib] Added support for ``ALL`` and ``NONE`` in ``PROCESS_MARKS`` (#1732).
- [Silf] Fixed issue in ``Silf`` table compilation and decompilation regarding str vs
  bytes in python3 (#1728).
- [merge] Handle duplicate glyph names better: instead of appending font index to
  all glyph names, use similar code like we use in ``post`` and ``CFF`` tables (#1729).

4.0.1 (released 2019-09-11)
---------------------------

- [otTables] Support fixing offset overflows in ``MultipleSubst`` lookup subtables
  (#1706).
- [subset] Prune empty strikes in ``EBDT`` and ``CBDT`` table data (#1698, #1633).
- [pens] Fixed issue in ``PointToSegmentPen`` when last point of closed contour has
  same coordinates as the starting point and was incorrectly dropped (#1720).
- [Graphite] Fixed ``Sill`` table output to pass OTS (#1705).
- [name] Added ``removeNames`` method to ``table__n_a_m_e`` class (#1719).
- [ttLib] Added aliases for renamed entries ``ascender`` and ``descender`` in
  ``hhea`` table (#1715).

4.0.0 (released 2019-08-22)
---------------------------

- NOTE: The v4.x version series only supports Python 3.6 or greater. You can keep
  using fonttools 3.x if you need support for Python 2.
- [py23] Removed all the python2-only code since it is no longer reachable, thus
  unused; only the Python3 symbols were kept, but these are no-op. The module is now
  DEPRECATED and will removed in the future.
- [ttLib] Fixed UnboundLocalError for empty loca/glyph tables (#1680). Also, allow
  the glyf table to be incomplete when dumping to XML (#1681).
- [varLib.models] Fixed KeyError while sorting masters and there are no on-axis for
  a given axis (38a8eb0e).
- [cffLib] Make sure glyph names are unique (#1699).
- [feaLib] Fix feature parser to correctly handle octal numbers (#1700).

3.44.0 (released 2019-08-02)
----------------------------

- NOTE: This is the last scheduled release to support Python 2.7. The upcoming fonttools
  v4.x series is going to require Python 3.6 or greater.
- [varLib] Added new ``varLib.instancer`` module for partially instantiating variable
  fonts. This extends (and will eventually replace) ``varLib.mutator`` module, as
  it allows to create not just full static instances from a variable font, but also
  "partial" or "less variable" fonts where some of the axes are dropped or
  instantiated at a particular value.
  Also available from the command-line as `fonttools varLib.instancer --help`
  (#1537, #1628).
- [cffLib] Added support for ``FDSelect`` format 4 (#1677).
- [subset] Added support for subsetting ``sbix`` (Apple bitmap color font) table.
- [t1Lib] Fixed issue parsing ``eexec`` section in Type1 fonts when whitespace
  characters are interspersed among the trailing zeros (#1676).
- [cffLib.specializer] Fixed bug in ``programToCommands`` with CFF2 charstrings (#1669).

3.43.2 (released 2019-07-10)
----------------------------

- [featureVars] Fixed region-merging code on python3 (#1659).
- [varLib.cff] Fixed merging of sparse PrivateDict items (#1653).

3.43.1 (released 2019-06-19)
----------------------------

- [subset] Fixed regression when passing ``--flavor=woff2`` option with an input font
  that was already compressed as WOFF 1.0 (#1650).

3.43.0 (released 2019-06-18)
----------------------------

- [woff2] Added support for compressing/decompressing WOFF2 fonts with non-transformed
  ``glyf`` and ``loca`` tables, as well as with transformed ``hmtx`` table.
  Removed ``Snippets/woff2_compress.py`` and ``Snippets/woff2_decompress.py`` scripts,
  and replaced them with a new console entry point ``fonttools ttLib.woff2``
  that provides two sub-commands ``compress`` and ``decompress``.
- [varLib.cff] Fixed bug when merging CFF2 ``PrivateDicts``. The ``PrivateDict``
  data from the first region font was incorrecty used for all subsequent fonts.
  The bug would only affect variable CFF2 fonts with hinting (#1643, #1644).
  Also, fixed a merging bug when VF masters have no blends or marking glyphs (#1632,
  #1642).
- [loggingTools] Removed unused backport of ``LastResortLogger`` class.
- [subset] Gracefully handle partial MATH table (#1635).
- [featureVars] Avoid duplicate references to ``rvrn`` feature record in
  ``DefaultLangSys`` tables when calling ``addFeatureVariations`` on a font that
  does not already have a ``GSUB`` table (aa8a5bc6).
- [varLib] Fixed merging of class-based kerning. Before, the process could introduce
  rogue kerning values and variations for random classes against class zero (everything
  not otherwise classed).
- [varLib] Fixed merging GPOS tables from master fonts with different number of
  ``SinglePos`` subtables (#1621, #1641).
- [unicodedata] Updated Blocks, Scripts and ScriptExtensions to Unicode 12.1.

3.42.0 (released 2019-05-28)
----------------------------

- [OS/2] Fixed sign of ``fsType``: it should be ``uint16``, not ``int16`` (#1619).
- [subset] Skip out-of-range class values in mark attachment (#1478).
- [fontBuilder] Add an empty ``DSIG`` table with ``setupDummyDSIG`` method (#1621).
- [varLib.merger] Fixed bug whereby ``GDEF.GlyphClassDef`` were being dropped
  when generating instance via ``varLib.mutator`` (#1614).
- [varLib] Added command-line options ``-v`` and ``-q`` to configure logging (#1613).
- [subset] Update font extents in head table (#1612).
- [subset] Make --retain-gids truncate empty glyphs after the last non-empty glyph
  (#1611).
- [requirements] Updated ``unicodedata2`` backport for Unicode 12.0.

3.41.2 (released 2019-05-13)
----------------------------

- [cffLib] Fixed issue when importing a ``CFF2`` variable font from XML, whereby
  the VarStore state was not propagated to PrivateDict (#1598).
- [varLib] Don't drop ``post`` glyph names when building CFF2 variable font (#1609).


3.41.1 (released 2019-05-13)
----------------------------

- [designspaceLib] Added ``loadSourceFonts`` method to load source fonts using
  custom opener function (#1606).
- [head] Round font bounding box coordinates to integers to fix compile error
  if CFF font has float coordinates (#1604, #1605).
- [feaLib] Don't write ``None`` in ``ast.ValueRecord.asFea()`` (#1599).
- [subset] Fixed issue ``AssertionError`` when using ``--desubroutinize`` option
  (#1590, #1594).
- [graphite] Fixed bug in ``Silf`` table's ``decompile`` method unmasked by
  previous typo fix (#1597). Decode languange code as UTF-8 in ``Sill`` table's
  ``decompile`` method (#1600).

3.41.0 (released 2019-04-29)
----------------------------

- [varLib/cffLib] Added support for building ``CFF2`` variable font from sparse
  masters, or masters with more than one model (multiple ``VarStore.VarData``).
  In ``cffLib.specializer``, added support for ``CFF2`` CharStrings with
  ``blend`` operators (#1547, #1591).
- [subset] Fixed subsetting ``HVAR`` and ``VVAR`` with ``--retain-gids`` option,
  and when advances mapping is null while sidebearings mappings are non-null
  (#1587, #1588).
- Added ``otlLib.maxContextCalc`` module to compute ``OS/2.usMaxContext`` value.
  Calculate it automatically when compiling features with feaLib. Added option
  ``--recalc-max-context`` to ``subset`` module (#1582).
- [otBase/otTables] Fixed ``AttributeError`` on missing OT table fields after
  importing font from TTX (#1584).
- [graphite] Fixed typo ``Silf`` table's ``decompile`` method (#1586).
- [otlLib] Better compress ``GPOS`` SinglePos (LookupType 1) subtables (#1539).

3.40.0 (released 2019-04-08)
----------------------------

- [subset] Fixed error while subsetting ``VVAR`` with ``--retain-gids``
  option (#1552).
- [designspaceLib] Use up-to-date default location in ``findDefault`` method
  (#1554).
- [voltLib] Allow passing file-like object to Parser.
- [arrayTools/glyf] ``calcIntBounds`` (used to compute bounding boxes of glyf
  table's glyphs) now uses ``otRound`` instead of ``round3`` (#1566).
- [svgLib] Added support for converting more SVG shapes to path ``d`` strings
  (ellipse, line, polyline), as well as support for ``transform`` attributes.
  Only ``matrix`` transformations are currently supported (#1564, #1564).
- [varLib] Added support for building ``VVAR`` table from ``vmtx`` and ``VORG``
  tables (#1551).
- [fontBuilder] Enable making CFF2 fonts with ``post`` table format 2 (#1557).
- Fixed ``DeprecationWarning`` on invalid escape sequences (#1562).

3.39.0 (released 2019-03-19)
----------------------------

- [ttLib/glyf] Raise more specific error when encountering recursive
  component references (#1545, #1546).
- [Doc/designspaceLib] Defined new ``public.skipExportGlyphs`` lib key (#1534,
  unified-font-object/ufo-spec#84).
- [varLib] Use ``vmtx`` to compute vertical phantom points; or ``hhea.ascent``
  and ``head.unitsPerEM`` if ``vmtx`` is missing (#1528).
- [gvar/cvar] Sort XML element's min/value/max attributes in TupleVariation
  toXML to improve readability of TTX dump (#1527).
- [varLib.plot] Added support for 2D plots with only 1 variation axis (#1522).
- [designspaceLib] Use axes maps when normalizing locations in
  DesignSpaceDocument (#1226, #1521), and when finding default source (#1535).
- [mutator] Set ``OVERLAP_SIMPLE`` and ``OVERLAP_COMPOUND`` glyf flags by
  default in ``instantiateVariableFont``. Added ``--no-overlap`` cli option
  to disable this (#1518).
- [subset] Fixed subsetting ``VVAR`` table (#1516, #1517).  
  Fixed subsetting an ``HVAR`` table that has an ``AdvanceWidthMap`` when the
  option ``--retain-gids`` is used.
- [feaLib] Added ``forceChained`` in MultipleSubstStatement (#1511).  
  Fixed double indentation of ``subtable`` statement (#1512).  
  Added support for ``subtable`` statement in more places than just PairPos
  lookups (#1520).  
  Handle lookupflag 0 and lookupflag without a value (#1540).
- [varLib] In ``load_designspace``, provide a default English name for the
  ``ital`` axis tag.
- Remove pyftinspect because it is unmaintained and bitrotted.

3.38.0 (released 2019-02-18)
----------------------------

- [cffLib] Fixed RecursionError when unpickling or deepcopying TTFont with
  CFF table (#1488, 649dc49).
- [subset] Fixed AttributeError when using --desubroutinize option (#1490).
  Also, fixed desubroutinizing bug when subrs contain hints (#1499).
- [CPAL] Make Color a subclass of namedtuple (173a0f5).
- [feaLib] Allow hyphen in glyph class names.
- [feaLib] Added 'tables' option to __main__.py (#1497).
- [feaLib] Add support for special-case contextual positioning formatting
  (#1501).
- [svgLib] Support converting SVG basic shapes (rect, circle, etc.) into
  equivalent SVG paths (#1500, #1508).
- [Snippets] Added name-viewer.ipynb Jupyter notebook.


3.37.3 (released 2019-02-05)
----------------------------

- The previous release accidentally changed several files from Unix to DOS
  line-endings. Fix that.

3.37.2 (released 2019-02-05)
----------------------------

- [varLib] Temporarily revert the fix to ``load_masters()``, which caused a
  crash in ``interpolate_layout()`` when ``deepcopy``-ing OTFs.

3.37.1 (released 2019-02-05)
----------------------------

- [varLib] ``load_masters()`` now actually assigns the fonts it loads to the
  source.font attributes.
- [varLib] Fixed an MVAR table generation crash when sparse masters were
  involved.
- [voltLib] ``parse_coverage_()`` returns a tuple instead of an ast.Enum.
- [feaLib] A MarkClassDefinition inside a block is no longer doubly indented
  compared to the rest of the block.

3.37.0 (released 2019-01-28)
----------------------------

- [svgLib] Added support for converting elliptical arcs to cubic bezier curves
  (#1464).
- [py23] Added backport for ``math.isfinite``.
- [varLib] Apply HIDDEN flag to fvar axis if designspace axis has attribute
  ``hidden=1``.
- Fixed "DeprecationWarning: invalid escape sequence" in Python 3.7.
- [voltLib] Fixed parsing glyph groups. Distinguish different PROCESS_MARKS.
  Accept COMPONENT glyph type.
- [feaLib] Distinguish missing value and explicit ``<NULL>`` for PairPos2
  format A (#1459). Round-trip ``useExtension`` keyword. Implemented
  ``ValueRecord.asFea`` method.
- [subset] Insert empty widths into hdmx when retaining gids (#1458).

3.36.0 (released 2019-01-17)
----------------------------

- [ttx] Added ``--no-recalc-timestamp`` option to keep the original font's
  ``head.modified`` timestamp (#1455, #46).
- [ttx/psCharStrings] Fixed issues while dumping and round-tripping CFF2 table
  with ttx (#1451, #1452, #1456).
- [voltLib] Fixed check for duplicate anchors (#1450). Don't try to read past
  the ``END`` operator in .vtp file (#1453).
- [varLib] Use sentinel value -0x8000 (-32768) to ignore post.underlineThickness
  and post.underlinePosition when generating MVAR deltas (#1449,
  googlei18n/ufo2ft#308).
- [subset] Added ``--retain-gids`` option to subset font without modifying the
  current glyph indices (#1443, #1447).
- [ufoLib] Replace deprecated calls to ``getbytes`` and ``setbytes`` with new
  equivalent ``readbytes`` and ``writebytes`` calls. ``fs`` >= 2.2 no required.
- [varLib] Allow loading masters from TTX files as well (#1441).

3.35.2 (released 2019-01-14)
----------------------------

- [hmtx/vmtx]: Allow to compile/decompile ``hmtx`` and ``vmtx`` tables even
  without the corresponding (required) metrics header tables, ``hhea`` and
  ``vhea`` (#1439).
- [varLib] Added support for localized axes' ``labelname`` and named instances'
  ``stylename`` (#1438).

3.35.1 (released 2019-01-09)
----------------------------

- [_m_a_x_p] Include ``maxComponentElements`` in ``maxp`` table's recalculation.

3.35.0 (released 2019-01-07)
----------------------------

- [psCharStrings] In ``encodeFloat`` function, use float's "general format" with
  8 digits of precision (i.e. ``%8g``) instead of ``str()``. This works around
  a macOS rendering issue when real numbers in CFF table are too long, and
  also makes sure that floats are encoded with the same precision in python 2.7
  and 3.x (#1430, googlei18n/ufo2ft#306).
- [_n_a_m_e/fontBuilder] Make ``_n_a_m_e_table.addMultilingualName`` also add
  Macintosh (platformID=1) names by default. Added options to ``FontBuilder``
  ``setupNameTable`` method to optionally disable Macintosh or Windows names.
  (#1359, #1431).
- [varLib] Make ``build`` optionally accept a ``DesignSpaceDocument`` object,
  instead of a designspace file path. The caller can now set the ``font``
  attribute of designspace's sources to a TTFont object, thus allowing to
  skip filenames manipulation altogether (#1416, #1425).
- [sfnt] Allow SFNTReader objects to be deep-copied.
- Require typing>=3.6.4 on py27 to fix issue with singledispatch (#1423).
- [designspaceLib/t1Lib/macRes] Fixed some cases where pathlib.Path objects were
  not accepted (#1421).
- [varLib] Fixed merging of multiple PairPosFormat2 subtables (#1411).
- [varLib] The default STAT table version is now set to 1.1, to improve
  compatibility with legacy applications (#1413).

3.34.2 (released 2018-12-17)
----------------------------

- [merge] Fixed AssertionError when none of the script tables in GPOS/GSUB have
  a DefaultLangSys record (#1408, 135a4a1).

3.34.1 (released 2018-12-17)
----------------------------

- [varLib] Work around macOS rendering issue for composites without gvar entry (#1381).

3.34.0 (released 2018-12-14)
----------------------------

- [varLib] Support generation of CFF2 variable fonts. ``model.reorderMasters()``
  now supports arbitrary mapping. Fix handling of overlapping ranges for feature
  variations (#1400).
- [cffLib, subset] Code clean-up and fixing related to CFF2 support.
- [ttLib.tables.ttProgram] Use raw strings for regex patterns (#1389).
- [fontbuilder] Initial support for building CFF2 fonts. Set CFF's
  ``FontMatrix`` automatically from unitsPerEm.
- [plistLib] Accept the more general ``collections.Mapping`` instead of the
  specific ``dict`` class to support custom data classes that should serialize
  to dictionaries.

3.33.0 (released 2018-11-30)
----------------------------
- [subset] subsetter bug fix with variable fonts.
- [varLib.featureVar] Improve FeatureVariations generation with many rules.
- [varLib] Enable sparse masters when building variable fonts:
  https://github.com/fonttools/fonttools/pull/1368#issuecomment-437257368
- [varLib.mutator] Add IDEF for GETVARIATION opcode, for handling hints in an
  instance.
- [ttLib] Ignore the length of kern table subtable format 0

3.32.0 (released 2018-11-01)
----------------------------

- [ufoLib] Make ``UFOWriter`` a subclass of ``UFOReader``, and use mixins
  for shared methods (#1344).
- [featureVars] Fixed normalization error when a condition's minimum/maximum
  attributes are missing in designspace ``<rule>`` (#1366).
- [setup.py] Added ``[plot]`` to extras, to optionally install ``matplotlib``,
  needed to use the ``fonTools.varLib.plot`` module.
- [varLib] Take total bounding box into account when resolving model (7ee81c8).
  If multiple axes have the same range ratio, cut across both (62003f4).
- [subset] Don't error if ``STAT`` has no ``AxisValue`` tables.
- [fontBuilder] Added a new submodule which contains a ``FontBuilder`` wrapper
  class around ``TTFont`` that makes it easier to create a working TTF or OTF
  font from scratch with code. NOTE: the API is still experimental and may
  change in future versions.

3.31.0 (released 2018-10-21)
----------------------------

- [ufoLib] Merged the `ufoLib <https://github.com/unified-font-objects/ufoLib>`__
  master branch into a new ``fontTools.ufoLib`` package (#1335, #1095).
  Moved ``ufoLib.pointPen`` module to ``fontTools.pens.pointPen``.
  Moved ``ufoLib.etree`` module to ``fontTools.misc.etree``.
  Moved ``ufoLib.plistlib`` module to ``fontTools.misc.plistlib``.
  To use the new ``fontTools.ufoLib`` module you need to install fonttools
  with the ``[ufo]`` extra, or you can manually install the required additional
  dependencies (cf. README.rst).
- [morx] Support AAT action type to insert glyphs and clean up compilation
  of AAT action tables (4a1871f, 2011ccf).
- [subset] The ``--no-hinting`` on a CFF font now also drops the optional
  hinting keys in Private dict: ``ForceBold``, ``LanguageGroup``, and
  ``ExpansionFactor`` (#1322).
- [subset] Include nameIDs referenced by STAT table (#1327).
- [loggingTools] Added ``msg=None`` argument to
  ``CapturingLogHandler.assertRegex`` (0245f2c).
- [varLib.mutator] Implemented ``FeatureVariations`` instantiation (#1244).
- [g_l_y_f] Added PointPen support to ``_TTGlyph`` objects (#1334).

3.30.0 (released 2018-09-18)
----------------------------

- [feaLib] Skip building noop class PairPos subtables when Coverage is NULL
  (#1318).
- [ttx] Expose the previously reserved bit flag ``OVERLAP_SIMPLE`` of
  glyf table's contour points in the TTX dump. This is used in some
  implementations to specify a non-zero fill with overlapping contours (#1316).
- [ttLib] Added support for decompiling/compiling ``TS1C`` tables containing
  VTT sources for ``cvar`` variation table (#1310).
- [varLib] Use ``fontTools.designspaceLib`` to read DesignSpaceDocument. The
  ``fontTools.varLib.designspace`` module is now deprecated and will be removed
  in future versions. The presence of an explicit ``axes`` element is now
  required in order to build a variable font (#1224, #1313).
- [varLib] Implemented building GSUB FeatureVariations table from the ``rules``
  element of DesignSpace document (#1240, #713, #1314).
- [subset] Added ``--no-layout-closure`` option to not expand the subset with
  the glyphs produced by OpenType layout features. Instead, OpenType features
  will be subset to only rules that are relevant to the otherwise-specified
  glyph set (#43, #1121).

3.29.1 (released 2018-09-10)
----------------------------

- [feaLib] Fixed issue whereby lookups from DFLT/dflt were not included in the
  DFLT/non-dflt language systems (#1307).
- [graphite] Fixed issue on big-endian architectures (e.g. ppc64) (#1311).
- [subset] Added ``--layout-scripts`` option to add/exclude set of OpenType
  layout scripts that will be preserved. By default all scripts are retained
  (``'*'``) (#1303).

3.29.0 (released 2018-07-26)
----------------------------

- [feaLib] In the OTL table builder, when the ``name`` table is excluded
  from the list of tables to be build, skip compiling ``featureNames`` blocks,
  as the records referenced in ``FeatureParams`` table don't exist (68951b7).
- [otBase] Try ``ExtensionLookup`` if other offset-overflow methods fail
  (05f95f0).
- [feaLib] Added support for explicit ``subtable;`` break statements in
  PairPos lookups; previously these were ignored (#1279, #1300, #1302).
- [cffLib.specializer] Make sure the stack depth does not exceed maxstack - 1,
  so that a subroutinizer can insert subroutine calls (#1301,
  https://github.com/googlei18n/ufo2ft/issues/266).
- [otTables] Added support for fixing offset overflow errors occurring inside
  ``MarkBasePos`` subtables (#1297).
- [subset] Write the default output file extension based on ``--flavor`` option,
  or the value of ``TTFont.sfntVersion`` (d7ac0ad).
- [unicodedata] Updated Blocks, Scripts and ScriptExtensions for Unicode 11
  (452c85e).
- [xmlWriter] Added context manager to XMLWriter class to autoclose file
  descriptor on exit (#1290).
- [psCharStrings] Optimize the charstring's bytecode by encoding as integers
  all float values that have no decimal portion (8d7774a).
- [ttFont] Fixed missing import of ``TTLibError`` exception (#1285).
- [feaLib] Allow any languages other than ``dflt`` under ``DFLT`` script
  (#1278, #1292).

3.28.0 (released 2018-06-19)
----------------------------

- [featureVars] Added experimental module to build ``FeatureVariations``
  tables. Still needs to be hooked up to ``varLib.build`` (#1240).
- [fixedTools] Added ``otRound`` to round floats to nearest integer towards
  positive Infinity. This is now used where we deal with visual data like X/Y
  coordinates, advance widths/heights, variation deltas, and similar (#1274,
  #1248).
- [subset] Improved GSUB closure memoize algorithm.
- [varLib.models] Fixed regression in model resolution (180124, #1269).
- [feaLib.ast] Fixed error when converting ``SubtableStatement`` to string
  (#1275).
- [varLib.mutator] Set ``OS/2.usWeightClass`` and ``usWidthClass``, and
  ``post.italicAngle`` based on the 'wght', 'wdth' and 'slnt' axis values
  (#1276, #1264).
- [py23/loggingTools] Don't automatically set ``logging.lastResort`` handler
  on py27. Moved ``LastResortLogger`` to the ``loggingTools`` module (#1277).

3.27.1 (released 2018-06-11)
----------------------------

- [ttGlyphPen] Issue a warning and skip building non-existing components
  (https://github.com/googlei18n/fontmake/issues/411).
- [tests] Fixed issue running ttx_test.py from a tagged commit.

3.27.0 (released 2018-06-11)
----------------------------

- [designspaceLib] Added new ``conditionSet`` element to ``rule`` element in
  designspace document. Bumped ``format`` attribute to ``4.0`` (previously,
  it was formatted as an integer). Removed ``checkDefault``, ``checkAxes``
  methods, and any kind of guessing about the axes when the ``<axes>`` element
  is missing. The default master is expected at the intersection of all default
  values for each axis (#1254, #1255, #1267).
- [cffLib] Fixed issues when compiling CFF2 or converting from CFF when the
  font has an FDArray (#1211, #1271).
- [varLib] Avoid attempting to build ``cvar`` table when ``glyf`` table is not
  present, as is the case for CFF2 fonts.
- [subset] Handle None coverages in MarkGlyphSets; revert commit 02616ab that
  sets empty Coverage tables in MarkGlyphSets to None, to make OTS happy.
- [ttFont] Allow to build glyph order from ``maxp.numGlyphs`` when ``post`` or
  ``cmap`` are missing.
- [ttFont] Added ``__len__`` method to ``_TTGlyphSet``.
- [glyf] Ensure ``GlyphCoordinates`` never overflow signed shorts (#1230).
- [py23] Added alias for ``itertools.izip`` shadowing the built-in ``zip``.
- [loggingTools] Memoize ``log`` property of ``LogMixin`` class (fbab12).
- [ttx] Impoved test coverage (#1261).
- [Snippets] Addded script to append a suffix to all family names in a font.
- [varLib.plot] Make it work with matplotlib >= 2.1 (b38e2b).

3.26.0 (released 2018-05-03)
----------------------------

- [designspace] Added a new optional ``layer`` attribute to the source element,
  and a corresponding ``layerName`` attribute to the ``SourceDescriptor``
  object (#1253).
  Added ``conditionset`` element to the ``rule`` element to the spec, but not
  implemented in designspace reader/writer yet (#1254).
- [varLib.models] Refine modeling one last time (0ecf5c5).
- [otBase] Fixed sharing of tables referred to by different offset sizes
  (795f2f9).
- [subset] Don't drop a GDEF that only has VarStore (fc819d6). Set to None
  empty Coverage tables in MarkGlyphSets (02616ab).
- [varLib]: Added ``--master-finder`` command-line option (#1249).
- [varLib.mutator] Prune fvar nameIDs from instance's name table (#1245).
- [otTables] Allow decompiling bad ClassDef tables with invalid format, with
  warning (#1236).
- [varLib] Make STAT v1.2 and reuse nameIDs from fvar table (#1242).
- [varLib.plot] Show master locations. Set axis limits to -1, +1.
- [subset] Handle HVAR direct mapping. Passthrough 'cvar'.
  Added ``--font-number`` command-line option for collections.
- [t1Lib] Allow a text encoding to be specified when parsing a Type 1 font
  (#1234). Added ``kind`` argument to T1Font constructor (c5c161c).
- [ttLib] Added context manager API to ``TTFont`` class, so it can be used in
  ``with`` statements to auto-close the file when exiting the context (#1232).

3.25.0 (released 2018-04-03)
----------------------------

- [varLib] Improved support-resolution algorithm. Previously, the on-axis
  masters would always cut the space. They don't anymore. That's more
  consistent, and fixes the main issue Erik showed at TYPO Labs 2017.
  Any varfont built that had an unusual master configuration will change
  when rebuilt (42bef17, a523a697,
  https://github.com/googlei18n/fontmake/issues/264).
- [varLib.models] Added a ``main()`` entry point, that takes positions and
  prints model results.
- [varLib.plot] Added new module to plot a designspace's
  VariationModel. Requires ``matplotlib``.
- [varLib.mutator] Added -o option to specify output file path (2ef60fa).
- [otTables] Fixed IndexError while pruning of HVAR pre-write (6b6c34a).
- [varLib.models] Convert delta array to floats if values overflows signed
  short integer (0055f94).

3.24.2 (released 2018-03-26)
----------------------------

- [otBase] Don't fail during ``ValueRecord`` copy if src has more items.
  We drop hinting in the subsetter by simply changing ValueFormat, without
  cleaning up the actual ValueRecords. This was causing assertion error if
  a variable font was subsetted without hinting and then passed directly to
  the mutator for instantiation without first it saving to disk.

3.24.1 (released 2018-03-06)
----------------------------

- [varLib] Don't remap the same ``DeviceTable`` twice in VarStore optimizer
  (#1206).
- [varLib] Add ``--disable-iup`` option to ``fonttools varLib`` script,
  and a ``optimize=True`` keyword argument to ``varLib.build`` function,
  to optionally disable IUP optimization while building varfonts.
- [ttCollection] Fixed issue while decompiling ttc with python3 (#1207).

3.24.0 (released 2018-03-01)
----------------------------

- [ttGlyphPen] Decompose composite glyphs if any components' transform is too
  large to fit a ``F2Dot14`` value, or clamp transform values that are
  (almost) equal to +2.0 to make them fit and avoid decomposing (#1200,
  #1204, #1205).
- [ttx] Added new ``-g`` option to dump glyphs from the ``glyf`` table
  splitted as individual ttx files (#153, #1035, #1132, #1202).
- Copied ``ufoLib.filenames`` module to ``fontTools.misc.filenames``, used
  for the ttx split-glyphs option (#1202).
- [feaLib] Added support for ``cvParameters`` blocks in Character Variant
  feautures ``cv01-cv99`` (#860, #1169).
- [Snippets] Added ``checksum.py`` script to generate/check SHA1 hash of
  ttx files (#1197).
- [varLib.mutator] Fixed issue while instantiating some variable fonts
  whereby the horizontal advance width computed from ``gvar`` phantom points
  could turn up to be negative (#1198).
- [varLib/subset] Fixed issue with subsetting GPOS variation data not
  picking up ``ValueRecord`` ``Device`` objects (54fd71f).
- [feaLib/voltLib] In all AST elements, the ``location`` is no longer a
  required positional argument, but an optional kewyord argument (defaults
  to ``None``). This will make it easier to construct feature AST from
  code (#1201).


3.23.0 (released 2018-02-26)
----------------------------

- [designspaceLib] Added an optional ``lib`` element to the designspace as a
  whole, as well as to the instance elements, to store arbitrary data in a
  property list dictionary, similar to the UFO's ``lib``. Added an optional
  ``font`` attribute to the ``SourceDescriptor``, to allow operating on
  in-memory font objects (#1175).
- [cffLib] Fixed issue with lazy-loading of attributes when attempting to
  set the CFF TopDict.Encoding (#1177, #1187).
- [ttx] Fixed regression introduced in 3.22.0 that affected the split tables
  ``-s`` option (#1188).
- [feaLib] Added ``IncludedFeaNotFound`` custom exception subclass, raised
  when an included feature file cannot be found (#1186).
- [otTables] Changed ``VarIdxMap`` to use glyph names internally instead of
  glyph indexes. The old ttx dumps of HVAR/VVAR tables that contain indexes
  can still be imported (21cbab8, 38a0ffb).
- [varLib] Implemented VarStore optimizer (#1184).
- [subset] Implemented pruning of GDEF VarStore, HVAR and MVAR (#1179).
- [sfnt] Restore backward compatiblity with ``numFonts`` attribute of
  ``SFNTReader`` object (#1181).
- [merge] Initial support for merging ``LangSysRecords`` (#1180).
- [ttCollection] don't seek(0) when writing to possibly unseekable strems.
- [subset] Keep all ``--name-IDs`` from 0 to 6 by default (#1170, #605, #114).
- [cffLib] Added ``width`` module to calculate optimal CFF default and
  nominal glyph widths.
- [varLib] Don’t fail if STAT already in the master fonts (#1166).

3.22.0 (released 2018-02-04)
----------------------------

- [subset] Support subsetting ``endchar`` acting as ``seac``-like components
  in ``CFF`` (fixes #1162).
- [feaLib] Allow to build from pre-parsed ``ast.FeatureFile`` object.
  Added ``tables`` argument to only build some tables instead of all (#1159,
  #1163).
- [textTools] Replaced ``safeEval`` with ``ast.literal_eval`` (#1139).
- [feaLib] Added option to the parser to not resolve ``include`` statements
  (#1154).
- [ttLib] Added new ``ttCollection`` module to read/write TrueType and
  OpenType Collections. Exports a ``TTCollection`` class with a ``fonts``
  attribute containing a list of ``TTFont`` instances, the methods ``save``
  and ``saveXML``, plus some list-like methods. The ``importXML`` method is
  not implemented yet (#17).
- [unicodeadata] Added ``ot_tag_to_script`` function that converts from
  OpenType script tag to Unicode script code.
- Added new ``designspaceLib`` subpackage, originally from Erik Van Blokland's
  ``designSpaceDocument``: https://github.com/LettError/designSpaceDocument
  NOTE: this is not yet used internally by varLib, and the API may be subject
  to changes (#911, #1110, LettError/designSpaceDocument#28).
- Added new FontTools icon images (8ee7c32).
- [unicodedata] Added ``script_horizontal_direction`` function that returns
  either "LTR" or "RTL" given a unicode script code.
- [otConverters] Don't write descriptive name string as XML comment if the
  NameID value is 0 (== NULL) (#1151, #1152).
- [unicodedata] Add ``ot_tags_from_script`` function to get the list of
  OpenType script tags associated with unicode script code (#1150).
- [feaLib] Don't error when "enumerated" kern pairs conflict with preceding
  single pairs; emit warning and chose the first value (#1147, #1148).
- [loggingTools] In ``CapturingLogHandler.assertRegex`` method, match the
  fully formatted log message.
- [sbix] Fixed TypeError when concatenating str and bytes (#1154).
- [bezierTools] Implemented cusp support and removed ``approximate_fallback``
  arg in ``calcQuadraticArcLength``. Added ``calcCubicArcLength`` (#1142).

3.21.2 (released 2018-01-08)
----------------------------

- [varLib] Fixed merging PairPos Format1/2 with missing subtables (#1125).

3.21.1 (released 2018-01-03)
----------------------------

- [feaLib] Allow mixed single/multiple substitutions (#612)
- Added missing ``*.afm`` test assets to MAINFEST.in (#1137).
- Fixed dumping ``SVG`` tables containing color palettes (#1124).

3.21.0 (released 2017-12-18)
----------------------------

- [cmap] when compiling format6 subtable, don't assume gid0 is always called
  '.notdef' (1e42224).
- [ot] Allow decompiling fonts with bad Coverage format number (1aafae8).
- Change FontTools licence to MIT (#1127).
- [post] Prune extra names already in standard Mac set (df1e8c7).
- [subset] Delete empty SubrsIndex after subsetting (#994, #1118).
- [varLib] Don't share points in cvar by default, as it currently fails on
  some browsers (#1113).
- [afmLib] Make poor old afmLib work on python3.

3.20.1 (released 2017-11-22)
----------------------------

- [unicodedata] Fixed issue with ``script`` and ``script_extension`` functions
  returning inconsistent short vs long names. They both return the short four-
  letter script codes now. Added ``script_name`` and ``script_code`` functions
  to look up the long human-readable script name from the script code, and
  viceversa (#1109, #1111).

3.20.0 (released 2017-11-21)
----------------------------

- [unicodedata] Addded new module ``fontTools.unicodedata`` which exports the
  same interface as the built-in ``unicodedata`` module, with the addition of
  a few functions that are missing from the latter, such as ``script``,
  ``script_extension`` and ``block``. Added a ``MetaTools/buildUCD.py`` script
  to download and parse data files from the Unicode Character Database and
  generate python modules containing lists of ranges and property values.
- [feaLib] Added ``__str__`` method to all ``ast`` elements (delegates to the
  ``asFea`` method).
- [feaLib] ``Parser`` constructor now accepts a ``glyphNames`` iterable
  instead of ``glyphMap`` dict. The latter still works but with a pending
  deprecation warning (#1104).
- [bezierTools] Added arc length calculation functions originally from
  ``pens.perimeterPen`` module (#1101).
- [varLib] Started generating STAT table (8af4309). Right now it just reflects
  the axes, and even that with certain limitations:
  * AxisOrdering is set to the order axes are defined,
  * Name-table entries are not shared with fvar.
- [py23] Added backports for ``redirect_stdout`` and ``redirect_stderr``
  context managers (#1097).
- [Graphite] Fixed some round-trip bugs (#1093).

3.19.0 (released 2017-11-06)
----------------------------

- [varLib] Try set of used points instead of all points when testing whether to
  share points between tuples (#1090).
- [CFF2] Fixed issue with reading/writing PrivateDict BlueValues to TTX file.
  Read the commit message 8b02b5a and issue #1030 for more details.
  NOTE: this change invalidates all the TTX files containing CFF2 tables
  that where dumped with previous verisons of fonttools.
  CFF2 Subr items can have values on the stack after the last operator, thus
  a ``CFF2Subr`` class was added to accommodate this (#1091).
- [_k_e_r_n] Fixed compilation of AAT kern version=1.0 tables (#1089, #1094)
- [ttLib] Added getBestCmap() convenience method to TTFont class and cmap table
  class that returns a preferred Unicode cmap subtable given a list of options
  (#1092).
- [morx] Emit more meaningful subtable flags. Implement InsertionMorphAction

3.18.0 (released 2017-10-30)
----------------------------

- [feaLib] Fixed writing back nested glyph classes (#1086).
- [TupleVariation] Reactivated shared points logic, bugfixes (#1009).
- [AAT] Implemented ``morx`` ligature subtables (#1082).
- [reverseContourPen] Keep duplicate lineTo following a moveTo (#1080,
  https://github.com/googlei18n/cu2qu/issues/51).
- [varLib.mutator] Suport instantiation of GPOS, GDEF and MVAR (#1079).
- [sstruct] Fixed issue with ``unicode_literals`` and ``struct`` module in
  old versions of python 2.7 (#993).

3.17.0 (released 2017-10-16)
----------------------------

- [svgPathPen] Added an ``SVGPathPen`` that translates segment pen commands
  into SVG path descriptions. Copied from Tal Leming's ``ufo2svg.svgPathPen``
  https://github.com/typesupply/ufo2svg/blob/d69f992/Lib/ufo2svg/svgPathPen.py
- [reverseContourPen] Added ``ReverseContourPen``, a filter pen that draws
  contours with the winding direction reversed, while keeping the starting
  point (#1071).
- [filterPen] Added ``ContourFilterPen`` to manipulate contours as a whole
  rather than segment by segment.
- [arrayTools] Added ``Vector`` class to apply math operations on an array
  of numbers, and ``pairwise`` function to loop over pairs of items in an
  iterable.
- [varLib] Added support for building and interpolation of ``cvar`` table
  (f874cf6, a25a401).

3.16.0 (released 2017-10-03)
----------------------------

- [head] Try using ``SOURCE_DATE_EPOCH`` environment variable when setting
  the ``head`` modified timestamp to ensure reproducible builds (#1063).
  See https://reproducible-builds.org/specs/source-date-epoch/
- [VTT] Decode VTT's ``TSI*`` tables text as UTF-8 (#1060).
- Added support for Graphite font tables: Feat, Glat, Gloc, Silf and Sill.
  Thanks @mhosken! (#1054).
- [varLib] Default to using axis "name" attribute if "labelname" element
  is missing (588f524).
- [merge] Added support for merging Script records. Remove unused features
  and lookups after merge (d802580, 556508b).
- Added ``fontTools.svgLib`` package. Includes a parser for SVG Paths that
  supports the Pen protocol (#1051). Also, added a snippet to convert SVG
  outlines to UFO GLIF (#1053).
- [AAT] Added support for ``ankr``, ``bsln``, ``mort``, ``morx``, ``gcid``,
  and ``cidg``.
- [subset] Implemented subsetting of ``prop``, ``opbd``, ``bsln``, ``lcar``.

3.15.1 (released 2017-08-18)
----------------------------

- [otConverters] Implemented ``__add__`` and ``__radd__`` methods on
  ``otConverters._LazyList`` that decompile a lazy list before adding
  it to another list or ``_LazyList`` instance. Fixes an ``AttributeError``
  in the ``subset`` module when attempting to sum ``_LazyList`` objects
  (6ef48bd2, 1aef1683).
- [AAT] Support the `opbd` table with optical bounds (a47f6588).
- [AAT] Support `prop` table with glyph properties (d05617b4).


3.15.0 (released 2017-08-17)
----------------------------

- [AAT] Added support for AAT lookups. The ``lcar`` table can be decompiled
  and recompiled; futher work needed to handle ``morx`` table (#1025).
- [subset] Keep (empty) DefaultLangSys for Script 'DFLT' (6eb807b5).
- [subset] Support GSUB/GPOS.FeatureVariations (fe01d87b).
- [varLib] In ``models.supportScalars``, ignore an axis when its peak value
  is 0 (fixes #1020).
- [varLib] Add default mappings to all axes in avar to fix rendering issue
  in some rasterizers (19c4b377, 04eacf13).
- [varLib] Flatten multiple tail PairPosFormat2 subtables before merging
  (c55ef525).
- [ttLib] Added support for recalculating font bounding box in ``CFF`` and
  ``head`` tables, and min/max values in ``hhea`` and ``vhea`` tables (#970).

3.14.0 (released 2017-07-31)
----------------------------

- [varLib.merger] Remove Extensions subtables before merging (f7c20cf8).
- [varLib] Initialize the avar segment map with required default entries
  (#1014).
- [varLib] Implemented optimal IUP optmiziation (#1019).
- [otData] Add ``AxisValueFormat4`` for STAT table v1.2 from OT v1.8.2
  (#1015).
- [name] Fixed BCP46 language tag for Mac langID=9: 'si' -> 'sl'.
- [subset] Return value from ``_DehintingT2Decompiler.op_hintmask``
  (c0d672ba).
- [cffLib] Allow to get TopDict by index as well as by name (dca96c9c).
- [cffLib] Removed global ``isCFF2`` state; use one set of classes for
  both CFF and CFF2, maintaining backward compatibility existing code (#1007).
- [cffLib] Deprecated maxstack operator, per OpenType spec update 1.8.1.
- [cffLib] Added missing default (-100) for UnderlinePosition (#983).
- [feaLib] Enable setting nameIDs greater than 255 (#1003).
- [varLib] Recalculate ValueFormat when merging SinglePos (#996).
- [varLib] Do not emit MVAR if there are no entries in the variation store
  (#987).
- [ttx] For ``-x`` option, pad with space if table tag length is < 4.

3.13.1 (released 2017-05-30)
----------------------------

- [feaLib.builder] Removed duplicate lookups optimization. The original
  lookup order and semantics of the feature file are preserved (#976).

3.13.0 (released 2017-05-24)
----------------------------

- [varLib.mutator] Implement IUP optimization (#969).
- [_g_l_y_f.GlyphCoordinates] Changed ``__bool__()`` semantics to match those
  of other iterables (e46f949). Removed ``__abs__()`` (3db5be2).
- [varLib.interpolate_layout] Added ``mapped`` keyword argument to
  ``interpolate_layout`` to allow disabling avar mapping: if False (default),
  the location is mapped using the map element of the axes in designspace file;
  if True, it is assumed that location is in designspace's internal space and
  no mapping is performed (#950, #975).
- [varLib.interpolate_layout] Import designspace-loading logic from varLib.
- [varLib] Fixed bug with recombining PairPosClass2 subtables (81498e5, #914).
- [cffLib.specializer] When copying iterables, cast to list (462b7f86).

3.12.1 (released 2017-05-18)
----------------------------

- [pens.t2CharStringPen] Fixed AttributeError when calling addComponent in
  T2CharStringPen (#965).

3.12.0 (released 2017-05-17)
----------------------------

- [cffLib.specializer] Added new ``specializer`` module to optimize CFF
  charstrings, used by the T2CharStringPen (#948).
- [varLib.mutator] Sort glyphs by component depth before calculating composite
  glyphs' bounding boxes to ensure deltas are correctly caclulated (#945).
- [_g_l_y_f] Fixed loss of precision in GlyphCoordinates by using 'd' (double)
  instead of 'f' (float) as ``array.array`` typecode (#963, #964).

3.11.0 (released 2017-05-03)
----------------------------

- [t2CharStringPen] Initial support for specialized Type2 path operators:
  vmoveto, hmoveto, vlineto, hlineto, vvcurveto, hhcurveto, vhcurveto and
  hvcurveto. This should produce more compact charstrings (#940, #403).
- [Doc] Added Sphinx sources for the documentation. Thanks @gferreira (#935).
- [fvar] Expose flags in XML (#932)
- [name] Add helper function for building multi-lingual names (#921)
- [varLib] Fixed kern merging when a PairPosFormat2 has ClassDef1 with glyphs
  that are NOT present in the Coverage (1b5e1c4, #939).
- [varLib] Fixed non-deterministic ClassDef order with PY3 (f056c12, #927).
- [feLib] Throw an error when the same glyph is defined in multiple mark
  classes within the same lookup (3e3ff00, #453).

3.10.0 (released 2017-04-14)
----------------------------

- [varLib] Added support for building ``avar`` table, using the designspace
  ``<map>`` elements.
- [varLib] Removed unused ``build(..., axisMap)`` argument. Axis map should
  be specified in designspace file now. We do not accept nonstandard axes
  if ``<axes>`` element is not present.
- [varLib] Removed "custom" axis from the ``standard_axis_map``. This was
  added before when glyphsLib was always exporting the (unused) custom axis.
- [varLib] Added partial support for building ``MVAR`` table; does not
  implement ``gasp`` table variations yet.
- [pens] Added FilterPen base class, for pens that control another pen;
  factored out ``addComponent`` method from BasePen into a separate abstract
  DecomposingPen class; added DecomposingRecordingPen, which records
  components decomposed as regular contours.
- [TSI1] Fixed computation of the textLength of VTT private tables (#913).
- [loggingTools] Added ``LogMixin`` class providing a ``log`` property to
  subclasses, which returns a ``logging.Logger`` named after the latter.
- [loggingTools] Added ``assertRegex`` method to ``CapturingLogHandler``.
- [py23] Added backport for python 3's ``types.SimpleNamespace`` class.
- [EBLC] Fixed issue with python 3 ``zip`` iterator.

3.9.2 (released 2017-04-08)
---------------------------

- [pens] Added pen to draw glyphs using WxPython ``GraphicsPath`` class:
  https://wxpython.org/docs/api/wx.GraphicsPath-class.html
- [varLib.merger] Fixed issue with recombining multiple PairPosFormat2
  subtables (#888)
- [varLib] Do not encode gvar deltas that are all zeroes, or if all values
  are smaller than tolerance.
- [ttLib] _TTGlyphSet glyphs now also have ``height`` and ``tsb`` (top
  side bearing) attributes from the ``vmtx`` table, if present.
- [glyf] In ``GlyphCoordintes`` class, added ``__bool__`` / ``__nonzero__``
  methods, and ``array`` property to get raw array.
- [ttx] Support reading TTX files with BOM (#896)
- [CFF2] Fixed the reporting of the number of regions in the font.

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
