"""
Interpolate OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.varLib import designspace, models, VarLibError
from fontTools.varLib.merger import InstancerMerger
import os.path



def interpolate_layout(designspace_filename, loc, finder):

	ds = designspace.load(designspace_filename)
	axes = ds['axes'] if 'axes' in ds else []
	if 'sources' not in ds or not ds['sources']:
		raise VarLibError("no 'sources' defined in .designspace")
	masters = ds['sources']

	base_idx = None
	for i,m in enumerate(masters):
		if 'info' in m and m['info']['copy']:
			assert base_idx is None
			base_idx = i
	assert base_idx is not None, "Cannot find 'base' master; Add <info> element to one of the masters in the .designspace document."

	from pprint import pprint
	print("Index of base master:", base_idx)

	print("Building variable font")
	print("Loading master fonts")
	basedir = os.path.dirname(designspace_filename)
	master_ttfs = [finder(os.path.join(basedir, m['filename'])) for m in masters]
	master_fonts = [TTFont(ttf_path) for ttf_path in master_ttfs]

	#font = master_fonts[base_idx]
	font = TTFont(master_ttfs[base_idx])

	master_locs = [o['location'] for o in masters]

	axis_names = set(master_locs[0].keys())
	assert all(axis_names == set(m.keys()) for m in master_locs)

	# Set up axes
	axes_dict = {}
	if axes:
		# the designspace file loaded had an <axes> element
		for axis in axes:
			default = axis['default']
			lower = axis['minimum']
			upper = axis['maximum']
			name = axis['name']
			axes_dict[name] = (lower, default, upper)
	else:
		for tag in axis_names:
			default = master_locs[base_idx][tag]
			lower = min(m[tag] for m in master_locs)
			upper = max(m[tag] for m in master_locs)
			if default == lower == upper:
				continue
			axes_dict[tag] = (lower, default, upper)
	print("Axes:")
	pprint(axes_dict)

	print("Location:", loc)
	print("Master locations:")
	pprint(master_locs)

	# Normalize locations
	loc = models.normalizeLocation(loc, axes_dict)
	master_locs = [models.normalizeLocation(m, axes_dict) for m in master_locs]

	print("Normalized location:", loc)
	print("Normalized master locations:")
	pprint(master_locs)

	# Assume single-model for now.
	model = models.VariationModel(master_locs)
	assert 0 == model.mapping[base_idx]

	merger = InstancerMerger(font, model, loc)

	print("Building variations tables")
	merger.mergeTables(font, master_fonts, axes_dict, base_idx, ['GPOS'])
	return font


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

	font = interpolate_layout(designspace_filename, loc, finder)
	print("Saving font", outfile)
	font.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		sys.exit(main())
	import doctest
	sys.exit(doctest.testmod().failed)
