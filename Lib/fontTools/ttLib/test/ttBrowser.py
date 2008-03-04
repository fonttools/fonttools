"""Mac-OS9-only TrueType browser window, deprecated and no longer maintained."""

from fontTools import ttLib
from fontTools.ttLib import macUtils
import macfs
import PyBrowser
import W, Lists
import os
import ATM
import numpy
import Qd
from rf.views.wGlyphList import GlyphList


class TableBrowser:
	
	def __init__(self, path=None, ttFont=None, res_index=None):
		W.SetCursor('watch')
		if path is None:
			self.ttFont = ttFont
			self.filename = "????"
		else:
			self.ttFont = ttLib.TTFont(path, res_index)
			if res_index is None:
				self.filename = os.path.basename(path)
			else:
				self.filename = os.path.basename(path) + " - " + str(res_index)
		self.currentglyph = None
		self.glyphs = {}
		self.buildinterface()
	
	def buildinterface(self):
		buttonwidth = 120
		glyphlistwidth = 150
		hmargin = 10
		vmargin = 8
		title = self.filename
		tables = self.ttFont.keys()
		tables.sort()
		self.w = w = W.Window((500, 300), title, minsize = (400, 200))
		w.browsetablebutton = W.Button((hmargin, 32, buttonwidth, 16), "Browse tableä", 
				self.browsetable)
		w.browsefontbutton = W.Button((hmargin, vmargin, buttonwidth, 16), "Browse fontä", 
				self.browsefont)
		w.tablelist = W.List((hmargin, 56, buttonwidth, -128), tables, self.tablelisthit)
		
		w.divline1 = W.VerticalLine((buttonwidth + 2 * hmargin, vmargin, 1, -vmargin))
		
		gleft = buttonwidth + 3 * hmargin + 1
		
		hasGlyfTable = self.ttFont.has_key('glyf')
		
		glyphnames = self.ttFont.getGlyphNames2()  # caselessly sorted glyph names
		
		if hasGlyfTable:
			w.glyphlist = GlyphList((gleft, 56, glyphlistwidth, -vmargin), 
					glyphnames, self.glyphlisthit)
			
			w.divline2 = W.VerticalLine((buttonwidth + glyphlistwidth + 4 * hmargin + 2, 
					vmargin, 1, -vmargin))
			
			yMin = self.ttFont['head'].yMin
			yMax = self.ttFont['head'].yMax
			w.gviewer = GlyphViewer((buttonwidth + glyphlistwidth + 5 * hmargin + 3, 
					vmargin, -hmargin, -vmargin), yMin, yMax)
			
			w.showpoints = W.CheckBox((gleft, vmargin, glyphlistwidth, 16), "Show points", 
					self.w.gviewer.toggleshowpoints)
			w.showpoints.set(self.w.gviewer.showpoints)
			w.showlines = W.CheckBox((gleft, vmargin + 24, glyphlistwidth, 16), "Show lines",
					self.w.gviewer.toggleshowlines)
			w.showlines.set(self.w.gviewer.showlines)
		else:
			w.glyphlist = GlyphList((gleft, 56, glyphlistwidth, -vmargin), 
					glyphnames)
			w.noGlyphTable = W.TextBox((gleft, vmargin, -20, 20), "no 'glyf' table found")
		
		
		w.setdefaultbutton(w.browsetablebutton)
		
		w.tocurrentfont = W.Button((hmargin, -120, buttonwidth, 16), "Copy to current font", self.copytocurrentfont)
		w.fromcurrentfont = W.Button((hmargin, -96, buttonwidth, 16), "Copy from current font", self.copyfromcurrentfont)
		w.saveflat = W.Button((hmargin, -72, buttonwidth, 16), "Save as flat fileä", self.saveflat)
		w.savesuitcasebutton = W.Button((hmargin, -48, buttonwidth, 16), "Save as suitcaseä", self.savesuitcase)
		w.savexmlbutton = W.Button((hmargin, -24, buttonwidth, 16), "Save as XMLä", self.saveXML)
		
		w.open()
		w.browsetablebutton.enable(0)
	
	def browsetable(self):
		self.tablelisthit(1)
	
	def browsefont(self):
		PyBrowser.Browser(self.ttFont)
	
	def copytocurrentfont(self):
		pass
		
	def copyfromcurrentfont(self):
		pass
		
	def saveflat(self):
		path = putfile("Save font as flat file:", self.filename, ".TTF")
		if path:
			W.SetCursor('watch')
			self.ttFont.save(path)
	
	def savesuitcase(self):
		path = putfile("Save font as suitcase:", self.filename, ".suit")
		if path:
			W.SetCursor('watch')
			self.ttFont.save(path, 1)
	
	def saveXML(self):
		path = putfile("Save font as XML text file:", self.filename, ".ttx")
		if path:
			W.SetCursor('watch')
			pb = macUtils.ProgressBar("Saving %s as XMLä" % self.filename)
			try:
				self.ttFont.saveXML(path, pb)
			finally:
				pb.close()
	
	def glyphlisthit(self, isDbl):
		sel = self.w.glyphlist.getselectedobjects()
		if not sel or sel[0] == self.currentglyph:
			return
		self.currentglyph = sel[0]
		if self.glyphs.has_key(self.currentglyph):
			g = self.glyphs[self.currentglyph]
		else:
			g = Glyph(self.ttFont, self.currentglyph)
			self.glyphs[self.currentglyph] = g
		self.w.gviewer.setglyph(g)
	
	def tablelisthit(self, isdbl):
		if isdbl:
			for tag in self.w.tablelist.getselectedobjects():
				table = self.ttFont[tag]
				if tag == 'glyf':
					W.SetCursor('watch')
					for glyphname in self.ttFont.getGlyphOrder():
						try:
							glyph = table[glyphname]
						except KeyError:
							pass # incomplete font, oh well.
				PyBrowser.Browser(table)
		else:
			sel = self.w.tablelist.getselection()
			if sel:
				self.w.browsetablebutton.enable(1)
			else:
				self.w.browsetablebutton.enable(0)


