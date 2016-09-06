"""
Interpolate OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.varLib import designspace, models, builder
from fontTools.varLib.merger import merge_tables
import os.path

class Merger(object):

	def __init__(self, model, location):
		self.model = model
		self.location = location

def main(args=None):

	import sys
	if args is None:
		args = sys.argv[1:]

	designspace_filename = args[0]
	locargs = args[1:]
	outfile = os.path.splitext(designspace_filename)[0] + '-instance.ttf'

	finder = lambda s: s.replace('master_ufo', 'master_ttf_interpolatable').replace('.ufo', '.ttf')

	loc = {}
	for arg in locargs:
		tag,val = arg.split('=')
		loc[tag] = float(val)
	print("Location:", loc)

	masters, instances = designspace.load(designspace_filename)
	base_idx = None
	for i,m in enumerate(masters):
		if 'info' in m and m['info']['copy']:
			assert base_idx is None
			base_idx = i
	assert base_idx is not None, "Cannot find 'base' master; Add <info> element to one of the masters in the .designspace document."

	from pprint import pprint
	print("Masters:")
	pprint(masters)
	print("Index of base master:", base_idx)

	print("Building GX")
	print("Loading TTF masters")
	basedir = os.path.dirname(designspace_filename)
	master_ttfs = [finder(os.path.join(basedir, m['filename'])) for m in masters]
	master_fonts = [TTFont(ttf_path) for ttf_path in master_ttfs]

	#font = master_fonts[base_idx]
	font = TTFont(master_ttfs[base_idx])

	master_locs = [o['location'] for o in masters]

	axis_tags = set(master_locs[0].keys())
	assert all(axis_tags == set(m.keys()) for m in master_locs)
	print("Axis tags:", axis_tags)
	print("Master positions:")
	pprint(master_locs)

	# Set up axes
	axes = {}
	for tag in axis_tags:
		default = master_locs[base_idx][tag]
		lower = min(m[tag] for m in master_locs)
		upper = max(m[tag] for m in master_locs)
		axes[tag] = (lower, default, upper)
	print("Axes:")
	pprint(axes)

	loc = models.normalizeLocation(loc, axes)
	# Location is normalized now
	print("Normalized location:", loc)

	# Normalize master locations
	master_locs = [models.normalizeLocation(m, axes) for m in master_locs]
	print("Normalized master positions:")
	print(master_locs)

	# Assume single-model for now.
	model = models.VariationModel(master_locs)
	assert 0 == model.mapping[base_idx]

	merger = Merger(model, loc)

	print("Building variations tables")
	merge_tables(font, merger, master_fonts, axes, base_idx, ['GPOS'])

	print("Saving font", outfile)
	font.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		main()
		#sys.exit(0)
	import doctest, sys
	sys.exit(doctest.testmod().failed)
