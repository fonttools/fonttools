from warnings import warn
warn("featureLib.py is deprecated.", DeprecationWarning)

"""
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 

W A R N I N G

This is work in progress, a fast moving target.

XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
"""



"""FeatureLib

An attempt to get OpenType features written like Adobe's FDK
Feature descriptions to export into UFO and back. FontLab has
an interface for writing the features. FeatureLib offers some
tools to store the feature text, or to try interpretating it.

There seem to be no clever ways to make an interpreter for
feature speak based on abstract descriptions of the language:
	No Backus Naur Form description is available.
	No python interpreter
	No C source code available to the public
	
So rather than go for the complete image, this implementation
is incomplete and probably difficult to extend. But it can
interpret the following features and write them back into the
right format and order:

	feature xxxx {
		<something>
	} xxxx;
	
	# lines with comment
	@classname = [name1 name2 etc];	
	sub x x x by y y;
	sub x from [a b c];
	pos xx yy 100;

When interpret = False is passed as parameter it won't attempt to
interpret the feature text and just store it. Uninterpreted feature
text is exported as an url encoded string to ensure roundtripping
when the data is stored in a plist:
	%09feature%20smcp%20%7B
This makes the feature text safe for storage in plist form without
breaking anything.

Also, if interpretation fails for any  reason, the feature text is stored
so data should be lost.

To do:
	- make it possible to read a .fea file and spit into seperate items
	- test with more and different features from fontlab.

"""


DEBUG = True

DEFAULTNAME = "xxxx"



__all__ = ["Feature", "FeatureSet", "many_to_many", "one_from_many",
		"simple_pair", "extractFLFeatures", "putFeaturesLib", "getFeaturesLib"]


# substition types
# are there official opentype substitution titles for this?
many_to_many = 0
one_from_many = 1

# kern types
simple_pair = 0

# lib key for features
featureLibKey = "org.robofab.features"