class Glyph:
	
	def __init__(self, ttFont, glyphName):
		ttglyph = ttFont['glyf'][glyphName]
		self.iscomposite = ttglyph.numberOfContours == -1
		self.width, self.lsb = ttFont['hmtx'][glyphName]
		if ttglyph.numberOfContours == 0:
			self.xMin = 0
			self.contours = []
			return
		self.xMin = ttglyph.xMin
		coordinates, endPts, flags = ttglyph.getCoordinates(ttFont['glyf'])
		self.contours = []
		self.flags = []
		startpt = 0
		for endpt in endPts:
			self.contours.append(numpy.array(coordinates[startpt:endpt+1]))
			self.flags.append(flags[startpt:endpt+1])
			startpt = endpt + 1
	
	def getcontours(self, scale, move):
		contours = []
		for i in range(len(self.contours)):
			contours.append(((self.contours[i] * numpy.array(scale) + move), self.flags[i]))
		return contours


class GlyphViewer(W.Widget):
	
	def __init__(self, possize, yMin, yMax):
		W.Widget.__init__(self, possize)
		self.glyph = None
		extra = 0.02 * (yMax-yMin)
		self.yMin, self.yMax = yMin - extra, yMax + extra
		self.showpoints = 1
		self.showlines = 1
	
	def toggleshowpoints(self, onoff):
		self.showpoints = onoff
		self.SetPort()
		self.draw()
	
	def toggleshowlines(self, onoff):
		self.showlines = onoff
		self.SetPort()
		self.draw()
	
	def setglyph(self, glyph):
		self.glyph = glyph
		self.SetPort()
		self.draw()
		
	def draw(self, visRgn=None):
		# This a HELL of a routine, but it's pretty damn fast...
		import Qd
		if not self._visible:
			return
		Qd.EraseRect(Qd.InsetRect(self._bounds, 1, 1))
		cliprgn = Qd.NewRgn()
		savergn = Qd.NewRgn()
		Qd.RectRgn(cliprgn, self._bounds)
		Qd.GetClip(savergn)
		Qd.SetClip(cliprgn)
		try:
			if self.glyph:
				l, t, r, b = Qd.InsetRect(self._bounds, 1, 1)
				height = b - t
				scale = float(height) / (self.yMax - self.yMin)
				topoffset = t + scale * self.yMax
				width = scale * self.glyph.width
				lsb = scale * self.glyph.lsb
				xMin = scale * self.glyph.xMin
				# XXXX this is not correct when USE_MY_METRICS is set in component!
				leftoffset = l + 0.5 * (r - l - width)
				gleftoffset = leftoffset - xMin + lsb
				if self.showlines:
					Qd.RGBForeColor((0xafff, 0xafff, 0xafff))
					# left sidebearing
					Qd.MoveTo(leftoffset, t)
					Qd.LineTo(leftoffset, b - 1)
					# right sidebearing
					Qd.MoveTo(leftoffset + width, t)
					Qd.LineTo(leftoffset + width, b - 1)
					# baseline
					Qd.MoveTo(l, topoffset)
					Qd.LineTo(r - 1, topoffset)
					
					# origin
					Qd.RGBForeColor((0x5fff, 0, 0))
					Qd.MoveTo(gleftoffset, topoffset - 16)
					Qd.LineTo(gleftoffset, topoffset + 16)
					# reset color
					Qd.RGBForeColor((0, 0, 0))
				
				if self.glyph.iscomposite:
					Qd.RGBForeColor((0x7fff, 0x7fff, 0x7fff))
				
				ATM.startFillATM()
				contours = self.glyph.getcontours((scale, -scale), (gleftoffset, topoffset))
				for contour, flags in contours:
					currentpoint = None
					done_moveto = 0
					i = 0
					nPoints = len(contour)
					while i < nPoints:
						pt = contour[i]
						if flags[i]:
							# onCurve
							currentpoint = lineto(pt, done_moveto)
						else:
							if not currentpoint:
								if not flags[i-1]:
									currentpoint = 0.5 * (contour[i-1] + pt)
								else:
									currentpoint = contour[i-1]
							if not flags[(i+1) % nPoints]:
								endPt = 0.5 * (pt + contour[(i+1) % nPoints])
							else:
								endPt = contour[(i+1) % nPoints]
								i = i + 1
							# offCurve
							currentpoint = qcurveto(currentpoint, 
									pt, endPt, done_moveto)
						done_moveto = 1
						i = i + 1
					ATM.fillClosePathATM()
				ATM.endFillATM()
				# draw point markers
				if self.showpoints:
					for contour, flags in contours:
						Qd.RGBForeColor((0, 0xffff, 0))
						for i in range(len(contour)):
							(x, y) = contour[i]
							onCurve = flags[i] & 0x1
							if onCurve:
								Qd.PaintRect(Qd.InsetRect((x, y, x, y), -2, -2))
							else:
								Qd.PaintOval(Qd.InsetRect((x, y, x, y), -2, -2))
							Qd.RGBForeColor((0xffff, 0, 0))
						Qd.RGBForeColor((0, 0, 0))
			Qd.FrameRect(self._bounds)
		finally:
			Qd.SetClip(savergn)
			Qd.DisposeRgn(cliprgn)
			Qd.DisposeRgn(savergn)


