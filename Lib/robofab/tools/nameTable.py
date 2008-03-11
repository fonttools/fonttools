from warnings import warn
warn("FontLab contains a bug that renders nameTable.py inoperable", Warning)

"""
XXX: FontLab 4.6 contains a bug that renders this module inoperable.

A simple wrapper around the not so simple OpenType
name table API in FontLab.

For more information about the name table see:
http://www.microsoft.com/typography/otspec/name.htm

The PID, EID, LID and NID arguments in the various
methods can be integer values or string values (as
long as the string value matches the key in the lookup
dicts shown below). All values must be strings and all
platform line ending conversion is handled automatically
EXCEPT in the setSpecificRecord method. If you need to do
line ending conversion, the convertLineEndings method
is publicly available. 
"""

from robofab import RoboFabError

	##
	## internal pid constants
	##

UNI = 'unicode'
UNI_INT = 0
MAC = 'macintosh'
MAC_INT = 1
MS = 'microsoft'
MS_INT = 3

	##
	## lookup dicts
	##

def _flipDict(aDict):
	bDict = {}
	for k, v in aDict.items():
		bDict[v] = k
	return bDict

pidName2Int = {
			UNI	:	UNI_INT,
			MAC	:	MAC_INT,
			MS	:	MS_INT,
			}

nidName2Int = {
			'copyright'		:	0,
			'familyName'		:	1,
			'subfamilyName'	:	2,
			'uniqueID'		:	3,
			'fullName'		:	4,
			'versionString'	:	5,
			'postscriptName'	:	6,
			'trademark'		:	7,
			'manufacturer'	:	8,
			'designer'		:	9,
			'description'		:	10,
			'vendorURL'		:	11,
			'designerURL'		:	12,
			'license'		:	13,
			'licenseURL'		:	14,
			# ID 15 is reserved
			'preferredFamily'	:	16,
			'preferredSubfamily'	:	17,
			'compatibleFull'	:	18,
			'sampleText'		:	19,
			'postscriptCID'	:	20
			}

nidInt2Name = _flipDict(nidName2Int)

uniEIDName2Int = {
			"unicode_1.0"		:	0,
			"unicode_1.1"		:	1,
			"iso_10646:1993"	:	2,
			"unicode_2.0_bmp"	:	3,
			"unicode_2.0_full"	:	4,
			}

uniEIDInt2Name = _flipDict(uniEIDName2Int)

uniLIDName2Int = {}

uniLIDInt2Name = _flipDict(uniLIDName2Int)

msEIDName2Int = {
			
			'symbol'		:	0,
			'unicode_bmp_only'	:	1,
			'shift_jis'		:	2,
			'prc'			:	3,
			'big5'			:	4,
			'wansung'		:	5,
			'johab'			:	6,
			# 7 is reserved
			# 8 is reserved
			# 9 is reserved
			'unicode_full_repertoire'	:	7,
			}

msEIDInt2Name = _flipDict(msEIDName2Int)

msLIDName2Int = {
			# need to find a parsable file
			}

msLIDInt2Name = _flipDict(msLIDName2Int)

macEIDName2Int = {
			"roman"		:	0,
			"japanese"		:	1,
			"chinese"		:	2,
			"korean"		:	3,
			"arabic"		:	4,
			"hebrew"		:	5,
			"greek"		:	6,
			"russian"		:	7,
			"rsymbol"		:	8,
			"devanagari"		:	9,
			"gurmukhi"		:	10,
			"gujarati"		:	11,
			"oriya"		:	12,
			"bengali"		:	13,
			"tamil"		:	14,
			"telugu"		:	15,
			"kannada"		:	16,
			"malayalam"		:	17,
			"sinhalese"		:	18,
			"burmese"		:	19,
			"khmer"		:	20,
			"thai"			:	21,
			"laotian"		:	22,
			"georgian"		:	23,
			"armenian"		:	24,
			"chinese"		:	25,
			"tibetan"		:	26,
			"mongolian"		:	27,
			"geez"			:	28,
			"slavic"		:	29,
			"vietnamese"		:	30,
			"sindhi"		:	31,
			"uninterpreted"	:	32,
			}

macEIDInt2Name = _flipDict(macEIDName2Int)