class Feature:

	"""Feature contains one single feature, of any flavor.
		Read from feature script
		Write to feature script
		Read from simple dict
		Write to simple dict
		Parse  some of the lines
		Accept edits and additions
	"""
	
	def __init__(self, name=None, text=None, data=None, interpret=True):
		if  name is not None:
			self.name = name
		else:
			self.name = DEFAULTNAME
		self._sub = []
		self._pos = []
		self._comment = []
		self._feature = []
		self._classes = []
		self._tab = " "*4
		self._text = None
		if text is not None:
			self.readFeatureText(text, interpret)
		elif data is not None:
			self.fromDict(data)
	
	def __repr__(self):
		return "<Robofab Feature object '%s'>"%(self.name)
	
	def addSub(self, itemsIn, itemsOut, subType=many_to_many):
		"""Add a substitution statement"""
		self._sub.append((subType, itemsIn, itemsOut))
	
	def addPos(self, itemOne, itemTwo, offset):
		"""Add a positioning statement"""
		self._pos.append((itemOne, itemTwo, offset))
		
	def hasSubs(self):
		"""Return True if this feature has substitutions defined."""
		return len(self._sub) > 0

	def hasPos(self):
		"""Return True if this feature has positioning defined."""
		return len(self._pos) > 0

	def readFeatureText(self, featureText, interpret=True):
		"""Read the feature text and try to make sense of it.

		Note: Should you want to preserve the actual featuretext
		rather than the intrepreted data, set interpret = False

		In case the feature text isn't properly interpreted
		(possible) or because the feature text is hand edited
		and you just want it to round trip to UFO.
		"""
		if interpret:
			if featureText is not None:
				self.parse(featureText)
		else:
			self._text = featureText
	
	def parse(self, featureText):
		"""bluntly split the lines of feature code as they come from fontlab
		This doesn't by any means parse all of the possible combinations 
		in a .fea file. It parses the pos and sub lines defines within a feature.
		Something higher up should parse the seperate features from the .fea.
		
		It doesn't check for validity of the lines.
		"""
		lines = featureText.split("\n")
		count = 0
		featureOpened = False
		interpretOK = True
		for l in lines:
			#
			# run through all lines
			#
			p = l.strip()
			if len(p)==0:continue
			if p[-1] == ";":
				p = p[:-1]
			p = p.split(" ")
			count += 1
			
			#
			# plain substitutions
			# example:
			# sub @class496 by @class497;
			# sub aring from [amacron aringacute adieresis aacute];
			# sub s s by s_s;
			#
			if p[0] == "sub":
				if "by" in p:
					# sub xx by xx;
					self.addSub(p[1:p.index("by")], p[p.index("by")+1:], many_to_many)
				elif "from" in p:
					# sub x from [zzz];
					theList = " ".join(p[p.index("from")+1:])[1:-1].split(" ")
					self.addSub(p[1:p.index("from")], theList, one_from_many)
			
			#
			# plain kerning
			# example:
			# pos Yacute A -215;
			#
			elif p[0] == "pos":
				items = p[1:-1]
				value = int(p[-1])
				self._pos.append((simple_pair, items, value))
			
			#
			# comments
			#
			elif p[0] == "#":
				# comment?
				self._comment.append(" ".join(p[1:]))
			
			#
			# features beginning or feature within feature
			#
			elif p[0] == "feature":
				# comment?
				if  not featureOpened:
					# ah, it's a fully wrapped description
					if len(p[1]) == 4 and p[2] == "{":
						self.name = p[1]
					else:
						print 'uh oh xxxxx', p
					featureOpened = True
				else:
					# it's an unwrapped (from fontlab) description
					self._feature.append(p[1:])
			
			#
			# feature ending
			#
			elif p[0] == "}" and p[1] == self.name:
				featureOpened = False
			
			#
			# special cases (humph)
			#
			
			#
			# special case: class definitions
			#
			elif "=" in p:
				# check for class defenitions
				# example:
				# @MMK_L_A = [A Aacute];
				# @S = [S Sacute Scedille]
				equalOperatorIndex = p.index("=")
				classNames = p[:equalOperatorIndex]
				# get the seperate names from the list:
				classMembers = " ".join(p[equalOperatorIndex+1:])[1:-1].split(" ")
				self._classes.append((classNames, classMembers))
			
			#
			# we can't make sense of it, store the feature text instead then..
			#
			else:
				print "Feature interpreter error:", p
				interpretOK = False
			if not interpretOK:
				if DEBUG:
					"Couldn't interpret all feature lines, storing the text as well."
				self._text = featureText
				
				
	def writeFeatureText(self, wrapped=True):
		"""return the feature as an OpenType feature string 
		wrapped = True: wrapped with featurename { feature items; }
		wrapped = False:  similar to that produced by FontLab
		"""
		
		text = []
		if self._text:
			# if literal feature text is stored: use that
			# XXXX how to handle is there are new, manually added feature items?
			# XXXX should the caller clear the text first?
			from urllib import unquote
			return unquote(self._text)
		if wrapped:
			text.append("feature %s {"%self.name)
		if self._comment:
			text.append(" # %s"%(" ".join(self._comment)))
		if self._feature:
			for f in self._feature:
				text.append("  feature %s;"%(" ".join(f)))
		if self._classes:
			#
			# first dump any in-feature class definitions
			#
			for classNames, classMembers in self._classes:
				text.append(self._tab+"%s = [%s];"%(" ".join(classNames), " ".join(classMembers)))
		if self._pos:
			#
			# run through the list twice to get the class kerns first
			#
			for posType, names, value in self._pos:
				text.append(self._tab+"pos %s %d;"%(" ".join(names), value))
		if self._sub:
			for (subType, stuffIn, stuffOut) in self._sub:
				if subType == many_to_many:
					text.append(self._tab+"sub %s by %s;"%((" ".join(stuffIn), " ".join(stuffOut))))
				elif subType == one_from_many:
					text.append(self._tab+"sub %s from [%s];"%((" ".join(stuffIn), " ".join(stuffOut))))
		if wrapped:
			text.append("} %s;"%self.name)
		final = "\n".join(text)+"\n"
		return final
		
	def asDict(self):
		"""Return the data of this feature as a plist ready dictionary"""
		data = {}
		data['name'] = self.name
		if self._comment:
			data['comment'] = self._comment
		if self._sub:
			data["sub"] = self._sub
		if self._pos:
			data["pos"] = self._pos
		if self._feature:
			data["feature"] = self._feature
		if self._text:
			from urllib import quote
			data['text'] = quote(self._text)
		return data
		
	def fromDict(self, aDict):
		"""Read the data from a dict."""
		self.name = aDict.get("name", DEFAULTNAME)
		self._sub = aDict.get("sub", [])
		self._pos = aDict.get("pos", [])
		self._feature = aDict.get("feature", [])
		self._comment = aDict.get("comment", [])
		text = aDict.get('text', None)
		if text is not None:
			from urllib import unquote
			self._text = unquote(text)
	

