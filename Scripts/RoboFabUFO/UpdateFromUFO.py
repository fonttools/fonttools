#FLM: Compare and update from UFO


"""
	Compare and Update from UFO.
	If the .vfb has a UFO in the same folder, and the names match
		<fontname>.vfb -> <fontname>.ufo
	compare the digests for each glyph in the vfb and the ufo
	update the glyph in the vfb if there is no match
	don't touch groups, kerning, other values.
	
	evb 08

"""


from robofab.interface.all.dialogs import AskYesNoCancel
from robofab.interface.all.dialogs import Message

from robofab.world import AllFonts, OpenFont, CurrentFont
from robofab.objects.objectsRF import RFont as _RFont
from robofab.tools.glyphNameSchemes import glyphNameToShortFileName
from robofab.glifLib import GlyphSet
from robofab.objects.objectsFL import RGlyph
from robofab.ufoLib import makeUFOPath, UFOWriter
from robofab.interface.all.dialogs import ProgressBar

from dialogKit import *
from sets import Set

import os

class UpdateFromUFODialogDialog(object):
	
	def __init__(self, ufo, vfb):
		self.ufo = ufo
		self.vfb = vfb
		self.updateNames = []
		self.w = ModalDialog((200, 400), 'Update Font From UFO', okCallback=self.okCallback)
		self.w.list = List((5, 70, -5, -100), ['Comparing VFB', "to its UFO.", "Click Compare to begin."], callback=self.listHitCallback)
		self.w.updateButton = Button((10, 10, 90, 20), 'Update', callback=self.updateCallback)
		self.w.updateAllButton = Button((10, 40, 90, 20), 'Update All', callback=self.updateAllCallback)
		self.w.checkButton = Button((110, 10, -10, 50), 'Compare', callback=self.checkCallback)
		self.w.open()
	
	def okCallback(self, sender):
		print 'this final list contains:', list(self.w.list)
	
	def listHitCallback(self, sender):
		selection = sender.getSelection()
		if not selection:
			selectedItem = None
		else:
			selectionIndex = selection[0]
			selectedItem = sender[selectionIndex]
		print 'selection:', selectedItem

	def updateAllCallback(self, sender):
		print "Update all glyphs"
		names = self.updateNames[:]
		for n in self.updateNames:
			self.updateGlyph(n)
			names.remove(n)
			self.w.list.set(names)
		self.w.list.setSelection([-1])
	
	def updateCallback(self, sender):
		print "Update selected glyph"
		names = []
		for index in self.w.list.getSelection():
			names.append(self.updateNames[index])
		for n in names:
			self.updateGlyph(n)
			self.updateNames.remove(n)
			self.w.list.set(self.updateNames)
		self.w.list.setSelection([-1])
	
	def checkCallback(self, sender):
		print "checking fonts"
		self.analyseFonts()

	def analyseFonts(self):
		ufoDigests = {}
		print "calculating UFO digests"
		ufoNames = self.ufo.keys()
		vfbNames = self.vfb.keys()
		self.w.list.set([])
		self.updateNames = []
		for n in ufoNames:
			if n not in vfbNames:
				self.updateNames.append(n)
				self.updateNames.sort()
				self.w.list.set(self.updateNames)
				self.w.list.setSelection([-1])
		relevantNames = Set(ufoNames)&Set(vfbNames)
		names = list(relevantNames)
		names.sort()
		for name in names:
			print name
			ufoDigest = self.ufo[name]._getDigest()
			vfbDigest = self.vfb[name]._getDigest()
			if ufoDigest != vfbDigest:
				self.updateNames.append(name)
				self.w.list.set(self.updateNames)
				self.w.list.setSelection([-1])
	
	def updateGlyph(self, name):
		print "importing", name
		self.vfb[name].clear()
		self.vfb.insertGlyph(self.ufo[name], name=name)
		self.vfb[name].width = self.ufo[name].width
		self.vfb[name].note = self.ufo[name].note
		self.vfb[name].psHints.update(self.ufo[name].psHints)
		self.vfb[name].mark = 50
		self.vfb[name].update()


if __name__ == "__main__":
	
	
	f = CurrentFont()
	ufoPath = f.path.replace(".vfb", ".ufo")
	if os.path.exists(ufoPath):
		print "there is a ufo for this font at", ufoPath
		ufo = _RFont(ufoPath)
		UpdateFromUFODialogDialog(ufo, f)
	f.update()



	print "done"