"""
Interpolate OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib import designspace, models, builder
import os.path


def _all_equal(lst):
	it = iter(lst)
	v0 = next(it)
	for v in it:
		if v0 != v:
			return False
	return True

def buildVarDevTable(store, master_values):
	if _all_equal(master_values):
		return None
	deltas = master_values
	return builder.buildVarDevTable(0xdeadbeef)

def _merge_OTL(font, model, master_ttfs, axes, base_idx):

	print("Merging OpenType Layout tables")

	GDEFs = [m['GDEF'].table for m in master_ttfs]
	GPOSs = [m['GPOS'].table for m in master_ttfs]
	GSUBs = [m['GSUB'].table for m in master_ttfs]

	# Reuse the base font's tables
	for tag in 'GDEF', 'GPOS', 'GSUB':
		font[tag] = master_ttfs[base_idx][tag]

	GPOS = font['GPOS'].table

	getAnchor = lambda GPOS: GPOS.LookupList.Lookup[4].SubTable[0].MarkArray.MarkRecord[28].MarkAnchor
	store_builder = builder.OnlineVarStoreBuilder(axes.keys())
	store_builder.setModel(model)

	anchors = [getAnchor(G) for G in GPOSs]
	anchor = getAnchor(GPOS)

	XDeviceTable = buildVarDevTable(store_builder, [a.XCoordinate for a in anchors])
	YDeviceTable = buildVarDevTable(store_builder, [a.YCoordinate for a in anchors])
	if XDeviceTable or YDeviceTable:
		anchor.Format = 3
		anchor.XDeviceTable = XDeviceTable
		anchor.YDeviceTable = YDeviceTable

	store = store_builder.finish()
	# TODO insert in GDEF


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

	print("Building variations tables")
	_merge_OTL(font, model, master_fonts, axes, base_idx)

	print("Saving GX font", outfile)
	font.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		main()
		#sys.exit(0)
	import doctest, sys
	sys.exit(doctest.testmod().failed)