macLIDName2Int = {
			"english"		:	0,
			"french"		:	1,
			"german"		:	2,
			"italian"		:	3,
			"dutch"		:	4,
			"swedish"		:	5,
			"spanish"		:	6,
			"danish"		:	7,
			"portuguese"		:	8,
			"norwegian"		:	9,
			"hebrew"		:	10,
			"japanese"		:	11,
			"arabic"		:	12,
			"finnish"		:	13,
			"inuktitut"		:	14,
			"icelandic"		:	15,
			"maltese"		:	16,
			"turkish"		:	17,
			"croatian"		:	18,
			"chinese"		:	19,
			"urdu"			:	20,
			"hindi"			:	21,
			"thai"			:	22,
			"korean"		:	23,
			"lithuanian"		:	24,
			"polish"		:	25,
			"hungarian"		:	26,
			"estonian"		:	27,
			"latvian"		:	28,
			"sami"			:	29,
			"faroese"		:	30,
			"farsi_persian"	:	31,
			"russian"		:	32,
			"chinese"		:	33,
			"flemish"		:	34,
			"irish gaelic"		:	35,
			"albanian"		:	36,
			"romanian"		:	37,
			"czech"		:	38,
			"slovak"		:	39,
			"slovenian"		:	40,
			"yiddish"		:	41,
			"serbian"		:	42,
			"macedonian"		:	43,
			"bulgarian"		:	44,
			"ukrainian"		:	45,
			"byelorussian"	:	46,
			"uzbek"		:	47,
			"kazakh"		:	48,
			"azerbaijani_cyrillic"	:	49,
			"azerbaijani_arabic"	:	50,
			"armenian"		:	51,
			"georgian"		:	52,
			"moldavian"		:	53,
			"kirghiz"		:	54,
			"tajiki"		:	55,
			"turkmen"		:	56,
			"mongolian_mongolian"	:	57,
			"mongolian_cyrillic"	:	58,
			"pashto"		:	59,
			"kurdish"		:	60,
			"kashmiri"		:	61,
			"sindhi"		:	62,
			"tibetan"		:	63,
			"nepali"		:	64,
			"sanskrit"		:	65,
			"marathi"		:	66,
			"bengali"		:	67,
			"assamese"		:	68,
			"gujarati"		:	69,
			"punjabi"		:	70,
			"oriya"		:	71,
			"malayalam"		:	72,
			"kannada"		:	73,
			"tamil"		:	74,
			"telugu"		:	75,
			"sinhalese"		:	76,
			"burmese"		:	77,
			"khmer"		:	78,
			"lao"			:	79,
			"vietnamese"		:	80,
			"indonesian"		:	81,
			"tagalong"		:	82,
			"malay_roman"	:	83,
			"malay_arabic"	:	84,
			"amharic"		:	85,
			"tigrinya"		:	86,
			"galla"			:	87,
			"somali"		:	88,
			"swahili"		:	89,
			"kinyarwanda_ruanda"	:	90,
			"rundi"		:	91,
			"nyanja_chewa"	:	92,
			"malagasy"		:	93,
			"esperanto"		:	94,
			"welsh"		:	128,
			"basque"		:	129,
			"catalan"		:	130,
			"latin"			:	131,
			"quenchua"		:	132,
			"guarani"		:	133,
			"aymara"		:	134,
			"tatar"			:	135,
			"uighur"		:	136,
			"dzongkha"		:	137,
			"javanese_roman"	:	138,
			"sundanese_roman"	:	139,
			"galician"		:	140,
			"afrikaans"		:	141,
			"breton"		:	142,
			"scottish_gaelic"	:	144,
			"manx_gaelic"		:	145,
			"irish_gaelic"		:	146,
			"tongan"		:	147,
			"greek_polytonic"	:	148,
			"greenlandic"		:	149,
			"azerbaijani_roman"	:	150,
			}

macLIDInt2Name = _flipDict(macLIDName2Int)

	##
	## value converters
	##

def _convertNID2Int(nid):
	if isinstance(nid, int):
		return nid
	return nidName2Int[nid]

def _convertPID2Int(pid):
	if isinstance(pid, int):
		return pid
	return pidName2Int[pid]