extensions = [".suit", ".xml", ".ttx", ".TTF", ".ttf"]

def putfile(prompt, filename, newextension):
	for ext in extensions:
		if filename[-len(ext):] == ext:
			filename = filename[:-len(ext)] + newextension
			break
	else:
		filename = filename + newextension
	fss, ok = macfs.StandardPutFile(prompt, filename)
	if ok:
		return fss.as_pathname()


def lineto(pt, done_moveto):
	x, y = pt
	if done_moveto:
		ATM.fillLineToATM((x, y))
	else:
		ATM.fillMoveToATM((x, y))
	return pt

def qcurveto(pt0, pt1, pt2, done_moveto):
	if not done_moveto:
		x0, y0 = pt0
		ATM.fillMoveToATM((x0, y0))
	x1a, y1a = pt0 + 0.6666666666667 * (pt1 - pt0)
	x1b, y1b = pt2 + 0.6666666666667 * (pt1 - pt2)
	x2, y2 = pt2
	ATM.fillCurveToATM((x1a, y1a), (x1b, y1b), (x2, y2))
	return pt2


def browseTTFont():
	fss, ok = macfs.StandardGetFile()
	if not ok:
		return
	path = fss.as_pathname()
	indices = macUtils.getSFNTResIndices(path)
	if indices:
		for i in indices:
			TableBrowser(path, res_index=i)
	else:
		TableBrowser(path)


if __name__ == "__main__":
	browseTTFont()

