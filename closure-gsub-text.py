#!/usr/bin/python

import sys, pyotlss

args = sys.argv[1:]

options = pyotlss.Options ()
args = options.parse_opts (args)

subsetter = pyotlss.Subsetter (options=options)
subsetter.populate (text = args[1])

font = pyotlss.load_font (args[0], dont_load_glyph_names=not options.glyph_names)

font['cmap'].closure_glyphs (subsetter)
font['GSUB'].closure_glyphs (subsetter)

if options.glyph_names:
	print ' '.join (sorted (subsetter.glyphs))
else:
	m = font.getReverseGlyphMap ()
	print ' '.join (str (s) for s in sorted (m[g] for g in subsetter.glyphs))
