"""
Interpolate OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.varLib import models, VarLibError, load_designspace, load_masters
from fontTools.varLib.merger import InstancerMerger
import os.path
import logging
from copy import deepcopy
from pprint import pformat

log = logging.getLogger("fontTools.varLib.interpolate_layout")


def interpolate_layout(designspace, loc, master_finder=lambda s:s, mapped=False):
	"""
	Interpolate GPOS from a designspace file and location.

	If master_finder is set, it should be a callable that takes master
	filename as found in designspace file and map it to master font
	binary as to be opened (eg. .ttf or .otf).

	If mapped is False (default), then location is mapped using the
	map element of the axes in designspace file.  If mapped is True,
	it is assumed that location is in designspace's internal space and
	no mapping is performed.
	"""
	if hasattr(designspace, "sources"):  # Assume a DesignspaceDocument
		pass
	else:  # Assume a file path
		from fontTools.designspaceLib import DesignSpaceDocument
		designspace = DesignSpaceDocument.fromfile(designspace)

	ds = load_designspace(designspace)
	log.info("Building interpolated font")

	log.info("Loading master fonts")
	master_fonts = load_masters(designspace, master_finder)
	font = deepcopy(master_fonts[ds.base_idx])

	log.info("Location: %s", pformat(loc))
	if not mapped:
		loc = {name: ds.axes[name].map_forward(v) for name,v in loc.items()}
	log.info("Internal location: %s", pformat(loc))
	loc = models.normalizeLocation(loc, ds.internal_axis_supports)
	log.info("Normalized location: %s", pformat(loc))

	# Assume single-model for now.
	model = models.VariationModel(ds.normalized_master_locs)
	assert 0 == model.mapping[ds.base_idx]

	merger = InstancerMerger(font, model, loc)

	log.info("Building interpolated tables")
	# TODO GSUB/GDEF
	merger.mergeTables(font, master_fonts, ['GPOS'])
	return font


def main(args=None):
	from fontTools import configLogger

	import sys
	if args is None:
		args = sys.argv[1:]

	designspace_filename = args[0]
	locargs = args[1:]
	outfile = os.path.splitext(designspace_filename)[0] + '-instance.ttf'

	# TODO: allow user to configure logging via command-line options
	configLogger(level="INFO")

	finder = lambda s: s.replace('master_ufo', 'master_ttf_interpolatable').replace('.ufo', '.ttf')

	loc = {}
	for arg in locargs:
		tag,val = arg.split('=')
		loc[tag] = float(val)

	font = interpolate_layout(designspace_filename, loc, finder)
	log.info("Saving font %s", outfile)
	font.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		sys.exit(main())
	import doctest
	sys.exit(doctest.testmod().failed)
