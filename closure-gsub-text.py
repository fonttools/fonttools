#!/usr/bin/python

# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0(the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Google Author(s): Behdad Esfahbod

import sys, pyotlss

args = sys.argv[1:]

options = pyotlss.Options ()
args = options.parse_opts (args)

subsetter = pyotlss.Subsetter (options=options)
subsetter.populate (text = args[1])

font = pyotlss.load_font (args[0], options, dontLoadGlyphNames=not options.glyph_names)

font['cmap'].closure_glyphs (subsetter)
font['GSUB'].closure_glyphs (subsetter)

if options.glyph_names:
	print ' '.join (sorted (subsetter.glyphs))
else:
	m = font.getReverseGlyphMap ()
	print ' '.join (str (s) for s in sorted (m[g] for g in subsetter.glyphs))
