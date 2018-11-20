from __future__ import print_function, division, absolute_import
from fontTools.misc.psCharStrings import CFF2Subr
from fontTools.pens.t2CharStringPen import T2CharStringPen, t2c_round
from fontTools.cffLib.specializer import (commandsToProgram,
										  specializeCommands)
from fontTools.cffLib import maxStackLimit
from fontTools.varLib.models import allEqual


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

	def make_flat_curve(self, prev_coords, cur_coords):
		# Convert line coords to curve coords.
		dx = self.roundNumber((cur_coords[0] - prev_coords[0])/3.0)
		dy = self.roundNumber((cur_coords[1] - prev_coords[1])/3.0)
		new_coords = [prev_coords[0] + dx,
					  prev_coords[1] + dy,
					  prev_coords[0] + 2*dx,
					  prev_coords[1] + 2*dy
					  ] + cur_coords
		return new_coords

	def make_curve_coords(self, coords, is_default):
		# Convert line coords to curve coords.
		prev_cmd = self._commands[self.pt_index-1]
		if is_default:
			new_coords = []
			for i, cur_coords in enumerate(coords):
				prev_coords = prev_cmd[1][i]
				master_coords = self.make_flat_curve(prev_coords[:2],
													 cur_coords)
				new_coords.append(master_coords)
		else:
			cur_coords = coords
			prev_coords = prev_cmd[1][-1]
			new_coords = self.make_flat_curve(prev_coords[:2], cur_coords)
		return new_coords

	def check_and_fix_flat_curve(self, cmd, point_type, pt_coords):
		if (point_type == 'rlineto') and (cmd[0] == 'rrcurveto'):
			is_default = False
			pt_coords = self.make_curve_coords(pt_coords, is_default)
			success = True
		elif (point_type == 'rrcurveto') and (cmd[0] == 'rlineto'):
			is_default = True
			expanded_coords = self.make_curve_coords(cmd[1], is_default)
			cmd[1] = expanded_coords
			cmd[0] = point_type
			success = True
		else:
			success = False
		return success, pt_coords

	def check_and_fix_closepath(self, cmd, point_type, pt_coords):
		""" Some workflows drop a lineto which closes a path.
		Also, if the last segment is a curve in one master,
		and a flat curve in another, the flat curve can get
		converted to a closing lineto, and then dropped.
		Test if:
		1) one master op is a moveto,
		2) the previous op for this master does not close the path
		3) in the other master the current op is not a moveto
		4) the current op in the otehr master closes the current path

		If the default font is missing the closing lineto, insert it,
		then proceed with merging the current op and pt_coords.

		If the current region is missing the closing lineto
		and therefore the current op is a moveto,
		then add closing coordinates to self._commands,
		and increment self.pt_index.

		Note that if this may insert a point in the default font list,
		so after using it, 'cmd' needs to be reset.

		return True if we can fix this issue.
		"""
		if point_type == 'rmoveto':
			# If this is the case, we know that cmd[0] != 'rmoveto'

			# The previous op must not close the path for this region font.
			prev_moveto_coords = self._commands[self.prev_move_idx][1][-1]
			prv_coords = self._commands[self.pt_index-1][1][-1]
			if prev_moveto_coords == prv_coords[-2:]:
				return False

			# The current op must close the path for the default font.
			prev_moveto_coords2 = self._commands[self.prev_move_idx][1][0]
			prv_coords = self._commands[self.pt_index][1][0]
			if prev_moveto_coords2 != prv_coords[-2:]:
				return False

			# Add the closing line coords for this region
			# so self._commands, then increment self.pt_index
			# so that the current region op will get merged
			# with the next default font moveto.
			if cmd[0] == 'rrcurveto':
				new_coords = self.make_curve_coords(prev_moveto_coords, False)
			cmd[1].append(new_coords)
			self.pt_index += 1
			return True

		if cmd[0] == 'rmoveto':
			# The previous op must not close the path for the default font.
			prev_moveto_coords = self._commands[self.prev_move_idx][1][0]
			prv_coords = self._commands[self.pt_index-1][1][0]
			if prev_moveto_coords == prv_coords[-2:]:
				return False

			# The current op must close the path for this region font.
			prev_moveto_coords2 = self._commands[self.prev_move_idx][1][-1]
			if prev_moveto_coords2 != pt_coords[-2:]:
				return False

			# Insert the close path segment in the default font.
			# We omit the last coords from the previous moveto
			# is it will be supplied by the current region point.
			# after this function returns.
			new_cmd = [point_type, None]
			prev_move_coords = self._commands[self.prev_move_idx][1][:-1]
			# Note that we omit the last region's coord from prev_move_coords,
			# as that is from the current region, and we will add the
			# current pts' coords from the current region in its place.
			if point_type == 'rlineto':
				new_cmd[1] = prev_move_coords
			else:
				# We omit the last set of coords from the
				# previous moveto, as it will be supplied by the coords
				# for the current region pt.
				new_cmd[1] = self.make_curve_coords(prev_move_coords, True)
			self._commands.insert(self.pt_index, new_cmd)
			return True
		return False

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
		self.prev_move_abs_coords = self.roundPoint(self._p0)
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
		charString = CFF2Subr(program=program, private=private,
							  globalSubrs=globalSubrs)
		return charString
