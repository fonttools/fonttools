# -*- coding: utf-8 -*-

"""T2CharString operator specializer and generalizer."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

def programToCommands(program):
	"""Takes a T2CharString program list and returns list of commands.
	Each command is a two-tuple of commandname,arg-list.  The commandname might
	be None if no commandname shall be emitted (used for glyph width (TODO),
	hintmask/cntrmask argument, as well as stray arguments at the end of
	program (¯\_(ツ)_/¯)."""

	commands = []
	stack = []
	it = iter(program)
	for token in it:
		if not isinstance(token, basestring):
			stack.append(token)
			continue
		if token in ('hintmask', 'cntrmask'):
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
	if len(el) % n != 0: raise ValueError(args)
	for i in range(0, len(el), n):
		yield el[i:i+n]


class _GeneralizeCommandsMap(object):

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
		if len(args) < 4 or len(args) % 8 not in (0,1,4,5): raise ValueError(args)
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
		if len(args) < 4 or len(args) % 8 not in (0,1,4,5): raise ValueError(args)
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
	mapping = _GeneralizeCommandsMap
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
				result.append((op,args))
			else:
				raise
	return result

def generalizeProgram(program, **kwargs):
	return commandsToProgram(generalizeCommands(programToCommands(program), **kwargs))


if __name__ == '__main__':
	import sys
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
