# Copyright 2021 Behdad Esfahbod. All Rights Reserved.

from fontTools import ttLib
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables import otTables
from fontTools.merge.base import add_method, mergeObjects
from fontTools.merge.util import *
import logging


log = logging.getLogger("fontTools.merge")


ttLib.getTableClass('COLR').mergeMap = {
	'version': max,
	'tableTag': onlyExisting(equal), # XXX clean me up
	'table': mergeObjects,
}

otTables.COLR.mergeMap = {
	'Version': max,
	'BaseGlyphRecordCount': sum,
	'BaseGlyphRecordArray': sum,
	'LayerRecordArray': sum,
	'LayerRecordCount': sum,
	'BaseGlyphList': sum,
	'LayerList': sum,
	'ClipList': sum,
	'VarIndexMap': NotImplemented,
    'VarStore': NotImplemented,
}
