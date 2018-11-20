import os
from fontTools.misc.py23 import BytesIO
from fontTools.cffLib import (TopDictIndex,
							  buildOrder,
							  topDictOperators,
							  topDictOperators2,
							  privateDictOperators,
							  privateDictOperators2,
							  FDArrayIndex,
							  FontDict,
							  VarStoreData)
from fontTools.cffLib.cff2mergePen import CFF2CharStringMergePen
from fontTools.ttLib import newTable
from fontTools import varLib
from fontTools.varLib.models import allEqual


def addCFFVarStore(varFont, varModel):
	supports = varModel.supports[1:]
	fvarTable = varFont['fvar']
	axisKeys = [axis.axisTag for axis in fvarTable.axes]
	varTupleList = varLib.builder.buildVarRegionList(supports, axisKeys)
	varTupleIndexes = list(range(len(supports)))
	varDeltasCFFV = varLib.builder.buildVarData(varTupleIndexes, None, False)
	varStoreCFFV = varLib.builder.buildVarStore(varTupleList, [varDeltasCFFV])

	topDict = varFont['CFF2'].cff.topDictIndex[0]
	topDict.VarStore = VarStoreData(otVarStore=varStoreCFFV)


def lib_convertCFFToCFF2(cff, otFont):
	# This assumes a decompiled CFF table.
	cff2GetGlyphOrder = cff.otFont.getGlyphOrder
	topDictData = TopDictIndex(None, cff2GetGlyphOrder, None)
	topDictData.items = cff.topDictIndex.items
	cff.topDictIndex = topDictData
	topDict = topDictData[0]
	if hasattr(topDict, 'Private'):
		privateDict = topDict.Private
	else:
		privateDict = None
	opOrder = buildOrder(topDictOperators2)
	topDict.order = opOrder
	topDict.cff2GetGlyphOrder = cff2GetGlyphOrder
	if not hasattr(topDict, "FDArray"):
		fdArray = topDict.FDArray = FDArrayIndex()
		fdArray.strings = None
		fdArray.GlobalSubrs = topDict.GlobalSubrs
		topDict.GlobalSubrs.fdArray = fdArray
		charStrings = topDict.CharStrings
		if charStrings.charStringsAreIndexed:
			charStrings.charStringsIndex.fdArray = fdArray
		else:
			charStrings.fdArray = fdArray
		fontDict = FontDict()
		fontDict.setCFF2(True)
		fdArray.append(fontDict)
		fontDict.Private = privateDict
		privateOpOrder = buildOrder(privateDictOperators2)
		for entry in privateDictOperators:
			key = entry[1]
			if key not in privateOpOrder:
				if key in privateDict.rawDict:
					# print "Removing private dict", key
					del privateDict.rawDict[key]
				if hasattr(privateDict, key):
					delattr(privateDict, key)
					# print "Removing privateDict attr", key
	else:
		# clean up the PrivateDicts in the fdArray
		fdArray = topDict.FDArray
		privateOpOrder = buildOrder(privateDictOperators2)
		for fontDict in fdArray:
			fontDict.setCFF2(True)
			for key in fontDict.rawDict.keys():
				if key not in fontDict.order:
					del fontDict.rawDict[key]
					if hasattr(fontDict, key):
						delattr(fontDict, key)

			privateDict = fontDict.Private
			for entry in privateDictOperators:
				key = entry[1]
				if key not in privateOpOrder:
					if key in privateDict.rawDict:
						# print "Removing private dict", key
						del privateDict.rawDict[key]
					if hasattr(privateDict, key):
						delattr(privateDict, key)
						# print "Removing privateDict attr", key
	# Now delete up the decrecated topDict operators from CFF 1.0
	for entry in topDictOperators:
		key = entry[1]
		if key not in opOrder:
			if key in topDict.rawDict:
				del topDict.rawDict[key]
			if hasattr(topDict, key):
				delattr(topDict, key)

	# At this point, the Subrs and Charstrings are all still T2Charstring class
	# easiest to fix this by compiling, then decompiling again
	cff.major = 2
	file = BytesIO()
	cff.compile(file, otFont, isCFF2=True)
	file.seek(0)
	cff.decompile(file, otFont, isCFF2=True)


def convertCFFtoCFF2(varFont):
	# Convert base font to a single master CFF2 font.
	cffTable = varFont['CFF ']
	lib_convertCFFToCFF2(cffTable.cff, varFont)
	newCFF2 = newTable("CFF2")
	newCFF2.cff = cffTable.cff
	varFont['CFF2'] = newCFF2
	del varFont['CFF ']