def _convertEID2Int(pid, eid):
	if isinstance(eid, int):
		return eid
	pid = _convertPID2Int(pid)
	if pid == UNI_INT:
		return uniEIDName2Int[eid]
	elif pid == MAC_INT:
		return macEIDName2Int[eid]
	elif pid == MS_INT:
		return msEIDName2Int[eid]

def _convertLID2Int(pid, lid):
	if isinstance(lid, int):
		return lid
	pid = _convertPID2Int(pid)
	if pid == UNI_INT:
		return uniLIDName2Int[lid]
	elif pid == MAC_INT:
		return macLIDName2Int[lid]
	elif pid == MS_INT:
		return msLIDName2Int[lid]

def _compareValues(v1, v2):
	if isinstance(v1, str):
		v1 = v1.replace('\r\n', '\n')
	if isinstance(v2, str):
		v2 = v2.replace('\r\n', '\n')
	return v1 == v2

def convertLineEndings(text, convertToMS=False):
	"""convert the line endings in a given text string"""
	if isinstance(text, str):
		if convertToMS:
			text = text.replace('\r\n', '\n')
			text = text.replace('\n', '\r\n')
		else:
			text = text.replace('\r\n', '\n')
	return text
	
	##
	## main object
	##

class NameTable(object):
	
	"""
	An object that allows direct manipulation of the name table of a given font.
	
	For example:
	
	from robofab.world import CurrentFont
	from robofab.tools.nameTable import NameTable
	f = CurrentFont()
	nt = NameTable(f)
	# bluntly set all copyright records to a string
	nt.copyright = "Copyright 2004 RoboFab"
	# get a record
	print nt.copyright
	# set a specific record to a string
	nt.setSpecificRecord(pid=1, eid=0, lid=0, nid=0, value="You Mac-Roman-English folks should know that this is Copyright 2004 RoboFab.")
	# get a record again to show what happens
	# when the records for a NID are not the same
	print nt.copyright
	# look at the code to see what else is possible
	f.update()
	"""
	
	def __init__(self, font):
		self._object = font
		self._pid_eid_lid = {}
		self._records = {}
		self._indexRef = {}
		self._populate()
	
	def _populate(self):
		# keys are tuples (pid, eid, lid, nid)
		self._records = {}
		# keys are tuples (pid, eid, lid, nid), values are indices
		self._indexRef = {}
		count = 0
		for record in self._object.naked().fontnames:
			pid = record.pid
			eid = record.eid
			lid = record.lid
			nid = record.nid
			value = record.name
			self._records[(pid, eid, lid, nid)] = value
			self._indexRef[(pid, eid, lid, nid)] = count
			count = count + 1
	
	def addRecord(self, pid, eid, lid, nidDict=None):
		"""add a record. the optional nidDict is
		a dictionary of NIDs and values. If no
		nidDict is given, the method will make
		an empty entry for ALL public NIDs."""
		if nidDict is None:
			nidDict = dict.fromkeys(nidInt2Name.keys())
			for nid in nidDict.keys():
				nidDict[nid] = ''
		pid = _convertPID2Int(pid)
		eid = _convertEID2Int(pid, eid)
		lid = _convertLID2Int(pid, lid)
		self.removeLID(pid, eid, lid)
		for nid, value in nidDict.items():
			nid = _convertNID2Int(nid)
			self._setRecord(pid, eid, lid, nid, value)
	
	def removePID(self, pid):
		"""remove a PID entry"""
		pid = _convertPID2Int(pid)
		for _pid, _eid, _lid, _nid in self._records.keys():
			if pid == _pid:
				self._removeRecord(_pid, _eid, _lid, _nid)
	
	def removeEID(self, pid, eid):
		"""remove an EID from a PID entry"""
		pid = _convertPID2Int(pid)
		eid = _convertEID2Int(pid, eid)
		for _pid, _eid, _lid, _nid in self._records.keys():
			if pid == _pid and eid == _eid:
				self._removeRecord(_pid, _eid, _lid, _nid)

	def removeLID(self, pid, eid, lid):
		"""remove a LID from a PID entry"""
		pid = _convertPID2Int(pid)
		eid = _convertEID2Int(pid, eid)
		lid = _convertLID2Int(pid, lid)
		for _pid, _eid, _lid, _nid in self._records.keys():
			if pid == _pid and eid == _eid and lid == _lid:
				self._removeRecord(_pid, _eid, _lid, _nid)
	
	def removeNID(self, nid):
		"""remove a NID from ALL PID, EID and LID entries"""
		nid = _convertNID2Int(nid)
		for _pid, _eid, _lid, _nid in self._records.keys():
			if nid == _nid:
				self._removeRecord(_pid, _eid, _lid, _nid)
	
	def setSpecificRecord(self, pid, eid, lid, nid, value):
		"""set a specific record based on the PID, EID, LID and NID
		this method does not do platform lineending conversion"""
		pid = _convertPID2Int(pid)
		eid = _convertEID2Int(pid, eid)
		lid = _convertLID2Int(pid, lid)
		nid = _convertNID2Int(nid)
		# id 18 is mac only, so it should
		# not be set for other PIDs
		if pid != MAC_INT and nid == 18:
			raise RoboFabError, "NID 18 is Macintosh only"
		self._setRecord(pid, eid, lid, nid, value)

	#
	# interface to FL name records
	#
	
	def _removeRecord(self, pid, eid, lid, nid):
		# remove the record from the font
		# note: this won't raise an error if the record doesn't exist
		if self._indexRef.has_key((pid, eid, lid, nid)):
			index = self._indexRef[(pid, eid, lid, nid)]
			del self._object.naked().fontnames[index]
			self._populate()
	
	def _setRecord(self, pid, eid, lid, nid, value):
		# set a record in the font
		if pid != MAC_INT and nid == 18:
			# id 18 is mac only, so it should
			# not be set for other PIDs
			return
		if pid == UNI_INT or pid == MAC_INT:
			value = convertLineEndings(value, convertToMS=False)
		if pid == MS_INT:
			value = convertLineEndings(value, convertToMS=True)
		self._removeRecord(pid, eid, lid, nid)
		from FL import NameRecord
		nr = NameRecord(nid, pid, eid, lid, value)
		self._object.naked().fontnames.append(nr)
		self._populate()
	
	def _setAllRecords(self, nid, value):
		# set nid for all pid, eid and lid records
		done = []
		for _pid, _eid, _lid, _nid in self._records.keys():
			if (_pid, _eid, _lid) not in done:
				self._setRecord(_pid, _eid, _lid, nid, value)
				done.append((_pid, _eid, _lid))
	
	def _getAllRecords(self, nid):
		# this retrieves all nid records and compares
		# them. if the values are all the same, it returns
		# the value. otherwise it returns a list of all values
		# as tuples (pid, eid, lid, value).
		found = []
		for (_pid, _eid, _lid, _nid), value in self._records.items():
			if nid == _nid:
				found.append((_pid, _eid, _lid, value))
		isSame = True
		compare = {}
		for pid, eid, lid, value in found:
			if compare == {}:
				compare = value
				continue
			vC = _compareValues(compare, value)
			if not vC:
				isSame = False
		if isSame:
			found = found[0][-1]
			found = convertLineEndings(found, convertToMS=False)
		return found

	#
	# attrs
	#
	
	def _get_copyright(self):
		nid = 0
		return self._getAllRecords(nid)

	def _set_copyright(self, value):
		nid = 0
		self._setAllRecords(nid, value)

	copyright = property(_get_copyright, _set_copyright, doc="NID 0")

	def _get_familyName(self):
		nid = 1
		return self._getAllRecords(nid)

	def _set_familyName(self, value):
		nid = 1
		self._setAllRecords(nid, value)

	familyName = property(_get_familyName, _set_familyName, doc="NID 1")

	def _get_subfamilyName(self):
		nid = 2
		return self._getAllRecords(nid)

	def _set_subfamilyName(self, value):
		nid = 2
		self._setAllRecords(nid, value)

	subfamilyName = property(_get_subfamilyName, _set_subfamilyName, doc="NID 2")

	def _get_uniqueID(self):
		nid = 3
		return self._getAllRecords(nid)

	def _set_uniqueID(self, value):
		nid = 3
		self._setAllRecords(nid, value)

	uniqueID = property(_get_uniqueID, _set_uniqueID, doc="NID 3")

	def _get_fullName(self):
		nid = 4
		return self._getAllRecords(nid)

	def _set_fullName(self, value):
		nid = 4
		self._setAllRecords(nid, value)

	fullName = property(_get_fullName, _set_fullName, doc="NID 4")

	def _get_versionString(self):
		nid = 5
		return self._getAllRecords(nid)

	def _set_versionString(self, value):
		nid = 5
		self._setAllRecords(nid, value)

	versionString = property(_get_versionString, _set_versionString, doc="NID 5")

	def _get_postscriptName(self):
		nid = 6
		return self._getAllRecords(nid)

	def _set_postscriptName(self, value):
		nid = 6
		self._setAllRecords(nid, value)

	postscriptName = property(_get_postscriptName, _set_postscriptName, doc="NID 6")

	def _get_trademark(self):
		nid = 7
		return self._getAllRecords(nid)

	def _set_trademark(self, value):
		nid = 7
		self._setAllRecords(nid, value)

	trademark = property(_get_trademark, _set_trademark, doc="NID 7")

	def _get_manufacturer(self):
		nid = 8
		return self._getAllRecords(nid)

	def _set_manufacturer(self, value):
		nid = 8
		self._setAllRecords(nid, value)

	manufacturer = property(_get_manufacturer, _set_manufacturer, doc="NID 8")

	def _get_designer(self):
		nid = 9
		return self._getAllRecords(nid)

	def _set_designer(self, value):
		nid = 9
		self._setAllRecords(nid, value)

	designer = property(_get_designer, _set_designer, doc="NID 9")

	def _get_description(self):
		nid = 10
		return self._getAllRecords(nid)

	def _set_description(self, value):
		nid = 10
		self._setAllRecords(nid, value)

	description = property(_get_description, _set_description, doc="NID 10")

	def _get_vendorURL(self):
		nid = 11
		return self._getAllRecords(nid)

	def _set_vendorURL(self, value):
		nid = 11
		self._setAllRecords(nid, value)

	vendorURL = property(_get_vendorURL, _set_vendorURL, doc="NID 11")

	def _get_designerURL(self):
		nid = 12
		return self._getAllRecords(nid)

	def _set_designerURL(self, value):
		nid = 12
		self._setAllRecords(nid, value)

	designerURL = property(_get_designerURL, _set_designerURL, doc="NID 12")

	def _get_license(self):
		nid = 13
		return self._getAllRecords(nid)

	def _set_license(self, value):
		nid = 13
		self._setAllRecords(nid, value)

	license = property(_get_license, _set_license, doc="NID 13")

	def _get_licenseURL(self):
		nid = 14
		return self._getAllRecords(nid)

	def _set_licenseURL(self, value):
		nid = 14
		self._setAllRecords(nid, value)

	licenseURL = property(_get_licenseURL, _set_licenseURL, doc="NID 14")

	def _get_preferredFamily(self):
		nid = 16
		return self._getAllRecords(nid)

	def _set_preferredFamily(self, value):
		nid = 16
		self._setAllRecords(nid, value)

	preferredFamily = property(_get_preferredFamily, _set_preferredFamily, doc="NID 16")

	def _get_preferredSubfamily(self):
		nid = 17
		return self._getAllRecords(nid)

	def _set_preferredSubfamily(self, value):
		nid = 17
		self._setAllRecords(nid, value)

	preferredSubfamily = property(_get_preferredSubfamily, _set_preferredSubfamily, doc="NID 17")

	def _get_compatibleFull(self):
		nid = 18
		return self._getAllRecords(nid)

	def _set_compatibleFull(self, value):
		nid = 18
		self._setAllRecords(nid, value)

	compatibleFull = property(_get_compatibleFull, _set_compatibleFull, doc="NID 18")

	def _get_sampleText(self):
		nid = 19
		return self._getAllRecords(nid)

	def _set_sampleText(self, value):
		nid = 19
		self._setAllRecords(nid, value)

	sampleText = property(_get_sampleText, _set_sampleText, doc="NID 19")

	def _get_postscriptCID(self):
		nid = 20
		return self._getAllRecords(nid)

	def _set_postscriptCID(self, value):
		nid = 20
		self._setAllRecords(nid, value)

	postscriptCID = property(_get_postscriptCID, _set_postscriptCID, doc="NID 20")


if __name__ == "__main__":
	from robofab.world import CurrentFont
	f = CurrentFont()
	nt = NameTable(f)
	print nt.copyright
	f.update()
