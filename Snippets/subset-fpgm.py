#! /usr/bin/env python3

from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
import sys

if len(sys.argv) < 2:
	print("usage: subset-fpgm.py fontfile.ttf func-number...")
	sys.exit(1)
fontfile = sys.argv[1]
func_nums = [int(x) for x in sys.argv[2:]]

font = TTFont(fontfile)
fpgm = font['fpgm']

# Parse fpgm
asm = fpgm.program.getAssembly()
funcs = {}
stack = []
tokens = iter(asm)
for token in tokens:
	if token.startswith("PUSH") or token.startswith("NPUSH"):
		for token in tokens:
			try:
				num = int(token)
				stack.append(num)
			except ValueError:
				break
	if token.startswith("FDEF"):
		num = stack.pop()
		body = []
		for token in tokens:
			if token.startswith("ENDF"):
				break
			body.append(token)
		funcs[num] = body
		continue
	assert 0, "Unexpected token in fpgm: %s" % token

# Subset!
funcs = {i:funcs[i] for i in func_nums}

# Put it back together:
asm = []
if funcs:
	asm.append("PUSH[ ]")
nums = sorted(funcs.keys())
asm.extend(str(i) for i in nums)
for i in nums:
	asm.append("FDEF[ ]")
	asm.extend(funcs[i])
	asm.append("ENDF[ ]")

import pprint
pprint.pprint(asm)

fpgm.program.fromAssembly(asm)
# Make sure it compiles
fpgm.program.getBytecode()
