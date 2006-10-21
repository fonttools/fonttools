otData = [

	#
	# common (generated from chapter2.htm)
	#

	('ScriptList', [
		('uint16', 'ScriptCount', None, None, 'Number of ScriptRecords'),
		('struct', 'ScriptRecord', 'ScriptCount', 0, 'Array of ScriptRecords -listed alphabetically by ScriptTag'),
	]),

	('ScriptRecord', [
		('Tag', 'ScriptTag', None, None, '4-byte ScriptTag identifier'),
		('Offset', 'Script', None, None, 'Offset to Script table-from beginning of ScriptList'),
	]),

	('Script', [
		('Offset', 'DefaultLangSys', None, None, 'Offset to DefaultLangSys table-from beginning of Script table-may be NULL'),
		('uint16', 'LangSysCount', None, None, 'Number of LangSysRecords for this script-excluding the DefaultLangSys'),
		('struct', 'LangSysRecord', 'LangSysCount', 0, 'Array of LangSysRecords-listed alphabetically by LangSysTag'),
	]),

	('LangSysRecord', [
		('Tag', 'LangSysTag', None, None, '4-byte LangSysTag identifier'),
		('Offset', 'LangSys', None, None, 'Offset to LangSys table-from beginning of Script table'),
	]),

	('LangSys', [
		('Offset', 'LookupOrder', None, None, '= NULL (reserved for an offset to a reordering table)'),
		('uint16', 'ReqFeatureIndex', None, None, 'Index of a feature required for this language system- if no required features = 0xFFFF'),
		('uint16', 'FeatureCount', None, None, 'Number of FeatureIndex values for this language system-excludes the required feature'),
		('uint16', 'FeatureIndex', 'FeatureCount', 0, 'Array of indices into the FeatureList-in arbitrary order'),
	]),

	('FeatureList', [
		('uint16', 'FeatureCount', None, None, 'Number of FeatureRecords in this table'),
		('struct', 'FeatureRecord', 'FeatureCount', 0, 'Array of FeatureRecords-zero-based (first feature has FeatureIndex = 0)-listed alphabetically by FeatureTag'),
	]),

	('FeatureRecord', [
		('Tag', 'FeatureTag', None, None, '4-byte feature identification tag'),
		('Offset', 'Feature', None, None, 'Offset to Feature table-from beginning of FeatureList'),
	]),

	('Feature', [
		('Offset', 'FeatureParams', None, None, '= NULL (reserved for offset to FeatureParams)'),
		('uint16', 'LookupCount', None, None, 'Number of LookupList indices for this feature'),
		('uint16', 'LookupListIndex', 'LookupCount', 0, 'Array of LookupList indices for this feature -zero-based (first lookup is LookupListIndex = 0)'),
	]),

	('LookupList', [
		('uint16', 'LookupCount', None, None, 'Number of lookups in this table'),
		('Offset', 'Lookup', 'LookupCount', 0, 'Array of offsets to Lookup tables-from beginning of LookupList -zero based (first lookup is Lookup index = 0)'),
	]),

	('Lookup', [
		('uint16', 'LookupType', None, None, 'Different enumerations for GSUB and GPOS'),
		('uint16', 'LookupFlag', None, None, 'Lookup qualifiers'),
		('uint16', 'SubTableCount', None, None, 'Number of SubTables for this lookup'),
		('Offset', 'SubTable', 'SubTableCount', 0, 'Array of offsets to SubTables-from beginning of Lookup table'),
	]),

	('CoverageFormat1', [
		('uint16', 'CoverageFormat', None, None, 'Format identifier-format = 1'),
		('uint16', 'GlyphCount', None, None, 'Number of glyphs in the GlyphArray'),
		('GlyphID', 'GlyphArray', 'GlyphCount', 0, 'Array of GlyphIDs-in numerical order'),
	]),

	('CoverageFormat2', [
		('uint16', 'CoverageFormat', None, None, 'Format identifier-format = 2'),
		('uint16', 'RangeCount', None, None, 'Number of RangeRecords'),
		('struct', 'RangeRecord', 'RangeCount', 0, 'Array of glyph ranges-ordered by Start GlyphID'),
	]),

	('RangeRecord', [
		('GlyphID', 'Start', None, None, 'First GlyphID in the range'),
		('GlyphID', 'End', None, None, 'Last GlyphID in the range'),
		('uint16', 'StartCoverageIndex', None, None, 'Coverage Index of first GlyphID in range'),
	]),

	('ClassDefFormat1', [
		('uint16', 'ClassFormat', None, None, 'Format identifier-format = 1'),
		('GlyphID', 'StartGlyph', None, None, 'First GlyphID of the ClassValueArray'),
		('uint16', 'GlyphCount', None, None, 'Size of the ClassValueArray'),
		('uint16', 'ClassValueArray', 'GlyphCount', 0, 'Array of Class Values-one per GlyphID'),
	]),

	('ClassDefFormat2', [
		('uint16', 'ClassFormat', None, None, 'Format identifier-format = 2'),
		('uint16', 'ClassRangeCount', None, None, 'Number of ClassRangeRecords'),
		('struct', 'ClassRangeRecord', 'ClassRangeCount', 0, 'Array of ClassRangeRecords-ordered by Start GlyphID'),
	]),

	('ClassRangeRecord', [
		('GlyphID', 'Start', None, None, 'First GlyphID in the range'),
		('GlyphID', 'End', None, None, 'Last GlyphID in the range'),
		('uint16', 'Class', None, None, 'Applied to all glyphs in the range'),
	]),

	('Device', [
		('uint16', 'StartSize', None, None, 'Smallest size to correct-in ppem'),
		('uint16', 'EndSize', None, None, 'Largest size to correct-in ppem'),
		('uint16', 'DeltaFormat', None, None, 'Format of DeltaValue array data: 1, 2, or 3'),
		('uint16', 'DeltaValue', '', 0, 'Array of compressed data'),
	]),


	#
	# gpos (generated from gpos.htm)
	#

	('GPOS', [
		('Fixed', 'Version', None, None, 'Version of the GPOS table-initially = 0x00010000'),
		('Offset', 'ScriptList', None, None, 'Offset to ScriptList table-from beginning of GPOS table'),
		('Offset', 'FeatureList', None, None, 'Offset to FeatureList table-from beginning of GPOS table'),
		('Offset', 'LookupList', None, None, 'Offset to LookupList table-from beginning of GPOS table'),
	]),

	('SinglePosFormat1', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of SinglePos subtable'),
		('uint16', 'ValueFormat', None, None, 'Defines the types of data in the ValueRecord'),
		('ValueRecord', 'Value', None, None, 'Defines positioning value(s)-applied to all glyphs in the Coverage table'),
	]),

	('SinglePosFormat2', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 2'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of SinglePos subtable'),
		('uint16', 'ValueFormat', None, None, 'Defines the types of data in the ValueRecord'),
		('uint16', 'ValueCount', None, None, 'Number of ValueRecords'),
		('ValueRecord', 'Value', 'ValueCount', 0, 'Array of ValueRecords-positioning values applied to glyphs'),
	]),

	('PairPosFormat1', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of PairPos subtable-only the first glyph in each pair'),
		('uint16', 'ValueFormat1', None, None, 'Defines the types of data in ValueRecord1-for the first glyph in the pair -may be zero (0)'),
		('uint16', 'ValueFormat2', None, None, 'Defines the types of data in ValueRecord2-for the second glyph in the pair -may be zero (0)'),
		('uint16', 'PairSetCount', None, None, 'Number of PairSet tables'),
		('Offset', 'PairSet', 'PairSetCount', 0, 'Array of offsets to PairSet tables-from beginning of PairPos subtable-ordered by Coverage Index'),
	]),

	('PairSet', [
		('uint16', 'PairValueCount', None, None, 'Number of PairValueRecords'),
		('struct', 'PairValueRecord', 'PairValueCount', 0, 'Array of PairValueRecords-ordered by GlyphID of the second glyph'),
	]),

	('PairValueRecord', [
		('GlyphID', 'SecondGlyph', None, None, 'GlyphID of second glyph in the pair-first glyph is listed in the Coverage table'),
		('ValueRecord', 'Value1', None, None, 'Positioning data for the first glyph in the pair'),
		('ValueRecord', 'Value2', None, None, 'Positioning data for the second glyph in the pair'),
	]),

	('PairPosFormat2', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 2'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of PairPos subtable-for the first glyph of the pair'),
		('uint16', 'ValueFormat1', None, None, 'ValueRecord definition-for the first glyph of the pair-may be zero (0)'),
		('uint16', 'ValueFormat2', None, None, 'ValueRecord definition-for the second glyph of the pair-may be zero (0)'),
		('Offset', 'ClassDef1', None, None, 'Offset to ClassDef table-from beginning of PairPos subtable-for the first glyph of the pair'),
		('Offset', 'ClassDef2', None, None, 'Offset to ClassDef table-from beginning of PairPos subtable-for the second glyph of the pair'),
		('uint16', 'Class1Count', None, None, 'Number of classes in ClassDef1 table-includes Class0'),
		('uint16', 'Class2Count', None, None, 'Number of classes in ClassDef2 table-includes Class0'),
		('struct', 'Class1Record', 'Class1Count', 0, 'Array of Class1 records-ordered by Class1'),
	]),

	('Class1Record', [
		('struct', 'Class2Record', 'Class2Count', 0, 'Array of Class2 records-ordered by Class2'),
	]),

	('Class2Record', [
		('ValueRecord', 'Value1', None, None, 'Positioning for first glyph-empty if ValueFormat1 = 0'),
		('ValueRecord', 'Value2', None, None, 'Positioning for second glyph-empty if ValueFormat2 = 0'),
	]),

	('CursivePosFormat1', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of CursivePos subtable'),
		('uint16', 'EntryExitCount', None, None, 'Number of EntryExit records'),
		('struct', 'EntryExitRecord', 'EntryExitCount', 0, 'Array of EntryExit records-in Coverage Index order'),
	]),

	('EntryExitRecord', [
		('Offset', 'EntryAnchor', None, None, 'Offset to EntryAnchor table-from beginning of CursivePos subtable-may be NULL'),
		('Offset', 'ExitAnchor', None, None, 'Offset to ExitAnchor table-from beginning of CursivePos subtable-may be NULL'),
	]),

	('MarkBasePosFormat1', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'MarkCoverage', None, None, 'Offset to MarkCoverage table-from beginning of MarkBasePos subtable'),
		('Offset', 'BaseCoverage', None, None, 'Offset to BaseCoverage table-from beginning of MarkBasePos subtable'),
		('uint16', 'ClassCount', None, None, 'Number of classes defined for marks'),
		('Offset', 'MarkArray', None, None, 'Offset to MarkArray table-from beginning of MarkBasePos subtable'),
		('Offset', 'BaseArray', None, None, 'Offset to BaseArray table-from beginning of MarkBasePos subtable'),
	]),

	('BaseArray', [
		('uint16', 'BaseCount', None, None, 'Number of BaseRecords'),
		('struct', 'BaseRecord', 'BaseCount', 0, 'Array of BaseRecords-in order of BaseCoverage Index'),
	]),

	('BaseRecord', [
		('Offset', 'BaseAnchor', 'ClassCount', 0, 'Array of offsets (one per class) to Anchor tables-from beginning of BaseArray table-ordered by class-zero-based'),
	]),

	('MarkLigPosFormat1', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'MarkCoverage', None, None, 'Offset to Mark Coverage table-from beginning of MarkLigPos subtable'),
		('Offset', 'LigatureCoverage', None, None, 'Offset to Ligature Coverage table-from beginning of MarkLigPos subtable'),
		('uint16', 'ClassCount', None, None, 'Number of defined mark classes'),
		('Offset', 'MarkArray', None, None, 'Offset to MarkArray table-from beginning of MarkLigPos subtable'),
		('Offset', 'LigatureArray', None, None, 'Offset to LigatureArray table-from beginning of MarkLigPos subtable'),
	]),

	('LigatureArray', [
		('uint16', 'LigatureCount', None, None, 'Number of LigatureAttach table offsets'),
		('Offset', 'LigatureAttach', 'LigatureCount', 0, 'Array of offsets to LigatureAttach tables-from beginning of LigatureArray table-ordered by LigatureCoverage Index'),
	]),

	('LigatureAttach', [
		('uint16', 'ComponentCount', None, None, 'Number of ComponentRecords in this ligature'),
		('struct', 'ComponentRecord', 'ComponentCount', 0, 'Array of Component records-ordered in writing direction'),
	]),

	('ComponentRecord', [
		('Offset', 'LigatureAnchor', 'ClassCount', 0, 'Array of offsets (one per class) to Anchor tables-from beginning of LigatureAttach table-ordered by class-NULL if a component does not have an attachment for a class-zero-based array'),
	]),

	('MarkMarkPosFormat1', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Mark1Coverage', None, None, 'Offset to Combining Mark Coverage table-from beginning of MarkMarkPos subtable'),
		('Offset', 'Mark2Coverage', None, None, 'Offset to Base Mark Coverage table-from beginning of MarkMarkPos subtable'),
		('uint16', 'ClassCount', None, None, 'Number of Combining Mark classes defined'),
		('Offset', 'Mark1Array', None, None, 'Offset to MarkArray table for Mark1-from beginning of MarkMarkPos subtable'),
		('Offset', 'Mark2Array', None, None, 'Offset to Mark2Array table for Mark2-from beginning of MarkMarkPos subtable'),
	]),

	('Mark2Array', [
		('uint16', 'Mark2Count', None, None, 'Number of Mark2 records'),
		('struct', 'Mark2Record', 'Mark2Count', 0, 'Array of Mark2 records-in Coverage order'),
	]),

	('Mark2Record', [
		('Offset', 'Mark2Anchor', 'ClassCount', 0, 'Array of offsets (one per class) to Anchor tables-from beginning of Mark2Array table-zero-based array'),
	]),

	('PosLookupRecord', [
		('uint16', 'SequenceIndex', None, None, 'Index to input glyph sequence-first glyph = 0'),
		('uint16', 'LookupListIndex', None, None, 'Lookup to apply to that position-zero-based'),
	]),

	('ContextPosFormat1', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of ContextPos subtable'),
		('uint16', 'PosRuleSetCount', None, None, 'Number of PosRuleSet tables'),
		('Offset', 'PosRuleSet', 'PosRuleSetCount', 0, 'Array of offsets to PosRuleSet tables-from beginning of ContextPos subtable-ordered by Coverage Index'),
	]),

	('PosRuleSet', [
		('uint16', 'PosRuleCount', None, None, 'Number of PosRule tables'),
		('Offset', 'PosRule', 'PosRuleCount', 0, 'Array of offsets to PosRule tables-from beginning of PosRuleSet-ordered by preference'),
	]),

	('PosRule', [
		('uint16', 'GlyphCount', None, None, 'Number of glyphs in the Input glyph sequence'),
		('uint16', 'PosCount', None, None, 'Number of PosLookupRecords'),
		('GlyphID', 'Input', 'GlyphCount', -1, 'Array of input GlyphIDs-starting with the second glyph'),
		('struct', 'PosLookupRecord', 'PosCount', 0, 'Array of positioning lookups-in design order'),
	]),

	('ContextPosFormat2', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 2'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of ContextPos subtable'),
		('Offset', 'ClassDef', None, None, 'Offset to ClassDef table-from beginning of ContextPos subtable'),
		('uint16', 'PosClassSetCount', None, None, 'Number of PosClassSet tables'),
		('Offset', 'PosClassSet', 'PosClassSetCount', 0, 'Array of offsets to PosClassSet tables-from beginning of ContextPos subtable-ordered by class-may be NULL'),
	]),

	('PosClassSet', [
		('uint16', 'PosClassRuleCount', None, None, 'Number of PosClassRule tables'),
		('Offset', 'PosClassRule', 'PosClassRuleCount', 0, 'Array of offsets to PosClassRule tables-from beginning of PosClassSet-ordered by preference'),
	]),

	('PosClassRule', [
		('uint16', 'GlyphCount', None, None, 'Number of glyphs to be matched'),
		('uint16', 'PosCount', None, None, 'Number of PosLookupRecords'),
		('uint16', 'Class', 'GlyphCount', -1, 'Array of classes-beginning with the second class-to be matched to the input glyph sequence'),
		('struct', 'PosLookupRecord', 'PosCount', 0, 'Array of positioning lookups-in design order'),
	]),

	('ContextPosFormat3', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 3'),
		('uint16', 'GlyphCount', None, None, 'Number of glyphs in the input sequence'),
		('uint16', 'PosCount', None, None, 'Number of PosLookupRecords'),
		('Offset', 'Coverage', 'GlyphCount', 0, 'Array of offsets to Coverage tables-from beginning of ContextPos subtable'),
		('struct', 'PosLookupRecord', 'PosCount', 0, 'Array of positioning lookups-in design order'),
	]),

	('ChainContextPosFormat1', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of ContextPos subtable'),
		('uint16', 'ChainPosRuleSetCount', None, None, 'Number of ChainPosRuleSet tables'),
		('Offset', 'ChainPosRuleSet', 'ChainPosRuleSetCount', 0, 'Array of offsets to ChainPosRuleSet tables-from beginning of ContextPos subtable-ordered by Coverage Index'),
	]),

	('ChainPosRuleSet', [
		('uint16', 'ChainPosRuleCount', None, None, 'Number of ChainPosRule tables'),
		('Offset', 'ChainPosRule', 'ChainPosRuleCount', 0, 'Array of offsets to ChainPosRule tables-from beginning of ChainPosRuleSet-ordered by preference'),
	]),

	('ChainPosRule', [
		('uint16', 'BacktrackGlyphCount', None, None, 'Total number of glyphs in the backtrack sequence (number of glyphs to be matched before the first glyph)'),
		('GlyphID', 'Backtrack', 'BacktrackGlyphCount', 0, "Array of backtracking GlyphID's (to be matched before the input sequence)"),
		('uint16', 'InputGlyphCount', None, None, 'Total number of glyphs in the input sequence (includes the first glyph)'),
		('GlyphID', 'Input', 'InputGlyphCount', -1, 'Array of input GlyphIDs (start with second glyph)'),
		('uint16', 'LookAheadGlyphCount', None, None, 'Total number of glyphs in the look ahead sequence (number of glyphs to be matched after the input sequence)'),
		('GlyphID', 'LookAhead', 'LookAheadGlyphCount', 0, "Array of lookahead GlyphID's (to be matched after the input sequence)"),
		('uint16', 'PosCount', None, None, 'Number of PosLookupRecords'),
		('struct', 'PosLookupRecord', 'PosCount', 0, 'Array of PosLookupRecords (in design order)'),
	]),

	('ChainContextPosFormat2', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 2'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of ChainContextPos subtable'),
		('Offset', 'BacktrackClassDef', None, None, 'Offset to ClassDef table containing backtrack sequence context-from beginning of ChainContextPos subtable'),
		('Offset', 'InputClassDef', None, None, 'Offset to ClassDef table containing input sequence context-from beginning of ChainContextPos subtable'),
		('Offset', 'LookAheadClassDef', None, None, 'Offset to ClassDef table containing lookahead sequence context-from beginning of ChainContextPos subtable'),
		('uint16', 'ChainPosClassSetCount', None, None, 'Number of ChainPosClassSet tables'),
		('Offset', 'ChainPosClassSet', 'ChainPosClassSetCount', 0, 'Array of offsets to ChainPosClassSet tables-from beginning of ChainContextPos subtable-ordered by input class-may be NULL'),
	]),

	('ChainPosClassSet', [
		('uint16', 'ChainPosClassRuleCount', None, None, 'Number of ChainPosClassRule tables'),
		('Offset', 'ChainPosClassRule', 'ChainPosClassRuleCount', 0, 'Array of offsets to ChainPosClassRule tables-from beginning of ChainPosClassSet-ordered by preference'),
	]),

	('ChainPosClassRule', [
		('uint16', 'BacktrackGlyphCount', None, None, 'Total number of glyphs in the backtrack sequence (number of glyphs to be matched before the first glyph)'),
		('uint16', 'Backtrack', 'BacktrackGlyphCount', 0, 'Array of backtracking classes(to be matched before the input sequence)'),
		('uint16', 'InputGlyphCount', None, None, 'Total number of classes in the input sequence (includes the first class)'),
		('uint16', 'Input', 'InputGlyphCount', -1, 'Array of input classes(start with second class; to be matched with the input glyph sequence)'),
		('uint16', 'LookAheadGlyphCount', None, None, 'Total number of classes in the look ahead sequence (number of classes to be matched after the input sequence)'),
		('uint16', 'LookAhead', 'LookAheadGlyphCount', 0, 'Array of lookahead classes(to be matched after the input sequence)'),
		('uint16', 'PosCount', None, None, 'Number of PosLookupRecords'),
		('struct', 'PosLookupRecord', 'PosCount', 0, 'Array of PosLookupRecords (in design order)'),
	]),

	('ChainContextPosFormat3', [
		('uint16', 'PosFormat', None, None, 'Format identifier-format = 3'),
		('uint16', 'BacktrackGlyphCount', None, None, 'Number of glyphs in the backtracking sequence'),
		('Offset', 'BacktrackCoverage', 'BacktrackGlyphCount', 0, 'Array of offsets to coverage tables in backtracking sequence, in glyph sequence order'),
		('uint16', 'InputGlyphCount', None, None, 'Number of glyphs in input sequence'),
		('Offset', 'InputCoverage', 'InputGlyphCount', 0, 'Array of offsets to coverage tables in input sequence, in glyph sequence order'),
		('uint16', 'LookAheadGlyphCount', None, None, 'Number of glyphs in lookahead sequence'),
		('Offset', 'LookAheadCoverage', 'LookAheadGlyphCount', 0, 'Array of offsets to coverage tables in lookahead sequence, in glyph sequence order'),
		('uint16', 'PosCount', None, None, 'Number of PosLookupRecords'),
		('struct', 'PosLookupRecord', 'PosCount', 0, 'Array of PosLookupRecords,in design order'),
	]),

	('ExtensionPosFormat1', [
		('USHORT', 'ExtFormat', None, None, 'Format identifier. Set to 1.'),
		('USHORT', 'ExtensionLookupType', None, None, 'Lookup type of subtable referenced by ExtensionOffset (i.e. the extension subtable).'),
		('LOffset', 'ExtSubTable', None, None, 'Array of offsets to Lookup tables-from beginning of LookupList -zero based (first lookup is Lookup index = 0)'),
	]),

	('ValueRecord', [
		('int16', 'XPlacement', None, None, 'Horizontal adjustment for placement-in design units'),
		('int16', 'YPlacement', None, None, 'Vertical adjustment for placement-in design units'),
		('int16', 'XAdvance', None, None, 'Horizontal adjustment for advance-in design units (only used for horizontal writing)'),
		('int16', 'YAdvance', None, None, 'Vertical adjustment for advance-in design units (only used for vertical writing)'),
		('Offset', 'XPlaDevice', None, None, 'Offset to Device table for horizontal placement-measured from beginning of PosTable (may be NULL)'),
		('Offset', 'YPlaDevice', None, None, 'Offset to Device table for vertical placement-measured from beginning of PosTable (may be NULL)'),
		('Offset', 'XAdvDevice', None, None, 'Offset to Device table for horizontal advance-measured from beginning of PosTable (may be NULL)'),
		('Offset', 'YAdvDevice', None, None, 'Offset to Device table for vertical advance-measured from beginning of PosTable (may be NULL)'),
	]),

	('AnchorFormat1', [
		('uint16', 'AnchorFormat', None, None, 'Format identifier-format = 1'),
		('int16', 'XCoordinate', None, None, 'Horizontal value-in design units'),
		('int16', 'YCoordinate', None, None, 'Vertical value-in design units'),
	]),

	('AnchorFormat2', [
		('uint16', 'AnchorFormat', None, None, 'Format identifier-format = 2'),
		('int16', 'XCoordinate', None, None, 'Horizontal value-in design units'),
		('int16', 'YCoordinate', None, None, 'Vertical value-in design units'),
		('uint16', 'AnchorPoint', None, None, 'Index to glyph contour point'),
	]),

	('AnchorFormat3', [
		('uint16', 'AnchorFormat', None, None, 'Format identifier-format = 3'),
		('int16', 'XCoordinate', None, None, 'Horizontal value-in design units'),
		('int16', 'YCoordinate', None, None, 'Vertical value-in design units'),
		('Offset', 'XDeviceTable', None, None, 'Offset to Device table for X coordinate- from beginning of Anchor table (may be NULL)'),
		('Offset', 'YDeviceTable', None, None, 'Offset to Device table for Y coordinate- from beginning of Anchor table (may be NULL)'),
	]),

	('MarkArray', [
		('uint16', 'MarkCount', None, None, 'Number of MarkRecords'),
		('struct', 'MarkRecord', 'MarkCount', 0, 'Array of MarkRecords-in Coverage order'),
	]),

	('MarkRecord', [
		('uint16', 'Class', None, None, 'Class defined for this mark'),
		('Offset', 'MarkAnchor', None, None, 'Offset to Anchor table-from beginning of MarkArray table'),
	]),


	#
	# gsub (generated from gsub.htm)
	#

	('GSUB', [
		('Fixed', 'Version', None, None, 'Version of the GSUB table-initially set to 0x00010000'),
		('Offset', 'ScriptList', None, None, 'Offset to ScriptList table-from beginning of GSUB table'),
		('Offset', 'FeatureList', None, None, 'Offset to FeatureList table-from beginning of GSUB table'),
		('Offset', 'LookupList', None, None, 'Offset to LookupList table-from beginning of GSUB table'),
	]),

	('SingleSubstFormat1', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('int16', 'DeltaGlyphID', None, None, 'Add to original GlyphID to get substitute GlyphID'),
	]),

	('SingleSubstFormat2', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 2'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('uint16', 'GlyphCount', None, None, 'Number of GlyphIDs in the Substitute array'),
		('GlyphID', 'Substitute', 'GlyphCount', 0, 'Array of substitute GlyphIDs-ordered by Coverage Index'),
	]),

	('MultipleSubstFormat1', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('uint16', 'SequenceCount', None, None, 'Number of Sequence table offsets in the Sequence array'),
		('Offset', 'Sequence', 'SequenceCount', 0, 'Array of offsets to Sequence tables-from beginning of Substitution table-ordered by Coverage Index'),
	]),

	('Sequence', [
		('uint16', 'GlyphCount', None, None, 'Number of GlyphIDs in the Substitute array. This should always be greater than 0.'),
		('GlyphID', 'Substitute', 'GlyphCount', 0, 'String of GlyphIDs to substitute'),
	]),

	('AlternateSubstFormat1', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('uint16', 'AlternateSetCount', None, None, 'Number of AlternateSet tables'),
		('Offset', 'AlternateSet', 'AlternateSetCount', 0, 'Array of offsets to AlternateSet tables-from beginning of Substitution table-ordered by Coverage Index'),
	]),

	('AlternateSet', [
		('uint16', 'GlyphCount', None, None, 'Number of GlyphIDs in the Alternate array'),
		('GlyphID', 'Alternate', 'GlyphCount', 0, 'Array of alternate GlyphIDs-in arbitrary order'),
	]),

	('LigatureSubstFormat1', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('uint16', 'LigSetCount', None, None, 'Number of LigatureSet tables'),
		('Offset', 'LigatureSet', 'LigSetCount', 0, 'Array of offsets to LigatureSet tables-from beginning of Substitution table-ordered by Coverage Index'),
	]),

	('LigatureSet', [
		('uint16', 'LigatureCount', None, None, 'Number of Ligature tables'),
		('Offset', 'Ligature', 'LigatureCount', 0, 'Array of offsets to Ligature tables-from beginning of LigatureSet table-ordered by preference'),
	]),

	('Ligature', [
		('GlyphID', 'LigGlyph', None, None, 'GlyphID of ligature to substitute'),
		('uint16', 'CompCount', None, None, 'Number of components in the ligature'),
		('GlyphID', 'Component', 'CompCount', -1, 'Array of component GlyphIDs-start with the second component-ordered in writing direction'),
	]),

	('SubstLookupRecord', [
		('uint16', 'SequenceIndex', None, None, 'Index into current glyph sequence-first glyph = 0'),
		('uint16', 'LookupListIndex', None, None, 'Lookup to apply to that position-zero-based'),
	]),

	('ContextSubstFormat1', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('uint16', 'SubRuleSetCount', None, None, 'Number of SubRuleSet tables-must equal GlyphCount in Coverage table'),
		('Offset', 'SubRuleSet', 'SubRuleSetCount', 0, 'Array of offsets to SubRuleSet tables-from beginning of Substitution table-ordered by Coverage Index'),
	]),

	('SubRuleSet', [
		('uint16', 'SubRuleCount', None, None, 'Number of SubRule tables'),
		('Offset', 'SubRule', 'SubRuleCount', 0, 'Array of offsets to SubRule tables-from beginning of SubRuleSet table-ordered by preference'),
	]),

	('SubRule', [
		('uint16', 'GlyphCount', None, None, 'Total number of glyphs in input glyph sequence-includes the first glyph'),
		('uint16', 'SubstCount', None, None, 'Number of SubstLookupRecords'),
		('GlyphID', 'Input', 'GlyphCount', -1, 'Array of input GlyphIDs-start with second glyph'),
		('struct', 'SubstLookupRecord', 'SubstCount', 0, 'Array of SubstLookupRecords-in design order'),
	]),

	('ContextSubstFormat2', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 2'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('Offset', 'ClassDef', None, None, 'Offset to glyph ClassDef table-from beginning of Substitution table'),
		('uint16', 'SubClassSetCount', None, None, 'Number of SubClassSet tables'),
		('Offset', 'SubClassSet', 'SubClassSetCount', 0, 'Array of offsets to SubClassSet tables-from beginning of Substitution table-ordered by class-may be NULL'),
	]),

	('SubClassSet', [
		('uint16', 'SubClassRuleCount', None, None, 'Number of SubClassRule tables'),
		('Offset', 'SubClassRule', 'SubClassRuleCount', 0, 'Array of offsets to SubClassRule tables-from beginning of SubClassSet-ordered by preference'),
	]),

	('SubClassRule', [
		('uint16', 'GlyphCount', None, None, 'Total number of classes specified for the context in the rule-includes the first class'),
		('uint16', 'SubstCount', None, None, 'Number of SubstLookupRecords'),
		('uint16', 'Class', 'GlyphCount', -1, 'Array of classes-beginning with the second class-to be matched to the input glyph class sequence'),
		('struct', 'SubstLookupRecord', 'SubstCount', 0, 'Array of Substitution lookups-in design order'),
	]),

	('ContextSubstFormat3', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 3'),
		('uint16', 'GlyphCount', None, None, 'Number of glyphs in the input glyph sequence'),
		('uint16', 'SubstCount', None, None, 'Number of SubstLookupRecords'),
		('Offset', 'Coverage', 'GlyphCount', 0, 'Array of offsets to Coverage table-from beginning of Substitution table-in glyph sequence order'),
		('struct', 'SubstLookupRecord', 'SubstCount', 0, 'Array of SubstLookupRecords-in design order'),
	]),

	('ChainContextSubstFormat1', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('uint16', 'ChainSubRuleSetCount', None, None, 'Number of ChainSubRuleSet tables-must equal GlyphCount in Coverage table'),
		('Offset', 'ChainSubRuleSet', 'ChainSubRuleSetCount', 0, 'Array of offsets to ChainSubRuleSet tables-from beginning of Substitution table-ordered by Coverage Index'),
	]),

	('ChainSubRuleSet', [
		('uint16', 'ChainSubRuleCount', None, None, 'Number of ChainSubRule tables'),
		('Offset', 'ChainSubRule', 'ChainSubRuleCount', 0, 'Array of offsets to ChainSubRule tables-from beginning of ChainSubRuleSet table-ordered by preference'),
	]),

	('ChainSubRule', [
		('uint16', 'BacktrackGlyphCount', None, None, 'Total number of glyphs in the backtrack sequence (number of glyphs to be matched before the first glyph)'),
		('GlyphID', 'Backtrack', 'BacktrackGlyphCount', 0, "Array of backtracking GlyphID's (to be matched before the input sequence)"),
		('uint16', 'InputGlyphCount', None, None, 'Total number of glyphs in the input sequence (includes the first glyph)'),
		('GlyphID', 'Input', 'InputGlyphCount', -1, 'Array of input GlyphIDs (start with second glyph)'),
		('uint16', 'LookAheadGlyphCount', None, None, 'Total number of glyphs in the look ahead sequence (number of glyphs to be matched after the input sequence)'),
		('GlyphID', 'LookAhead', 'LookAheadGlyphCount', 0, "Array of lookahead GlyphID's (to be matched after the input sequence)"),
		('uint16', 'SubstCount', None, None, 'Number of SubstLookupRecords'),
		('struct', 'SubstLookupRecord', 'SubstCount', 0, 'Array of SubstLookupRecords (in design order)'),
	]),

	('ChainContextSubstFormat2', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 2'),
		('Offset', 'Coverage', None, None, 'Offset to Coverage table-from beginning of Substitution table'),
		('Offset', 'BacktrackClassDef', None, None, 'Offset to glyph ClassDef table containing backtrack sequence data-from beginning of Substitution table'),
		('Offset', 'InputClassDef', None, None, 'Offset to glyph ClassDef table containing input sequence data-from beginning of Substitution table'),
		('Offset', 'LookAheadClassDef', None, None, 'Offset to glyph ClassDef table containing lookahead sequence data-from beginning of Substitution table'),
		('uint16', 'ChainSubClassSetCount', None, None, 'Number of ChainSubClassSet tables'),
		('Offset', 'ChainSubClassSet', 'ChainSubClassSetCount', 0, 'Array of offsets to ChainSubClassSet tables-from beginning of Substitution table-ordered by input class-may be NULL'),
	]),

	('ChainSubClassSet', [
		('uint16', 'ChainSubClassRuleCount', None, None, 'Number of ChainSubClassRule tables'),
		('Offset', 'ChainSubClassRule', 'ChainSubClassRuleCount', 0, 'Array of offsets to ChainSubClassRule tables-from beginning of ChainSubClassSet-ordered by preference'),
	]),

	('ChainSubClassRule', [
		('uint16', 'BacktrackGlyphCount', None, None, 'Total number of glyphs in the backtrack sequence (number of glyphs to be matched before the first glyph)'),
		('uint16', 'Backtrack', 'BacktrackGlyphCount', 0, 'Array of backtracking classes(to be matched before the input sequence)'),
		('uint16', 'InputGlyphCount', None, None, 'Total number of classes in the input sequence (includes the first class)'),
		('uint16', 'Input', 'InputGlyphCount', -1, 'Array of input classes(start with second class; to be matched with the input glyph sequence)'),
		('uint16', 'LookAheadGlyphCount', None, None, 'Total number of classes in the look ahead sequence (number of classes to be matched after the input sequence)'),
		('uint16', 'LookAhead', 'LookAheadGlyphCount', 0, 'Array of lookahead classes(to be matched after the input sequence)'),
		('uint16', 'SubstCount', None, None, 'Number of SubstLookupRecords'),
		('struct', 'SubstLookupRecord', 'SubstCount', 0, 'Array of SubstLookupRecords (in design order)'),
	]),

	('ChainContextSubstFormat3', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 3'),
		('uint16', 'BacktrackGlyphCount', None, None, 'Number of glyphs in the backtracking sequence'),
		('Offset', 'BacktrackCoverage', 'BacktrackGlyphCount', 0, 'Array of offsets to coverage tables in backtracking sequence, in glyph sequence order'),
		('uint16', 'InputGlyphCount', None, None, 'Number of glyphs in input sequence'),
		('Offset', 'InputCoverage', 'InputGlyphCount', 0, 'Array of offsets to coverage tables in input sequence, in glyph sequence order'),
		('uint16', 'LookAheadGlyphCount', None, None, 'Number of glyphs in lookahead sequence'),
		('Offset', 'LookAheadCoverage', 'LookAheadGlyphCount', 0, 'Array of offsets to coverage tables in lookahead sequence, in glyph sequence order'),
		('uint16', 'SubstCount', None, None, 'Number of SubstLookupRecords'),
		('struct', 'SubstLookupRecord', 'SubstCount', 0, 'Array of SubstLookupRecords, in design order'),
	]),

	('ExtensionSubstFormat1', [
		('USHORT', 'ExtFormat', None, None, 'Format identifier. Set to 1.'),
		('USHORT', 'ExtensionLookupType', None, None, 'Lookup type of subtable referenced by ExtensionOffset (i.e. the extension subtable).'),
		('LOffset', 'ExtSubTable', None, None, 'Array of offsets to Lookup tables-from beginning of LookupList -zero based (first lookup is Lookup index = 0)'),
	]),

	('ReverseChainSingleSubstFormat1', [
		('uint16', 'SubstFormat', None, None, 'Format identifier-format = 1'),
		('Offset', 'Coverage', None, 0, 'Offset to Coverage table - from beginning of Substitution table'),
		('uint16', 'BacktrackGlyphCount', None, None, 'Number of glyphs in the backtracking sequence'),
		('Offset', 'BacktrackCoverage', 'BacktrackGlyphCount', 0, 'Array of offsets to coverage tables in backtracking sequence, in glyph sequence order'),
		('uint16', 'LookAheadGlyphCount', None, None, 'Number of glyphs in lookahead sequence'),
		('Offset', 'LookAheadCoverage', 'LookAheadGlyphCount', 0, 'Array of offsets to coverage tables in lookahead sequence, in glyph sequence order'),
		('uint16', 'GlyphCount', None, None, 'Number of GlyphIDs in the Substitute array'),
		('GlyphID', 'Substitute', 'GlyphCount', 0, 'Array of substitute GlyphIDs-ordered by Coverage index'),
	]),

	#
	# gdef (generated from gdef.htm)
	#

	('GDEF', [
		('Fixed', 'Version', None, None, 'Version of the GDEF table-initially 0x00010000'),
		('Offset', 'GlyphClassDef', None, None, 'Offset to class definition table for glyph type-from beginning of GDEF header (may be NULL)'),
		('Offset', 'AttachList', None, None, 'Offset to list of glyphs with attachment points-from beginning of GDEF header (may be NULL)'),
		('Offset', 'LigCaretList', None, None, 'Offset to list of positioning points for ligature carets-from beginning of GDEF header (may be NULL)'),
		('Offset', 'MarkAttachClassDef', None, None, 'Offset to class definition table for mark attachment type-from beginning of GDEF header (may be NULL)'),
	]),

	('AttachList', [
		('Offset', 'Coverage', None, None, 'Offset to Coverage table - from beginning of AttachList table'),
		('uint16', 'GlyphCount', None, None, 'Number of glyphs with attachment points'),
		('Offset', 'AttachPoint', 'GlyphCount', 0, 'Array of offsets to AttachPoint tables-from beginning of AttachList table-in Coverage Index order'),
	]),

	('AttachPoint', [
		('uint16', 'PointCount', None, None, 'Number of attachment points on this glyph'),
		('uint16', 'PointIndex', 'PointCount', 0, 'Array of contour point indices -in increasing numerical order'),
	]),

	('LigCaretList', [
		('Offset', 'Coverage', None, None, 'Offset to Coverage table - from beginning of LigCaretList table'),
		('uint16', 'LigGlyphCount', None, None, 'Number of ligature glyphs'),
		('Offset', 'LigGlyph', 'LigGlyphCount', 0, 'Array of offsets to LigGlyph tables-from beginning of LigCaretList table-in Coverage Index order'),
	]),

	('LigGlyph', [
		('uint16', 'CaretCount', None, None, 'Number of CaretValues for this ligature (components - 1)'),
		('Offset', 'CaretValue', 'CaretCount', 0, 'Array of offsets to CaretValue tables-from beginning of LigGlyph table-in increasing coordinate order'),
	]),

	('CaretValueFormat1', [
		('uint16', 'CaretValueFormat', None, None, 'Format identifier-format = 1'),
		('int16', 'Coordinate', None, None, 'X or Y value, in design units'),
	]),

	('CaretValueFormat2', [
		('uint16', 'CaretValueFormat', None, None, 'Format identifier-format = 2'),
		('uint16', 'CaretValuePoint', None, None, 'Contour point index on glyph'),
	]),

	('CaretValueFormat3', [
		('uint16', 'CaretValueFormat', None, None, 'Format identifier-format = 3'),
		('int16', 'Coordinate', None, None, 'X or Y value, in design units'),
		('Offset', 'DeviceTable', None, None, 'Offset to Device table for X or Y value-from beginning of CaretValue table'),
	]),


	#
	# base (generated from base.htm)
	#

	('BASE', [
		('fixed32', 'Version', None, None, 'Version of the BASE table-initially 0x00010000'),
		('Offset', 'HorizAxis', None, None, 'Offset to horizontal Axis table-from beginning of BASE table-may be NULL'),
		('Offset', 'VertAxis', None, None, 'Offset to vertical Axis table-from beginning of BASE table-may be NULL'),
	]),

	('Axis', [
		('Offset', 'BaseTagList', None, None, 'Offset to BaseTagList table-from beginning of Axis table-may be NULL'),
		('Offset', 'BaseScriptList', None, None, 'Offset to BaseScriptList table-from beginning of Axis table'),
	]),

	('BaseTagList', [
		('uint16', 'BaseTagCount', None, None, 'Number of baseline identification tags in this text direction-may be zero (0)'),
		('Tag', 'BaselineTag', 'BaseTagCount', 0, 'Array of 4-byte baseline identification tags-must be in alphabetical order'),
	]),

	('BaseScriptList', [
		('uint16', 'BaseScriptCount', None, None, 'Number of BaseScriptRecords defined'),
		('struct', 'BaseScriptRecord', 'BaseScriptCount', 0, 'Array of BaseScriptRecords-in alphabetical order by BaseScriptTag'),
	]),

	('BaseScriptRecord', [
		('Tag', 'BaseScriptTag', None, None, '4-byte script identification tag'),
		('Offset', 'BaseScript', None, None, 'Offset to BaseScript table-from beginning of BaseScriptList'),
	]),

	('BaseScript', [
		('Offset', 'BaseValues', None, None, 'Offset to BaseValues table-from beginning of BaseScript table-may be NULL'),
		('Offset', 'DefaultMinMax', None, None, 'Offset to MinMax table- from beginning of BaseScript table-may be NULL'),
		('uint16', 'BaseLangSysCount', None, None, 'Number of BaseLangSysRecords defined-may be zero (0)'),
		('struct', 'BaseLangSysRecord', 'BaseLangSysCount', 0, 'Array of BaseLangSysRecords-in alphabetical order by BaseLangSysTag'),
	]),

	('BaseLangSysRecord', [
		('Tag', 'BaseLangSysTag', None, None, '4-byte language system identification tag'),
		('Offset', 'MinMax', None, None, 'Offset to MinMax table-from beginning of BaseScript table'),
	]),

	('BaseValues', [
		('uint16', 'DefaultIndex', None, None, 'Index number of default baseline for this script-equals index position of baseline tag in BaselineArray of the BaseTagList'),
		('uint16', 'BaseCoordCount', None, None, 'Number of BaseCoord tables defined-should equal BaseTagCount in the BaseTagList'),
		('Offset', 'BaseCoord', 'BaseCoordCount', 0, 'Array of offsets to BaseCoord-from beginning of BaseValues table-order matches BaselineTag array in the BaseTagList'),
	]),

	('MinMax', [
		('Offset', 'MinCoord', None, None, 'Offset to BaseCoord table-defines minimum extent value-from the beginning of MinMax table-may be NULL'),
		('Offset', 'MaxCoord', None, None, 'Offset to BaseCoord table-defines maximum extent value-from the beginning of MinMax table-may be NULL'),
		('uint16', 'FeatMinMaxCount', None, None, 'Number of FeatMinMaxRecords-may be zero (0)'),
		('struct', 'FeatMinMaxRecord', 'FeatMinMaxCount', 0, 'Array of FeatMinMaxRecords-in alphabetical order, by FeatureTableTag'),
	]),

	('FeatMinMaxRecord', [
		('Tag', 'FeatureTableTag', None, None, '4-byte feature identification tag-must match FeatureTag in FeatureList'),
		('Offset', 'MinCoord', None, None, 'Offset to BaseCoord table-defines minimum extent value-from beginning of MinMax table-may be NULL'),
		('Offset', 'MaxCoord', None, None, 'Offset to BaseCoord table-defines maximum extent value-from beginning of MinMax table-may be NULL'),
	]),

	('BaseCoordFormat1', [
		('uint16', 'BaseCoordFormat', None, None, 'Format identifier-format = 1'),
		('int16', 'Coordinate', None, None, 'X or Y value, in design units'),
	]),

	('BaseCoordFormat2', [
		('uint16', 'BaseCoordFormat', None, None, 'Format identifier-format = 2'),
		('int16', 'Coordinate', None, None, 'X or Y value, in design units'),
		('GlyphID', 'ReferenceGlyph', None, None, 'GlyphID of control glyph'),
		('uint16', 'BaseCoordPoint', None, None, 'Index of contour point on the ReferenceGlyph'),
	]),

	('BaseCoordFormat3', [
		('uint16', 'BaseCoordFormat', None, None, 'Format identifier-format = 3'),
		('int16', 'Coordinate', None, None, 'X or Y value, in design units'),
		('Offset', 'DeviceTable', None, None, 'Offset to Device table for X or Y value'),
	]),


	#
	# jstf (generated from jstf.htm)
	#

	('JSTF', [
		('fixed32', 'Version', None, None, 'Version of the JSTF table-initially set to 0x00010000'),
		('uint16', 'JstfScriptCount', None, None, 'Number of JstfScriptRecords in this table'),
		('struct', 'JstfScriptRecord', 'JstfScriptCount', 0, 'Array of JstfScriptRecords-in alphabetical order, by JstfScriptTag'),
	]),

	('JstfScriptRecord', [
		('Tag', 'JstfScriptTag', None, None, '4-byte JstfScript identification'),
		('Offset', 'JstfScript', None, None, 'Offset to JstfScript table-from beginning of JSTF Header'),
	]),

	('JstfScript', [
		('Offset', 'ExtenderGlyph', None, None, 'Offset to ExtenderGlyph table-from beginning of JstfScript table-may be NULL'),
		('Offset', 'DefJstfLangSys', None, None, 'Offset to Default JstfLangSys table-from beginning of JstfScript table-may be NULL'),
		('uint16', 'JstfLangSysCount', None, None, 'Number of JstfLangSysRecords in this table- may be zero (0)'),
		('struct', 'JstfLangSysRecord', 'JstfLangSysCount', 0, 'Array of JstfLangSysRecords-in alphabetical order, by JstfLangSysTag'),
	]),

	('JstfLangSysRecord', [
		('Tag', 'JstfLangSysTag', None, None, '4-byte JstfLangSys identifier'),
		('Offset', 'JstfLangSys', None, None, 'Offset to JstfLangSys table-from beginning of JstfScript table'),
	]),

	('ExtenderGlyph', [
		('uint16', 'GlyphCount', None, None, 'Number of Extender Glyphs in this script'),
		('GlyphID', 'ExtenderGlyph', 'GlyphCount', 0, 'GlyphIDs-in increasing numerical order'),
	]),

	('JstfLangSys', [
		('uint16', 'JstfPriorityCount', None, None, 'Number of JstfPriority tables'),
		('Offset', 'JstfPriority', 'JstfPriorityCount', 0, 'Array of offsets to JstfPriority tables-from beginning of JstfLangSys table-in priority order'),
	]),

	('JstfPriority', [
		('Offset', 'ShrinkageEnableGSUB', None, None, 'Offset to Shrinkage Enable JstfGSUBModList table-from beginning of JstfPriority table-may be NULL'),
		('Offset', 'ShrinkageDisableGSUB', None, None, 'Offset to Shrinkage Disable JstfGSUBModList table-from beginning of JstfPriority table-may be NULL'),
		('Offset', 'ShrinkageEnableGPOS', None, None, 'Offset to Shrinkage Enable JstfGPOSModList table-from beginning of JstfPriority table-may be NULL'),
		('Offset', 'ShrinkageDisableGPOS', None, None, 'Offset to Shrinkage Disable JstfGPOSModList table-from beginning of JstfPriority table-may be NULL'),
		('Offset', 'ShrinkageJstfMax', None, None, 'Offset to Shrinkage JstfMax table-from beginning of JstfPriority table -may be NULL'),
		('Offset', 'ExtensionEnableGSUB', None, None, 'Offset to Extension Enable JstfGSUBModList table-may be NULL'),
		('Offset', 'ExtensionDisableGSUB', None, None, 'Offset to Extension Disable JstfGSUBModList table-from beginning of JstfPriority table-may be NULL'),
		('Offset', 'ExtensionEnableGPOS', None, None, 'Offset to Extension Enable JstfGSUBModList table-may be NULL'),
		('Offset', 'ExtensionDisableGPOS', None, None, 'Offset to Extension Disable JstfGSUBModList table-from beginning of JstfPriority table-may be NULL'),
		('Offset', 'ExtensionJstfMax', None, None, 'Offset to Extension JstfMax table-from beginning of JstfPriority table -may be NULL'),
	]),

	('JstfGSUBModList', [
		('uint16', 'LookupCount', None, None, 'Number of lookups for this modification'),
		('uint16', 'GSUBLookupIndex', 'LookupCount', 0, 'Array of LookupIndex identifiers in GSUB-in increasing numerical order'),
	]),

	('JstfGPOSModList', [
		('uint16', 'LookupCount', None, None, 'Number of lookups for this modification'),
		('uint16', 'GPOSLookupIndex', 'LookupCount', 0, 'Array of LookupIndex identifiers in GPOS-in increasing numerical order'),
	]),

	('JstfMax', [
		('uint16', 'LookupCount', None, None, 'Number of lookup Indices for this modification'),
		('Offset', 'Lookup', 'LookupCount', 0, 'Array of offsets to GPOS-type lookup tables-from beginning of JstfMax table-in design order'),
	]),

]

