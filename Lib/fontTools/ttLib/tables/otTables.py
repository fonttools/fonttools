"""fontTools.ttLib.tables.otTables -- A collection of classes representing the various
OpenType subtables.

Most are constructed upon import from data in otData.py. Most smartness is contained
in otBase.BaseTable.
"""

from otBase import BaseTable, FormatSwitchingBaseTable


class LookupOrder(BaseTable):
	"""Dummy class; this table isn't defined, but is used, and is always NULL."""

class FeatureParams(BaseTable):
	"""Dummy class; this table isn't defined, but is used, and is always NULL."""


_equivalents = [
	('MarkArray', ("Mark1Array",)),
	('LangSys', ('DefaultLangSys',)),
	('Coverage', ('MarkCoverage', 'BaseCoverage', 'LigatureCoverage', 'Mark1Coverage',
			'Mark2Coverage', 'BacktrackCoverage', 'InputCoverage',
			'LookaheadCoverage')),
	('ClassDef', ('ClassDef1', 'ClassDef2', 'BacktrackClassDef', 'InputClassDef',
			'LookaheadClassDef', 'GlyphClassDef', 'MarkAttachClassDef')),
	('Anchor', ('EntryAnchor', 'ExitAnchor', 'BaseAnchor', 'LigatureAnchor',
			'Mark2Anchor', 'MarkAnchor')),
	('Device', ('XPlaDevice', 'YPlaDevice', 'XAdvDevice', 'YAdvDevice',
			'XDeviceTable', 'YDeviceTable', 'DeviceTable')),
	('Axis', ('HorizAxis', 'VertAxis',)),
	('MinMax', ('DefaultMinMax',)),
	('BaseCoord', ('MinCoord', 'MaxCoord',)),
	('JstfLangSys', ('DefJstfLangSys',)),
	('JstfGSUBModList', ('ShrinkageEnableGSUB', 'ShrinkageDisableGSUB', 'ExtensionEnableGSUB',
			'ExtensionDisableGSUB',)),
	('JstfGPOSModList', ('ShrinkageEnableGPOS', 'ShrinkageDisableGPOS', 'ExtensionEnableGPOS',
			'ExtensionDisableGPOS',)),
	('JstfMax', ('ShrinkageJstfMax', 'ExtensionJstfMax',)),
]


def _buildClasses():
	import new, re
	from otData import otData
	
	formatPat = re.compile("([A-Za-z0-9]+)Format(\d+)$")
	namespace = globals()
	
	# populate module with classes
	for name, table in otData:
		baseClass = BaseTable
		m = formatPat.match(name)
		if m:
			# XxxFormatN subtable, we only add the "base" table
			name = m.group(1)
			baseClass = FormatSwitchingBaseTable
		if not namespace.has_key(name):
			cls = new.classobj(name, (baseClass,), {})
			namespace[name] = cls
	
	for base, alts in _equivalents:
		base = namespace[base]
		for alt in alts:
			namespace[alt] = new.classobj(alt, (base,), {})
	
	global lookupTypes
	lookupTypes = {
		'GSUB': {
			1: SingleSubst,
			2: MultipleSubst,
			3: AlternateSubst,
			4: LigatureSubst,
			5: ContextSubst,
			6: ChainContextSubst,
			7: ExtensionSubst,
		},
		'GPOS': {
			1: SinglePos,
			2: PairPos,
			3: CursivePos,
			4: MarkBasePos,
			5: MarkLigPos,
			6: MarkMarkPos,
			7: ContextPos,
			8: ChainContextPos,
			9: ExtensionPos,
		},
	}
	lookupTypes['JSTF'] = lookupTypes['GPOS']  # JSTF contains GPOS
	
	# add converters to classes
	from otConverters import buildConverterList
	for name, table in otData:
		m = formatPat.match(name)
		if m:
			# XxxFormatN subtable, add converter to "base" table
			name, format = m.groups()
			format = int(format)
			cls = namespace[name]
			if not hasattr(cls, "converters"):
				cls.converters = {}
				cls.convertersByName = {}
			converters, convertersByName = buildConverterList(table[1:], namespace)
			cls.converters[format] = converters
			cls.convertersByName[format] = convertersByName
		else:
			cls = namespace[name]
			cls.converters, cls.convertersByName = buildConverterList(table, namespace)


_buildClasses()
