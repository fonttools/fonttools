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


def stops(support, count=20):
	a,b,c = support

	return [a + (b - a) * i / count for i in range(count)] + \
	       [b + (c - b) * i / count for i in range(count)] + \
	       [c]

def plotDocument(doc, fig, **kwargs):
	assert len(doc.axes) == 2

	n = len(doc.sources)
	cols = math.ceil(n**.5)
	rows = math.ceil(n / cols)

	doc.normalize()

	model = VariationModel([s.location for s in doc.sources])

	ax1 = doc.axes[0].name
	ax2 = doc.axes[1].name
	for i, (support,color) in enumerate(zip(model.supports, cycle(pyplot.cm.Set1.colors))):

		axis3D = fig.add_subplot(rows, cols, i + 1, projection='3d')

		Xs = support.get(ax1, (-1.,0.,+1.))
		Ys = support.get(ax2, (-1.,0.,+1.))
		for x in stops(Xs):
			X, Y, Z = [], [], []
			for y in Ys:
				z = supportScalar({ax1:x, ax2:y}, support)
				X.append(x)
				Y.append(y)
				Z.append(z)
			axis3D.plot_wireframe(X, Y, Z, color=color, **kwargs)
		for y in stops(Ys):
			X, Y, Z = [], [], []
			for x in Xs:
				z = supportScalar({ax1:x, ax2:y}, support)
				X.append(x)
				Y.append(y)
				Z.append(z)
			axis3D.plot_wireframe(X, Y, Z, color=color, **kwargs)


def main(args=None):
	from fontTools import configLogger

	if args is None:
		args = sys.argv[1:]

	# configure the library logger (for >= WARNING)
	configLogger()
	# comment this out to enable debug messages from logger
	# log.setLevel(logging.DEBUG)

	if len(args) < 1:
		print("usage: fonttools varLib.plot soure.designspace", file=sys.stderr)
		sys.exit(1)

	doc = DesignSpaceDocument()
	doc.read(args[0])

	fig = pyplot.figure()

	plotDocument(doc, fig)

	pyplot.show()

if __name__ == '__main__':
	import sys
	sys.exit(main())
