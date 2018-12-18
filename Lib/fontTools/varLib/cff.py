import os
from fontTools.misc.py23 import BytesIO
from fontTools.misc.psCharStrings import T2CharString, T2OutlineExtractor
from fontTools.pens.t2CharStringPen import T2CharStringPen, t2c_round
from fontTools.cffLib import (
	maxStackLimit,
	TopDictIndex,
	buildOrder,
	topDictOperators,
	topDictOperators2,
	privateDictOperators,
	privateDictOperators2,
	FDArrayIndex,
	FontDict,
	VarStoreData
)
from fontTools.cffLib.specializer import (commandsToProgram, specializeCommands)
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
			for key in list(fontDict.rawDict.keys()):
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
		default_charstring.outlineExtractor = CFFToCFF2OutlineExtractor
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


class MergeTypeError(TypeError):
	def __init__(self, point_type, pt_index, m_index, default_type, glyphName):
		self.error_msg = [
					"In glyph '{gname}' "
					"'{point_type}' at point index {pt_index} in master "
					"index {m_index} differs from the default font point "
					"type '{default_type}'"
					"".format(gname=glyphName,
							  point_type=point_type, pt_index=pt_index,
							  m_index=m_index, default_type=default_type)
					][0]
		super(MergeTypeError, self).__init__(self.error_msg)


def makeRoundNumberFunc(tolerance):
	if tolerance < 0:
		raise ValueError("Rounding tolerance must be positive")

	def roundNumber(val):
		return t2c_round(val, tolerance)

	return roundNumber


class CFFToCFF2OutlineExtractor(T2OutlineExtractor):
	""" This class is used to remove the initial width
	from the CFF charstring without adding the width
	to self.nominalWidthX, which is None.
	"""
	def popallWidth(self, evenOdd=0):
		args = self.popall()
		if not self.gotWidth:
			if evenOdd ^ (len(args) % 2):
				args = args[1:]
			self.width = self.defaultWidthX
			self.gotWidth = 1
		return args


