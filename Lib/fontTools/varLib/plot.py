"""Visualize DesignSpaceDocument and resulting VariationModel."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.varLib.models import VariationModel, supportScalar
from fontTools.designspaceLib import DesignSpaceDocument
from mpl_toolkits.mplot3d import axes3d
from matplotlib import pyplot
from itertools import cycle
import math
import logging
import sys

log = logging.getLogger(__name__)


def stops(support, count=10):
	a,b,c = support

	return [a + (b - a) * i / count for i in range(count)] + \
	       [b + (c - b) * i / count for i in range(count)] + \
	       [c]

def plotLocations(locations, axes, axis3D, **kwargs):
	for loc,color in zip(locations, cycle(pyplot.cm.Set1.colors)):
		axis3D.plot([loc.get(axes[0], 0)],
			    [loc.get(axes[1], 0)],
			    [1.],
			    'o',
			    color=color,
			    **kwargs)

def plotLocationsSurfaces(locations, fig, names=None, **kwargs):

	assert len(locations[0].keys()) == 2

	if names is None:
		names = ['']

	n = len(locations)
	cols = math.ceil(n**.5)
	rows = math.ceil(n / cols)

	model = VariationModel(locations)
	names = [names[model.reverseMapping[i]] for i in range(len(names))]

	ax1, ax2 = sorted(locations[0].keys())
	for i, (support,color, name) in enumerate(zip(model.supports, cycle(pyplot.cm.Set1.colors), cycle(names))):

		axis3D = fig.add_subplot(rows, cols, i + 1, projection='3d')
		axis3D.set_title(name)
		axis3D.set_xlabel(ax1)
		axis3D.set_ylabel(ax2)
		pyplot.xlim(-1.,+1.)
		pyplot.ylim(-1.,+1.)

		Xs = support.get(ax1, (-1.,0.,+1.))
		Ys = support.get(ax2, (-1.,0.,+1.))
		for x in stops(Xs):
			X, Y, Z = [], [], []
			for y in Ys:
				z = supportScalar({ax1:x, ax2:y}, support)
				X.append(x)
				Y.append(y)
				Z.append(z)
			axis3D.plot(X, Y, Z, color=color, **kwargs)
		for y in stops(Ys):
			X, Y, Z = [], [], []
			for x in Xs:
				z = supportScalar({ax1:x, ax2:y}, support)
				X.append(x)
				Y.append(y)
				Z.append(z)
			axis3D.plot(X, Y, Z, color=color, **kwargs)

		plotLocations(model.locations, [ax1, ax2], axis3D)


def plotDocument(doc, fig, **kwargs):
	doc.normalize()
	locations = [s.location for s in doc.sources]
	names = [s.name for s in doc.sources]
	plotLocationsSurfaces(locations, fig, names, **kwargs)


def main(args=None):
	from fontTools import configLogger

	if args is None:
		args = sys.argv[1:]

	# configure the library logger (for >= WARNING)
	configLogger()
	# comment this out to enable debug messages from logger
	# log.setLevel(logging.DEBUG)

	if len(args) < 1:
		print("usage: fonttools varLib.plot source.designspace", file=sys.stderr)
		print("  or")
		print("usage: fonttools varLib.plot location1 location2 ...", file=sys.stderr)
		sys.exit(1)

	fig = pyplot.figure()

	if len(args) == 1 and args[0].endswith('.designspace'):
		doc = DesignSpaceDocument()
		doc.read(args[0])
		plotDocument(doc, fig)
	else:
		axes = [chr(c) for c in range(ord('A'), ord('Z')+1)]
		locs = [dict(zip(axes, (float(v) for v in s.split(',')))) for s in args]
		plotLocationsSurfaces(locs, fig)

	pyplot.show()

if __name__ == '__main__':
	import sys
	sys.exit(main())