class MergeDictError(TypeError):
	def __init__(self, key, value, values):
		error_msg = ["For the Private Dict key '{}', ".format(key),
					 "the default font value list:",
					 "\t{}".format(value),
					 "had a different number of values than a region font:"]
		error_msg += ["\t{}".format(region_value) for region_value in values]
		error_msg = os.linesep.join(error_msg)


def conv_to_int(num):
	if num % 1 == 0:
		return int(num)
	return num


pd_blend_fields = ("BlueValues", "OtherBlues", "FamilyBlues",
				   "FamilyOtherBlues", "BlueScale", "BlueShift",
				   "BlueFuzz", "StdHW", "StdVW", "StemSnapH",
				   "StemSnapV")


def merge_PrivateDicts(topDict, region_top_dicts, num_masters, var_model):
	if hasattr(region_top_dicts[0], 'FDArray'):
		regionFDArrays = [fdTopDict.FDArray for fdTopDict in region_top_dicts]
	else:
		regionFDArrays = [[fdTopDict] for fdTopDict in region_top_dicts]
	for fd_index, font_dict in enumerate(topDict.FDArray):
		private_dict = font_dict.Private
		pds = [private_dict] + [
			regionFDArray[fd_index].Private for regionFDArray in regionFDArrays
			]
		for key, value in private_dict.rawDict.items():
			if key not in pd_blend_fields:
				continue
			if isinstance(value, list):
				try:
					values = [pd.rawDict[key] for pd in pds]
				except KeyError:
					del private_dict.rawDict[key]
					print(
						b"Warning: {key} in default font Private dict is "
						b"missing from another font, and was "
						b"discarded.".format(key=key))
					continue
				try:
					values = zip(*values)
				except IndexError:
					raise MergeDictError(key, value, values)
				"""
				Row 0 contains the first  value from each master.
				Convert each row from absolute values to relative
				values from the previous row.
				e.g for three masters,	a list of values was:
				master 0 OtherBlues = [-217,-205]
				master 1 OtherBlues = [-234,-222]
				master 1 OtherBlues = [-188,-176]
				The call to zip() converts this to:
				[(-217, -234, -188), (-205, -222, -176)]
				and is converted finally to:
				OtherBlues = [[-217, 17.0, 46.0], [-205, 0.0, 0.0]]
				"""
				dataList = []
				prev_val_list = [0] * num_masters
				any_points_differ = False
				for val_list in values:
					rel_list = [(val - prev_val_list[i]) for (
							i, val) in enumerate(val_list)]
					if (not any_points_differ) and not allEqual(rel_list):
						any_points_differ = True
					prev_val_list = val_list
					deltas = var_model.getDeltas(rel_list)
					# Convert numbers with no decimal part to an int.
					deltas = [conv_to_int(delta) for delta in deltas]
					# For PrivateDict BlueValues, the default font
					# values are absolute, not relative to the prior value.
					deltas[0] = val_list[0]
					dataList.append(deltas)
				# If there are no blend values,then
				# we can collapse the blend lists.
				if not any_points_differ:
					dataList = [data[0] for data in dataList]
			else:
				values = [pd.rawDict[key] for pd in pds]
				if not allEqual(values):
					dataList = var_model.getDeltas(values)
				else:
					dataList = values[0]
			private_dict.rawDict[key] = dataList


def merge_region_fonts(varFont, model, ordered_fonts_list, glyphOrder):
	topDict = varFont['CFF2'].cff.topDictIndex[0]
	default_charstrings = topDict.CharStrings
	region_fonts = ordered_fonts_list[1:]
	region_top_dicts = [
			ttFont['CFF '].cff.topDictIndex[0] for ttFont in region_fonts
				]
	num_masters = len(model.mapping)
	merge_PrivateDicts(topDict, region_top_dicts, num_masters, model)
	merge_charstrings(default_charstrings,
					  glyphOrder,
					  num_masters,
					  region_top_dicts, model)


def merge_charstrings(default_charstrings,
					  glyphOrder,
					  num_masters,
					  region_top_dicts,
					  var_model):
	for gname in glyphOrder:
		default_charstring = default_charstrings[gname]
		var_pen = CFF2CharStringMergePen([], gname, num_masters, 0)
		default_charstring.draw(var_pen)
		for region_idx, region_td in enumerate(region_top_dicts, start=1):
			region_charstrings = region_td.CharStrings
			region_charstring = region_charstrings[gname]
			var_pen.restart(region_idx)
			region_charstring.draw(var_pen)
		new_charstring = var_pen.getCharString(
			private=default_charstring.private,
			globalSubrs=default_charstring.globalSubrs,
			var_model=var_model, optimize=True)
		default_charstrings[gname] = new_charstring
