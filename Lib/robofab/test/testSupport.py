"""Miscellaneous helpers for our test suite."""


import sys
import os
import types
import unittest


def getDemoFontPath():
	"""Return the path to Data/DemoFont.ufo/."""
	import robofab
	root = os.path.dirname(os.path.dirname(os.path.dirname(robofab.__file__)))
	return os.path.join(root, "Data", "DemoFont.ufo")


def getDemoFontGlyphSetPath():
	"""Return the path to Data/DemoFont.ufo/glyphs/."""
	return os.path.join(getDemoFontPath(), "glyphs")


def _gatherTestCasesFromCallerByMagic():
	# UGLY magic: fetch TestClass subclasses from the globals of our
	# caller's caller.
	frame = sys._getframe(2)
	return _gatherTestCasesFromDict(frame.f_globals)


def _gatherTestCasesFromDict(d):
	testCases = []
	for ob in d.values():
		if isinstance(ob, type) and issubclass(ob, unittest.TestCase):
			testCases.append(ob)
	return testCases

	
def runTests(testCases=None, verbosity=1):
	"""Run a series of tests."""
	if testCases is None:
		testCases = _gatherTestCasesFromCallerByMagic()
	loader = unittest.TestLoader()
	suites = []
	for testCase in testCases:
		suites.append(loader.loadTestsFromTestCase(testCase))

	testRunner = unittest.TextTestRunner(verbosity=verbosity)
	testSuite = unittest.TestSuite(suites)
	testRunner.run(testSuite)

