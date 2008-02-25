def test():
	"""
		# some tests for the ps Hints operations
		>>> from robofab.world import RFont, RGlyph
		>>> g = RGlyph()
		>>> g.psHints.isEmpty()
		True

		>>> h = RGlyph()
		>>> i = g + h
		>>> i.psHints.isEmpty()
		True
		
		>>> i = g - h
		>>> i.psHints.isEmpty()
		True
		
		>>> i = g * 2
		>>> i.psHints.isEmpty()
		True
		
		>>> i = g / 2
		>>> i.psHints.isEmpty()
		True
		
		>>> g.psHints.vHints = [(100, 50), (200, 50)]
		>>> g.psHints.hHints = [(100, 50), (200, 5)]

		>>> not g.psHints.isEmpty()
		True

		# multiplication
		>>> v = g.psHints * 2
		>>> v.asDict() == {'vHints': [[200, 100], [400, 100]], 'hHints': [[200, 100], [400, 10]]}
		True

		# division
		>>> v = g.psHints / 2
		>>> v.asDict() == {'vHints': [[50.0, 25.0], [100.0, 25.0]], 'hHints': [[50.0, 25.0], [100.0, 2.5]]}
		True

		# multiplication with x, y, factor
		# vertically oriented values should respond different
		>>> v = g.psHints * (.5, 10)
		>>> v.asDict() == {'vHints': [[1000, 500], [2000, 500]], 'hHints': [[50.0, 25.0], [100.0, 2.5]]}
		True

		# division with x, y, factor
		# vertically oriented values should respond different
		>>> v = g.psHints / (.5, 10)
		>>> v.asDict() == {'vHints': [[10.0, 5.0], [20.0, 5.0]], 'hHints': [[200.0, 100.0], [400.0, 10.0]]}
		True

		# rounding to integer
		>>> v = g.psHints / 2
		>>> v.round()
		>>> v.asDict() == {'vHints': [(50, 25), (100, 25)], 'hHints': [(50, 25), (100, 3)]}
		True

		# "ps hint values calculating with a glyph"
		# ps hint values as part of glyphmath operations.
		# multiplication
		>>> h = g * 10
		>>> h.psHints.asDict() == {'vHints': [[1000, 500], [2000, 500]], 'hHints': [[1000, 500], [2000, 50]]}
		True

		# division
		>>> h = g / 2
		>>> h.psHints.asDict() == {'vHints': [[50.0, 25.0], [100.0, 25.0]], 'hHints': [[50.0, 25.0], [100.0, 2.5]]}
		True

		# x, y factor multiplication
		>>> h = g * (.5, 10)
		>>> h.psHints.asDict() == {'vHints': [[1000, 500], [2000, 500]], 'hHints': [[50.0, 25.0], [100.0, 2.5]]}
		True

		# x, y factor division
		>>> h = g / (.5, 10)
		>>> h.psHints.asDict() == {'vHints': [[10.0, 5.0], [20.0, 5.0]], 'hHints': [[200.0, 100.0], [400.0, 10.0]]}
		True

		# "font ps hint values"
		>>> f = RFont()
		>>> f.psHints.isEmpty()
		True

		>>> f.psHints.blueScale = .5
		>>> f.psHints.blueShift = 1
		>>> f.psHints.blueFuzz = 1
		>>> f.psHints.forceBold = True
		>>> f.psHints.hStems = (100, 90)
		>>> f.psHints.vStems = (500, 10)

		>>> not f.psHints.isEmpty()
		True

		# multiplication
		>>> v = f.psHints * 2
		>>> v.asDict() == {'vStems': [1000, 20], 'blueFuzz': 2, 'blueShift': 2, 'forceBold': 2, 'blueScale': 1.0, 'hStems': [200, 180]}
		True

		# division
		>>> v = f.psHints / 2
		>>> v.asDict() == {'vStems': [250.0, 5.0], 'blueFuzz': 0.5, 'blueShift': 0.5, 'forceBold': 0.5, 'blueScale': 0.25, 'hStems': [50.0, 45.0]}
		True

		# multiplication with x, y, factor
		# note the h stems are multiplied by .5, the v stems (and blue values) are multiplied by 10
		>>> v = f.psHints * (.5, 10)
		>>> v.asDict() == {'vStems': [5000, 100], 'blueFuzz': 10, 'blueShift': 10, 'forceBold': 0.5, 'blueScale': 5.0, 'hStems': [50.0, 45.0]}
		True

		# multiplication with x, y, factor
		# note the h stems are divided by .5, the v stems (and blue values) are divided by 10
		>>> v = f.psHints / (.5, 10)
		>>> v.asDict() == {'vStems': [50.0, 1.0], 'blueFuzz': 0.10000000000000001, 'blueShift': 0.10000000000000001, 'forceBold': 2.0, 'blueScale': 0.050000000000000003, 'hStems': [200.0, 180.0]}
		True

		>>> v = f.psHints * .333
		>>> v.round()
		>>> v.asDict() == {'vStems': [167, 3], 'blueScale': 0.16650000000000001, 'hStems': [33, 30]}
		True

	"""

if __name__ == "__main__":
	import doctest
	doctest.testmod()