class CFF2CharStringMergePen(T2CharStringPen):
	"""Pen to merge Type 2 CharStrings.
	"""
	def __init__(self, default_commands,
				 glyphName, num_masters, master_idx, roundTolerance=0.5):
		super(
			CFF2CharStringMergePen,
			self).__init__(width=None,
						   glyphSet=None, CFF2=True,
						   roundTolerance=roundTolerance)
		self.pt_index = 0
		self._commands = default_commands
		self.m_index = master_idx
		self.num_masters = num_masters
		self.prev_move_idx = 0
		self.glyphName = glyphName
		self.roundNumber = makeRoundNumberFunc(roundTolerance)

	def _p(self, pt):
		""" Unlike T2CharstringPen, this class stores absolute values.
		This is to allow the logic in check_and_fix_closepath() to work,
		where the current or previous absolute point has to be compared to
		the path start-point.
		"""
		self._p0 = pt
		return list(self._p0)

	def add_point(self, point_type, pt_coords):
		if self.m_index == 0:
			self._commands.append([point_type, [pt_coords]])
		else:
			cmd = self._commands[self.pt_index]
			if cmd[0] != point_type:
				# Fix some issues that show up in some
				# CFF workflows, even when fonts are
				# topologically merge compatible.
				success, pt_coords = self.check_and_fix_flat_curve(
							cmd, point_type, pt_coords)
				if not success:
					success = self.check_and_fix_closepath(
							cmd, point_type, pt_coords)
					if success:
						# We may have incremented self.pt_index
						cmd = self._commands[self.pt_index]
						if cmd[0] != point_type:
							success = False
					if not success:
						raise MergeTypeError(point_type,
											 self.pt_index, len(cmd[1]),
											 cmd[0], self.glyphName)
			cmd[1].append(pt_coords)
		self.pt_index += 1

	def _moveTo(self, pt):
		pt_coords = self._p(pt)
		self.add_point('rmoveto', pt_coords)
		# I set prev_move_idx here because add_point()
		# can change self.pt_index.
		self.prev_move_idx = self.pt_index - 1

	def _lineTo(self, pt):
		pt_coords = self._p(pt)
		self.add_point('rlineto', pt_coords)

	def _curveToOne(self, pt1, pt2, pt3):
		_p = self._p
		pt_coords = _p(pt1)+_p(pt2)+_p(pt3)
		self.add_point('rrcurveto', pt_coords)

	def _closePath(self):
		pass

	def _endPath(self):
		pass

	def restart(self, region_idx):
		self.pt_index = 0
		self.m_index = region_idx
		self._p0 = (0, 0)

	def getCommands(self):
		return self._commands

	def reorder_blend_args(self, commands):
		"""
		We first re-order the master coordinate values.
		For a moveto to lineto, the args are now arranged as:
			[ [master_0 x,y], [master_1 x,y], [master_2 x,y] ]
		We re-arrange this to
		[	[master_0 x, master_1 x, master_2 x],
			[master_0 y, master_1 y, master_2 y]
		]
		We also make the value relative.
		If the master values are all the same, we collapse the list to
		as single value instead of a list.
		"""
		for cmd in commands:
			# arg[i] is the set of arguments for this operator from master i.
			args = cmd[1]
			m_args = zip(*args)
			# m_args[n] is now all num_master args for the i'th argument
			# for this operation.
			cmd[1] = m_args

		# Now convert from absolute to relative
		x0 = [0]*self.num_masters
		y0 = [0]*self.num_masters
		for cmd in self._commands:
			is_x = True
			coords = cmd[1]
			rel_coords = []
			for coord in coords:
				prev_coord = x0 if is_x else y0
				rel_coord = [pt[0] - pt[1] for pt in zip(coord, prev_coord)]

				if allEqual(rel_coord):
					rel_coord = rel_coord[0]
				rel_coords.append(rel_coord)
				if is_x:
					x0 = coord
				else:
					y0 = coord
				is_x = not is_x
			cmd[1] = rel_coords
		return commands

	@staticmethod
	def mergeCommandsToProgram(commands, var_model, round_func):
		"""
		Takes a commands list as returned by programToCommands() and
		converts it back to a T2CharString or CFF2Charstring program list. I
		need to use this rather than specialize.commandsToProgram, as the
		commands produced by CFF2CharStringMergePen initially contains a
		list of coordinate values, one for each master, wherever a single
		coordinate value is expected by the regular logic. The problem with
		doing using the specialize.py functions is that a commands list is
		expected to be a op name with its associated argument list. For the
		commands list here, some of the arguments may need to be converted
		to a new argument list and opcode.
		This version will convert each list of master arguments to a blend
		op and its arguments, and will also combine successive blend ops up
		to the stack limit.
		"""
		program = []
		for op, args in commands:
			num_args = len(args)
			# some of the args may be blend lists, and some may be
			# single coordinate values.
			i = 0
			stack_use = 0
			while i < num_args:
				arg = args[i]
				if not isinstance(arg, list):
					program.append(arg)
					i += 1
					stack_use += 1
				else:
					prev_stack_use = stack_use
					""" The arg is a tuple of blend values.
					These are each (master 0,master 1..master n)
					Combine as many successive tuples as we can,
					up to the max stack limit.
					"""
					num_masters = len(arg)
					blendlist = [arg]
					i += 1
					stack_use += 1 + num_masters  # 1 for the num_blends arg
					while (i < num_args) and isinstance(args[i], list):
						blendlist.append(args[i])
						i += 1
						stack_use += num_masters
						if stack_use + num_masters > maxStackLimit:
							# if we are here, max stack is is the CFF2 max stack.
							break
					num_blends = len(blendlist)
					# append the 'num_blends' default font values
					for arg in blendlist:
						if round_func:
							arg[0] = round_func(arg[0])
						program.append(arg[0])
					for arg in blendlist:
						# for each coordinate tuple, append the region deltas
						if len(arg) != 3:
							print(arg)
							import pdb
							pdb.set_trace()
						deltas = var_model.getDeltas(arg)
						if round_func:
							deltas = [round_func(delta) for delta in deltas]
						# First item in 'deltas' is the default master value;
						# for CFF2 data, that has already been written.
						program.extend(deltas[1:])
					program.append(num_blends)
					program.append('blend')
					stack_use = prev_stack_use + num_blends
			if op:
				program.append(op)
		return program


	def getCharString(self, private=None, globalSubrs=None,
					  var_model=None, optimize=True):
		commands = self._commands
		commands = self.reorder_blend_args(commands)
		if optimize:
			commands = specializeCommands(commands, generalizeFirst=False,
										  maxstack=maxStackLimit)
		program = self.mergeCommandsToProgram(commands, var_model=var_model,
									round_func=self.roundNumber)
		charString = T2CharString(program=program, private=private,
							  globalSubrs=globalSubrs)
		return charString
