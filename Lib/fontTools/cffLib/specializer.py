# -*- coding: utf-8 -*-

"""T2CharString operator specializer and generalizer."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *


def stringToProgram(string):
	if isinstance(string, basestring):
		string = string.split()
	program = []
	for token in string:
		try:
			token = int(token)
		except ValueError:
			try:
				token = float(token)
			except ValueError:
				pass
		program.append(token)
	return program

def programToString(program):
	return ' '.join(str(x) for x in program)


def programToCommands(program):
	"""Takes a T2CharString program list and returns list of commands.
	Each command is a two-tuple of commandname,arg-list.  The commandname might
	be empty string if no commandname shall be emitted (used for glyph width,
	hintmask/cntrmask argument, as well as stray arguments at the end of the
	program (¯\_(ツ)_/¯)."""

	width = None
	commands = []
	stack = []
	it = iter(program)
	for token in it:
		if not isinstance(token, basestring):
			stack.append(token)
			continue

		if width is None and token in {'hstem', 'hstemhm', 'vstem', 'vstemhm',
					       'cntrmask', 'hintmask',
					       'hmoveto', 'vmoveto', 'rmoveto',
					       'endchar'}:
			parity = token in {'hmoveto', 'vmoveto'}
			if stack and (len(stack) % 2) ^ parity:
				width = stack.pop(0)
				commands.append(('', [width]))

		if token in {'hintmask', 'cntrmask'}:
			if stack:
				commands.append(('', stack))
			commands.append((token, []))
			commands.append(('', [next(it)]))
		else:
			commands.append((token,stack))
		stack = []
	if stack:
		commands.append(('', stack))
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
		if not args: raise ValueError(args)
		for args in _everyN(args, 2):
			yield ('rlineto', args)
	@staticmethod
	def hlineto(args):
		if not args: raise ValueError(args)
		it = iter(args)
		try:
			while True:
				yield ('rlineto', [next(it), 0])
				yield ('rlineto', [0, next(it)])
		except StopIteration:
			pass
	@staticmethod
	def vlineto(args):
		if not args: raise ValueError(args)
		it = iter(args)
		try:
			while True:
				yield ('rlineto', [0, next(it)])
				yield ('rlineto', [next(it), 0])
		except StopIteration:
			pass
	@staticmethod
	def rrcurveto(args):
		if not args: raise ValueError(args)
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


def generalizeCommands(commands, ignoreErrors=False):
	result = []
	mapping = _GeneralizerDecombinerCommandsMap
	for op,args in commands:
		func = getattr(mapping, op, None)
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
				result.append(('', args))
				result.append(('', [op]))
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
	if not v[0]:
		if not v[1]:
			return '0', v[:1]
		else:
			return 'v', v[1:]
	else:
		if not v[1]:
			return 'h', v[:1]
		else:
			return 'r', v

def _mergeCategories(a, b):
	if a == '0': return b
	if b == '0': return a
	if a == b: return a
	return None

def _negateCategory(a):
	if a == 'h': return 'v'
	if a == 'v': return 'h'
	assert a in '0r'
	return a

def specializeCommands(commands,
		       ignoreErrors=False,
		       generalizeFirst=True,
		       preserveTopology=False,
		       maxstack=48):

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
	# 3. Merge or delete redundant operations, to the extent requested.
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
		commands = list(commands) # Make copy since we modify in-place later.

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
	# all four of rhcurveto, rvcurveto, hrcurveto, and vrcurveto are encodable for one curve.
	#
	# Of the curve types with '0', the 00curveto is equivalent to a lineto variant.  The rest
	# of the curve types with a 0 need to be encoded as a h or v variant.  Ie. a '0' can be
	# thought of a "don't care" and can be used as either an 'h' or a 'v'.  As such, we always
	# encode a number 0 as argument when we use a '0' variant.  Later on, we can just substitute
	# the '0' with either 'h' or 'v' and it works.
	#
	# When we get to curve splines however, things become more complicated...  XXX finish this.
	# There's one more complexity with splines.  If one side of the spline is not horizontal or
	# vertical (or zero), ie. if it's 'r', then it limits which spline types we can encode.
	# Only hhcurveto and vvcurveto operators can encode a spline starting with 'r', and
	# only hvcurveto and vhcurveto operators can encode a spline ending with 'r'.
	# This limits our merge opportunities later.
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
			commands[i] = c1+c2+'curveto', args1+args[2:4]+args2
			continue

	# 3. Merge or delete redundant operations, to the extent requested.
	#
	# TODO
	# A 0moveto that comes before all other path operations can be removed.
	# though I find conflicting evidence for this.
	#
	# TODO
	# "If hstem and vstem hints are both declared at the beginning of a
	# CharString, and this sequence is followed directly by the hintmask or
	# cntrmask operators, then the vstem hint operator (or, if applicable,
	# the vstemhm operator) need not be included."
	#
	# "The sequence and form of a CFF2 CharString program may be represented as:
	# {hs* vs* cm* hm* mt subpath}? {mt subpath}*"
	#
	# https://www.microsoft.com/typography/otspec/cff2charstr.htm#section3.1
	#
	# For Type2 CharStrings the sequence is:
	# w? {hs* vs* cm* hm* mt subpath}? {mt subpath}* endchar"


	# Some other redundancies change topology (point numbers).
	if not preserveTopology:
		for i in range(len(commands)-1, -1, -1):
			op, args = commands[i]

			# A 00curveto is demoted to a (specialized) lineto.
			if op == '00curveto':
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

		if op[2:] == 'curveto' and len(args) == 5 and prv == nxt == 'rrcurveto':
			assert (op[0] == 'r') ^ (op[1] == 'r')
			if op[0] == 'v':
				pos = 0
			elif op[0] != 'r':
				pos = 1
			elif op[1] == 'v':
				pos = 4
			else:
				pos = 5
			# Insert, while maintaining the type of args (can be tuple or list).
			args = args[:pos] + type(args)((0,)) + args[pos:]
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

		elif (op1, op2) in {('rlineto', 'rlinecurve'), ('rrcurveto', 'rcurveline')}:
			new_op = op2

		elif {op1, op2} == {'vlineto', 'hlineto'}:
			new_op = op1

		elif 'curveto' == op1[2:] == op2[2:]:
			d0, d1 = op1[:2]
			d2, d3 = op2[:2]

			if d1 == 'r' or d2 == 'r' or d0 == d3 == 'r':
				continue

			d = _mergeCategories(d1, d2)
			if d is None: continue
			if d0 == 'r':
				d = _mergeCategories(d, d3)
				if d is None: continue
				new_op = 'r'+d+'curveto'
			elif d3 == 'r':
				d0 = _mergeCategories(d0, _negateCategory(d))
				if d0 is None: continue
				new_op = d0+'r'+'curveto'
			else:
				d0 = _mergeCategories(d0, d3)
				if d0 is None: continue
				new_op = d0+d+'curveto'

		if new_op and len(args1) + len(args2) <= maxstack:
			commands[i-1] = (new_op, args1+args2)
			del commands[i]

	# 6. Resolve any remaining made-up operators into real operators.
	for i in range(len(commands)):
		op,args = commands[i]

		if op in {'0moveto', '0lineto'}:
			commands[i] = 'h'+op[1:], args
			continue

		if op[2:] == 'curveto' and op[:2] not in {'rr', 'hh', 'vv', 'vh', 'hv'}:
			op0, op1 = op[:2]
			if (op0 == 'r') ^ (op1 == 'r'):
				assert len(args) % 2 == 1
			if op0 == '0': op0 = 'h'
			if op1 == '0': op1 = 'h'
			if op0 == 'r': op0 = op1
			if op1 == 'r': op1 = _negateCategory(op0)
			assert {op0,op1} <= {'h','v'}, (op0, op1)

			if len(args) % 2:
				if op0 != op1: # vhcurveto / hvcurveto
					if (op0 == 'h') ^ (len(args) % 8 == 1):
						# Swap last two args order
						args = args[:-2]+args[-1:]+args[-2:-1]
				else: # hhcurveto / vvcurveto
					if op0 == 'h': # hhcurveto
						# Swap first two args order
						args = args[1:2]+args[:1]+args[2:]

			commands[i] = op0+op1+'curveto', args
			continue

	return commands

def specializeProgram(program, **kwargs):
	return commandsToProgram(specializeCommands(programToCommands(program), **kwargs))


if __name__ == '__main__':
	import sys
	if len(sys.argv) == 1:
		import doctest
		sys.exit(doctest.testmod().failed)
	program = stringToProgram(sys.argv[1:])
	print("Program:"); print(programToString(program))
	commands = programToCommands(program)
	print("Commands:"); print(commands)
	program2 = commandsToProgram(commands)
	print("Program from commands:"); print(programToString(program2))
	assert program == program2
	print("Generalized program:"); print(programToString(generalizeProgram(program)))
	print("Specialized program:"); print(programToString(specializeProgram(program)))