class FeatureSet(dict):
	
	"""A dict to combine all features, and write them to various places"""
	
	def __init__(self, interpret=True):
		self.interpret = interpret
		
	def readFL(self, aFont):
		"""Read the feature stuff from a RFont in FL context.
		This can be structured better I think, but let's get 
		something working first.
		"""
		for name  in aFont.getOTFeatures():
			if DEBUG:
				print 'reading %s from %s'%(name, aFont.info.fullName)
			self[name] = Feature(name, aFont.getOTFeature(name), interpret = self.interpret)
			self.changed = True
	
	def writeFL(self, aFont, featureName=None):
		"""Write one or all features back"""
		if featureName == None:
			names = self.keys()
		else:
			names = [featureName]
		for n in names:
			text = self[n].writeFeatureText(wrapped=False)
			if DEBUG:
				print "writing feature %s"%n
				print '- '*30
				print `text`
				print `self[n]._text`
				print '- '*30
			aFont.setOTFeature(n, text)
	
	def writeLib(self, aFont):
		aFont.lib[featureLibKey] = self.asDict()
		
	def readLib(self, aFont):
		"""Read the feature stuff from the font lib.
		Rather than add all this to yet another file in the UFO,
		just store it in the lib. UFO users will be able to read
		the data anyway.
		"""
		stuff = aFont.lib.get(featureLibKey, None)
		if stuff is None:
			if DEBUG:
				print "No features found in this lib.."
				return
		self.clear()
		self.update(stuff)
	
	def append(self, aFeature):
		"""Append a feature object to this set"""
		self[aFeature.name] = aFeature
		if DEBUG:
			print "..added %s to FeatureSet"%aFeature.name
		
	def newFeature(self, name):
		"""Add a new feature and return it"""
		self[name] = Feature(name)
		return self[name]
	
	def update(self, aDict):
		"""Accept a dictionary with all features written out as dicts.
		Ready for data read from plist
		"""
		for name, feature in aDict.items():
			self[name] = Feature(data=feature, interpret=self.interpret)
		
	def asDict(self):
		"""Return a dict with all features also written out as dicts. Not the same as self.
		Data is ready for writing to plist
		"""
		data = {}
		for name, feature in self.items():
			data[name] = feature.asDict()
		return data
	
	
# convenience functions
	
def extractFLFeatures(aFont, interpret=True):
	"""FontLab specific: copy features from the font to the font.lib"""
	fs = FeatureSet(interpret = interpret)
	fs.readFL(aFont)
	fs.writeLib(aFont)
	
def putFeaturesLib(aFont, featureSet):
	"""Put the features in the appropriate place in the font.lib"""
	featureSet.writeLib(aFont)
	
def getFeaturesLib(aFont, interpret=True):
	"""Get the featureset from a lib."""
	fs = FeatureSet(interpret = interpret)
	fs.readLib(aFont)
	return fs


if __name__ == "__main__":
	
	# examples
	
	print "-"*10, "sub many by many"
	# a regular ligature feature
	dligtext = """feature dlig {
		 # Latin
		@MMK_L_A = [A Aacute];
		    sub I J by IJ;
		    sub i j by ij;
		    sub s s by s_s;
		} dlig;
	"""
	
	feat1 = Feature(text=dligtext)
	print feat1.asDict()
	print
	print feat1.writeFeatureText()
	
	
	print "-"*10, "sub one from many"
	# aalt one from many substitution
	aalttext = """feature aalt {
			sub aring from [amacron acircumflex adblgrave a agrave abreve acaron atilde aogonek aringacute adieresis aacute];
			sub utilde from [umacron uring uacute udieresisacute ucircumflex uhorn udblgrave udieresis uhungarumlaut udieresisgrave ugrave ubreve uogonek ucaron u];
			sub Hcircumflex from [H.sc Hcedilla.sc Hcircumflex.sc Hdotaccent H Hcedilla Hdieresis Hdieresis.sc Hdotaccent.sc];
			sub pdotaccent from [p pacute];
		} aalt;
	"""
	
	feat2 = Feature(text=aalttext)
	print feat2.asDict()
	print
	print feat2.writeFeatureText()
	

	print "-"*10, "kerning"
	# kern and positioning
	kerntext = """	feature kern {
			 # Latin
			    pos Yacute A -215;
			    pos Yacute B -30;
			    pos Yacute C -100;
			    pos Yacute D -50;
			    pos Yacute E -35;
			    pos Yacute F -35;
			    pos Yacute G -80;
			    pos Yacute H -25;
			# -- kerning classes
			@MMK_L_A = [A Aacute];
			@MMK_R_C = [C Ccedilla];
		
		} kern;
	"""
	
	feat3 = Feature(text=kerntext)
	print feat3.asDict()
	print
	print feat3.writeFeatureText()
	
	
	
	
	print "-"*10, "something with groups in it"
	# references to groups  are treated like any other
	grouptext = """	feature smcp {
			 # Latin
			sub @class496 by @class497;
		} smcp;
	"""
	
	# Feature doesn't interpret the text in this example
	# when interpret = False is  given as parameter,
	# the feature code is stored and reproduced exactly.
	# But then you have to specify the name of the feature
	# otherwise it will default and overwrite other features
	# with the same default name.

	feat4 = Feature(name="smcp", text=grouptext, interpret = False)

	print feat4.asDict()
	print
	print feat4.writeFeatureText()
	

	print "-"*10, "store the feature set in the lib"
	# now create a feature  set to dump all features in the lib

	set = FeatureSet()
	set.append(feat1)
	set.append(feat2)
	set.append(feat3)
	set.append(feat4)
	
	from robofab.world import NewFont
	testFont = NewFont()
	set.writeLib(testFont)
	print testFont.lib[featureLibKey]

	print "-"*10, "read the feature set from the lib again"
	
	notherSet = FeatureSet()
	notherSet.readLib(testFont)
	for name, feat in notherSet.items():
		print name, feat
		


