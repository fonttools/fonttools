# -*- coding: utf-8 -*-

"""T2CharString operator specializer and generalizer."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

def programToCommands(program):
	"""Takes a T2CharString program list and returns list of commands.
	Each command is a two-tuple of commandname,arg-list.  The commandname might
	be None if no commandname shall be emitted (used for glyph width (TODO),
	hintmask/cntrmask argument, as well as stray arguments at the end of the
	program (¯\_(ツ)_/¯)."""

	commands = []
	stack = []
	it = iter(program)
	for token in it:
		if not isinstance(token, basestring):
			stack.append(token)
			continue
		if token in {'hintmask', 'cntrmask'}:
			if stack:
				commands.append((None, stack))
			commands.append((token, []))
			commands.append((None, [next(it)]))
		else:
			commands.append((token,stack))
		stack = []
	if stack:
		commands.append((None, stack))
	return commands

def commandsToProgram(commands):
	"""Takes a commands list as returned by programToCommands() and converts
	it back to a T2CharString program list."""
	program = []
	for op,args in commands:
		program.extend(args)
		if op:
			program.append(op)
	return program



def _everyN(el, n):
	"""Group the list el into groups of size n"""
	if len(el) % n != 0: raise ValueError(el)
	for i in range(0, len(el), n):
		yield el[i:i+n]


class _GeneralizerDecombinerCommandsMap(object):

	@staticmethod
	def rmoveto(args):
		if len(args) != 2: raise ValueError(args)
		yield ('rmoveto', args)
	@staticmethod
	def hmoveto(args):
		if len(args) != 1: raise ValueError(args)
		yield ('rmoveto', [args[0], 0])
	@staticmethod
	def vmoveto(args):
		if len(args) != 1: raise ValueError(args)
		yield ('rmoveto', [0, args[0]])

	@staticmethod
	def rlineto(args):
		for args in _everyN(args, 2):
			yield ('rlineto', args)
	@staticmethod
	def hlineto(args):
		it = iter(args)
		while True:
			yield ('rlineto', [next(it), 0])
			yield ('rlineto', [0, next(it)])
	@staticmethod
	def vlineto(args):
		it = iter(args)
		while True:
			yield ('rlineto', [0, next(it)])
			yield ('rlineto', [next(it), 0])

	@staticmethod
	def rrcurveto(args):
		for args in _everyN(args, 6):
			yield ('rrcurveto', args)
	@staticmethod
	def hhcurveto(args):
		if len(args) < 4 or len(args) % 4 > 1: raise ValueError(args)
		if len(args) % 2 == 1:
			yield ('rrcurveto', [args[1], args[0], args[2], args[3], args[4], 0])
			args = args[5:]
		for args in _everyN(args, 4):
			yield ('rrcurveto', [args[0], 0, args[1], args[2], args[3], 0])
	@staticmethod
	def vvcurveto(args):
		if len(args) < 4 or len(args) % 4 > 1: raise ValueError(args)
		if len(args) % 2 == 1:
			yield ('rrcurveto', [args[0], args[1], args[2], args[3], 0, args[4]])
			args = args[5:]
		for args in _everyN(args, 4):
			yield ('rrcurveto', [0, args[0], args[1], args[2], 0, args[3]])
	@staticmethod
	def hvcurveto(args):
		if len(args) < 4 or len(args) % 8 not in {0,1,4,5}: raise ValueError(args)
		last_args = None
		if len(args) % 2 == 1:
			lastStraight = len(args) % 8 == 5
			args, last_args = args[:-5], args[-5:]
		it = _everyN(args, 4)
		try:
			while True:
				args = next(it)
				yield ('rrcurveto', [args[0], 0, args[1], args[2], 0, args[3]])
				args = next(it)
				yield ('rrcurveto', [0, args[0], args[1], args[2], args[3], 0])
		except StopIteration:
			pass
		if last_args:
			args = last_args
			if lastStraight:
				yield ('rrcurveto', [args[0], 0, args[1], args[2], args[4], args[3]])
			else:
				yield ('rrcurveto', [0, args[0], args[1], args[2], args[3], args[4]])
	@staticmethod
	def vhcurveto(args):
		if len(args) < 4 or len(args) % 8 not in {0,1,4,5}: raise ValueError(args)
		last_args = None
		if len(args) % 2 == 1:
			lastStraight = len(args) % 8 == 5
			args, last_args = args[:-5], args[-5:]
		it = _everyN(args, 4)
		try:
			while True:
				args = next(it)
				yield ('rrcurveto', [0, args[0], args[1], args[2], args[3], 0])
				args = next(it)
				yield ('rrcurveto', [args[0], 0, args[1], args[2], 0, args[3]])
		except StopIteration:
			pass
		if last_args:
			args = last_args
			if lastStraight:
				yield ('rrcurveto', [0, args[0], args[1], args[2], args[3], args[4]])
			else:
				yield ('rrcurveto', [args[0], 0, args[1], args[2], args[4], args[3]])

	@staticmethod
	def rcurveline(args):
		if len(args) < 8 or len(args) % 6 != 2: raise ValueError(args)
		args, last_args = args[:-2], args[-2:]
		for args in _everyN(args, 6):
			yield ('rrcurveto', args)
		yield ('rlineto', last_args)
	@staticmethod
	def rlinecurve(args):
		if len(args) < 8 or len(args) % 2 != 0: raise ValueError(args)
		args, last_args = args[:-6], args[-6:]
		for args in _everyN(args, 2):
			yield ('rlineto', args)
		yield ('rrcurveto', last_args)


def generalizeCommands(commands, ignoreErrors=True):
	result = []
	mapping = _GeneralizerDecombinerCommandsMap
	for op,args in commands:
		func = getattr(mapping, op if op else '', None)
		if not func:
			result.append((op,args))
			continue
		try:
			for command in func(args):
				result.append(command)
		except ValueError:
			if ignoreErrors:
				# Store op as data, such that consumers of commands do not have to
				# deal with incorrect number of arguments.
				result.append((None,args))
				result.append((None, [op]))
			else:
				raise
	return result

def generalizeProgram(program, **kwargs):
	return commandsToProgram(generalizeCommands(programToCommands(program), **kwargs))


def _categorizeVector(v):
	"""
	Takes X,Y vector v and returns one of r, h, v, or 0 depending on which
	of X and/or Y are zero, plus tuple of nonzero ones.  If both are zero,
	it returns a single zero still.

	>>> _categorizeVector((0,0))
	('0', (0,))
	>>> _categorizeVector((1,0))
	('h', (1,))
	>>> _categorizeVector((0,2))
	('v', (2,))
	>>> _categorizeVector((1,2))
	('r', (1, 2))
	"""
	if v[0] == 0:
		if v[1] == 0:
			return '0', type(v)((0,))
		else:
			return 'v', v[1:]
	else:
		if v[1] == 0:
			return 'h', v[:1]
		else:
			return 'r', v
	return "rvh0"[(v[1]==0) * 2 + (v[0]==0)]

def _mergeCategories(a, b, dontCare):
	if a == dontCare: return b
	if b == dontCare: return a
	if a == b: return a
	return None

def _applyJoint(a, b, j):
	if j == '.' or a == 'r' or b == 'r': return a, b
	if a != '0':
		c = 'hv'[(a == 'v') ^ (j == '+')]
		assert b == '0' or b == c
		b = c
	else:
		a = 'hv'[(b == 'v') ^ (j == '+')]
	return a, b

def specializeCommands(commands,
		       ignoreErrors=False,
		       generalizeFirst=True,
		       preserveTopology=False,
		       maxstack=48):

	maxstack -= 3 # AFDKO code uses effective 45 maxstack while the spec says 48.

	# We perform several rounds of optimizations.  They are carefully ordered and are:
	#
	# 0. Generalize commands.
	#    This ensures that they are in our expected simple form, with each line/curve only
	#    having arguments for one segment, and using the generic form (rlineto/rrcurveto).
	#    If caller is sure the input is in this form, they can turn off generalization to
	#    save time.
	#
	# 1. Combine successive rmoveto operations.
	#
	# 2. Specialize rmoveto/rlineto/rrcurveto operators into horizontal/vertical variants.
	#    We specialize into some, made-up, variants as well, which simplifies following
	#    passes.
	#
	# 3. Merge or delete redundant operations, if changing topology is allowed.
	#    OpenType spec declares point numbers in CFF undefined.  As such, we happily
	#    change topology.  If client relies on point numbers (in GPOS anchors, or for
	#    hinting purposes(what?)) they can turn this off.
	#
	# 4. Peephole optimization to revert back some of the h/v variants back into their
	#    original "relative" operator (rline/rrcurveto) if that saves a byte.
	#
	# 5. Combine adjacent operators when possible, minding not to go over max stack size.
	#
	# 6. Resolve any remaining made-up operators into real operators.
	#
	# I have convinced myself that this produces optimal bytecode (except for, possibly
	# one byte each time maxstack size prohibits combining.)  YMMV, but you'd be wrong. :-)
	# A dynamic-programming approach can do the same but would be significantly slower.


	# 0. Generalize commands.
	if generalizeFirst:
		commands = generalizeCommands(commands, ignoreErrors=ignoreErrors)
	else:
		commands = commands[:] # Make copy since we modify in-place later.

	# 1. Combine successive rmoveto operations.
	for i in range(len(commands)-1, 0, -1):
		if 'rmoveto' == commands[i][0] == commands[i-1][0]:
			v1, v2 = commands[i-1][1], commands[i][1]
			commands[i-1] = ('rmoveto', [v1[0]+v2[0], v1[1]+v2[1]])
			del commands[i]

	# 2. Specialize rmoveto/rlineto/rrcurveto operators into horizontal/vertical variants.
	#
	# We, in fact, specialize into more, made-up, variants that special-case when both
	# X and Y components are zero.  This simplifies the following optimization passes.
	# This case is rare, but OCD does not let me skip it.
	#
	# After this round, we will have four variants that use the following mnemonics:
	#
	#  - 'r' for relative,   ie. non-zero X and non-zero Y,
	#  - 'h' for horizontal, ie. zero X and non-zero Y,
	#  - 'v' for vertical,   ie. non-zero X and zero Y,
	#  - '0' for zeros,      ie. zero X and zero Y.
	#
	# The '0' pseudo-operators are not part of the spec, but help simplify the following
	# optimization rounds.  We resolve them at the end.  So, after this, we will have four
	# moveto and four lineto variants:
	#
	#  - 0moveto, 0lineto
	#  - hmoveto, hlineto
	#  - vmoveto, vlineto
	#  - rmoveto, rlineto
	#
	# and sixteen curveto variants.  For example, a '0hcurveto' operator means a curve
	# dx0,dy0,dx1,dy1,dx2,dy2,dx3,dy3 where dx0, dx1, and dy3 are zero but not dx3.
	# An 'rvcurveto' means dx3 is zero but not dx0,dy0,dy3.
	#
	# There are nine different variants of curves without the '0'.  Those nine map exactly
	# to the existing curve variants in the spec: rrcurveto, and the four variants hhcurveto,
	# vvcurveto, hvcurveto, and vhcurveto each cover two cases, one with an odd number of
	# arguments and one without.  Eg. an hhcurveto with an extra argument (odd number of
	# arguments) is in fact an rhcurveto.  The operators in the spec are designed such that
	# all four of rhcurveto, rvcurveto, hrcurveto, and vrcurveto are encodable.
	#
	# Of the curve types with '0', the 00curveto is equivalent to a lineto variant.  The rest
	# of the curve types with a 0 need to be encoded as a h or v variant.  Ie. a '0' can be
	# thought of a "don't care" and can be used as either an 'h' or a 'v'.  As such, we always
	# encode a number 0 as argument when we use a '0' variant.  Later on, we can just substitute
	# the '0' with either 'h' or 'v' and it works.
	#
	# When we get to curve splines however, things become more complicated. When we have a
	# curve spline that starts and ends horizontally, there are two different cases, one
	# where all curves start and end horizontally, another when curves alternate between
	# horizontal-vertical and vertical-horizontal.  To distinguish these cases, we use an
	# extra character in the pseudo-operator names that signifies the spline type:
	#
	#  - '+' means a spline where curves alternate between horizontal and vertical orientations,
	#        and is called a "pizza-slice" spline.
	#  - '=' means a spline where all curves start and end in the same orientation (h or v),
	#        and is called a "french-fries" spline.
	#  - '.' means "don't care", ie. the spline can be encoded / treated as either a pizzal-slice
	#        or french-fries.  This happens where 0s are involved in curves, because those can
	#        be encoded as both h and v.
	#
	# So, from here one, we use rrcurveto as is, but for other variants of curves we use three
	# mnemonic signifiers.  For example, 'h+vcurveto', or 'r.0curveto'.  Rules for combining
	# these will be defined later.
	#
	# There's one more complexity with splines.  If one side of the spline is not horizontal or
	# vertical (or zero), ie. if it's 'r', then it limits which spline types we can encode.
	# Only spline type '=' can start with an 'r' (hhcurveto and vvcurveto operators), and
	# only spline type '+' can end in an 'r' (hvcurveto and vhcurveto operators).
	#
	for i in range(len(commands)):
		op,args = commands[i]

		if op in {'rmoveto', 'rlineto'}:
			c, args = _categorizeVector(args)
			commands[i] = c+op[1:], args
			continue

		if op == 'rrcurveto':
			c1, args1 = _categorizeVector(args[:2])
			c2, args2 = _categorizeVector(args[-2:])
			if c1 == c2 == 'r':
				continue

			join = '.'
			if c1 == 'r':
				join = '='
			elif c2 == 'r':
				join = '+'
			elif c1 != '0' and c2 != '0':
				# Both sides are h and/or v
				join = '=' if c1 == c2 else '+'

			commands[i] = c1+join+c2+'curveto', args1+args[2:4]+args2
			continue

	# 3. Merge or delete redundant operations, if changing topology is allowed.
	if not preserveTopology:
		for i in range(len(commands)-1, -1, -1):
			op, args = commands[i]

			# A 0x0curveto is demoted to a (specialized) lineto.
			if op == '0x0curveto':
				assert len(args) == 4
				c, args = _categorizeVector(args[1:3])
				op = c+'lineto'
				commands[i] = op, args
				# and then...

			# A 0lineto can be deleted.
			if op == '0lineto':
				del commands[i]
				continue

			# Merge adjacent hlineto's and vlineto's.
			if i and op in {'hlineto', 'vlineto'} and op == commands[i-1][0]:
				_, other_args = commands[i-1]
				assert len(args) == 1 and len(other_args) == 1
				commands[i-1] = (op, [other_args[0]+args[0]])
				del commands[i]
				continue

	# 4. Peephole optimization to revert back some of the h/v variants back into their
	#    original "relative" operator (rline/rrcurveto) if that saves a byte.
	for i in range(1, len(commands)-1):
		op,args = commands[i]
		prv,nxt = commands[i-1][0], commands[i+1][0]

		if op in {'0lineto', 'hlineto', 'vlineto'} and prv == nxt == 'rlineto':
			assert len(args) == 1
			args = [0, args[0]] if op[0] == 'v' else [args[0], 0]
			commands[i] = ('rlineto', args)
			continue

		if op[3:] == 'curveto' and len(args) == 5 and prv == nxt == 'rrcurveto':
			assert (op[0] == 'r') ^ (op[2] == 'r')
			args = args[:]
			if op[0] == 'v':
				pos = 0
			elif op[0] != 'r':
				pos = 1
			elif op[1] == 'v':
				pos = 4
			else:
				pos = 5
			args.insert(pos, 0)
			commands[i] = ('rrcurveto', args)
			continue

	# 5. Combine adjacent operators when possible, minding not to go over max stack size.
	for i in range(len(commands)-1, 0, -1):
		op1,args1 = commands[i-1]
		op2,args2 = commands[i]
		new_op = None

		# Merge logic...
		if {op1, op2} <= {'rlineto', 'rrcurveto'}:
			if op1 == op2:
				new_op = op1
			else:
				if op2 == 'rrcurveto' and len(args2) == 6:
					new_op = 'rlinecurve'
				elif len(args2) == 2:
					new_op = 'rcurveline'
		elif {op1, op2} == {'vlineto', 'hlineto'}:
			new_op = op1
		elif 'curveto' == op1[3:] == op2[3:]:
			# Two curves can merge if their spline types are compatible, ie.
			# at least one is a wildcard spline ('.') or otherwise the two are
			# both pizza ('+') or both fries ('='), and
			#
			# The joining orientations are NOT 'r', and are compatible, ie.
			# at least one is a '0', or otherwise they are both 'h' or both
			# 'v'.
			#
			# The _mergeCategories() function does such compatibility matching.

			d0, j1, d1 = op1[:3]
			d2, j2, d3 = op2[:3]

			j = _mergeCategories(j1, j2, '.')
			d = _mergeCategories(d1, d2, '0')
			if j and d and d != 'r':

				if j == '.' and d != '0':
					# Need to resolve join, if middle is oriented but
					# join type is free...  Happens for example for:
					#
					# 0 0 1 2 3 0 rrcurveto 4 0 5 6 0 0 rrcurveto
					#
					# which can be combined both into a h=hcurveto, or
					# a v+vcurveto.  But would be wrong to combine into
					# 0.0curveto.  That would lose the orientation of the
					# middle segments!!
					#
					# Ok, this is one place that now I'm convinced my model
					# is not powerful enough... and maybe dynamic-programming
					# is needed after all.  I'll keep thinking about how
					# to fix this without too much work...
					j = '=' # XXX arbitrary

				# Propagate...
				d0,d = _applyJoint(d0, d, j) # WRONG?
				d,d3 = _applyJoint(d, d3, j) # WRONG?
				d0,d = _applyJoint(d0, d, j) # WRONG?

				new_op = d0+j+d3+'curveto'

		if new_op and len(args1) + len(args2) <= maxstack:
			commands[i-1] = (new_op, args1+args2)
			del commands[i]

	# 6. Resolve any remaining made-up operators into real operators.
	for i in range(len(commands)):
		op,args = commands[i]

		if op in {'0moveto', '0lineto'}:
			commands[i] = 'h'+op[1:], args
			continue

		if op[3:] == 'curveto':
			if op[0] == 'r' or op[2] == 'r':
				assert len(args) % 2 == 1
			if op[1] == '+':
				if (op[0] == 'v' or
				    (op[2] == 'h' and len(args) % 8 >= 4) or
				    (op[2] == 'v' and len(args) % 8 <  4)):
					op = 'vhcurveto'
				else:
					op = 'hvcurveto'

				if len(args) % 2 == 1 and ((op[0] == 'h') ^ (len(args) % 8 == 5)):
					# Swap last two args order
					args = args[:-2]+args[-1:]+args[-2:-1]
			else:
				op = 'vvcurveto' if op[0] == 'v' or op[2] == 'v' else 'hhcurveto'
				if len(args) % 2 == 1 and op[0] == 'h':
					# Swap first two args order
					args = args[1:2]+args[:1]+args[2:]
			commands[i] = op, args
			continue

	return commands

def specializeProgram(program, **kwargs):
	return commandsToProgram(specializeCommands(programToCommands(program), **kwargs))


if __name__ == '__main__':
	import sys
	if len(sys.argv) == 1:
		import doctest
		sys.exit(doctest.testmod().failed)
	program = []
	for token in sys.argv[1:]:
		try:
			token = int(token)
		except ValueError:
			try:
				token = float(token)
			except ValueError:
				pass
		program.append(token)
	print("Program:"); print(program)
	commands = programToCommands(program)
	print("Commands:"); print(commands)
	program2 = commandsToProgram(commands)
	print("Program from commands:"); print(program2)
	assert program == program2
	print("Generalized program:"); print(generalizeProgram(program))
	print("Specialized program:"); print(specializeProgram(program))

