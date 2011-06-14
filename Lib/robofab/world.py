
import os, sys
from robofab import RoboFabError, version, numberVersion



class RFWorld:
	"""All parameters about platforms, versions and environments included in one object."""
	def __init__(self):
		self.mac = None
		self.pc = None
		self.platform = sys.platform
		self.applicationName = None # name of the application we're running in
		self.name = os.name
		self.version = version	# the robofab version
		self.numberVersion = numberVersion
		self._hasNagged = False
		self._willNag = True
		self._timedOut = False
		self._license = False
		self.run = True

		# get some platform information
		if self.name == 'mac' or self.name == 'posix':
			if self.platform == "darwin":
				self.mac = "X"
			else:
				self.mac = "pre-X"
		elif self.name == 'nt':
			# if you know more about PC & win stuff, add it here!
			self.pc = True
		else:
			raise RoboFabError, "We're running on an unknown platform."
		
		# collect versions
		self.pyVersion = sys.version[:3]
		self.inPython = False 
		self.inFontLab = False
		self.flVersion = None
		self.inGlyphsApp = False
		self.glyphsAppVersion = None

		# are we in FontLab?
		try:
			from FL import fl
			self.applicationName = fl.filename
			self.inFontLab = True
			self.flVersion = fl.version
		except ImportError: pass
		# are we in Glyphs?
		try:
			import objectsGS
			from AppKit import NSBundle
			bundle = NSBundle.mainBundle()
			self.applicationName = bundle.infoDictionary()["CFBundleName"]
			self.inGlyphsApp = True
			self.glyphsAppVersion = bundle.infoDictionary()["CFBundleVersion"]
		except ImportError: pass
		# we are in NoneLab
		if not self.inFontLab:
			self.inPython = True

		# see if we have DialogKit
		self.supportsDialogKit = False

	def __repr__(self):
		return "[Robofab is running on %s. Python version: %s, Mac stuff: %s, PC stuff: %s, FontLab stuff: %s, FLversion: %s]"%(self.platform, self.pyVersion, self.mac, self.pc, self.inFontLab, self.flVersion)


world = RFWorld()

lineBreak = os.linesep

if world.inFontLab:
	from robofab.interface.all.dialogs import SelectFont, SelectGlyph
	from robofab.objects.objectsFL import CurrentFont, CurrentGlyph, RFont, RGlyph, OpenFont, NewFont, AllFonts
	lineBreak = "\n"
elif world.inGlyphsApp:
	from robofab.objects.objectsFL import CurrentFont, CurrentGlyph, RFont, RGlyph, OpenFont, NewFont, AllFonts
elif world.inPython:
	from robofab.objects.objectsRF import CurrentFont, CurrentGlyph, RFont, RGlyph, OpenFont, NewFont, AllFonts



if __name__ == "__main__":
	f = RFWorld()
	print f
