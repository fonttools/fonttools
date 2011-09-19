"""Various low level data validators."""

import os
import calendar

# ----------------------
# fontinfo.plist Support
# ----------------------

# Data Validators

def fontInfoTypeValidator(value, typ):
	"""
	Generic. (Added at version 2.)
	"""
	return isinstance(value, typ)

def fontInfoIntListValidator(values, validValues):
	"""
	Generic. (Added at version 2.)
	"""
	if not isinstance(values, (list, tuple)):
		return False
	valuesSet = set(values)
	validValuesSet = set(validValues)
	if len(valuesSet - validValuesSet) > 0:
		return False
	for value in values:
		if not isinstance(value, int):
			return False
	return True

def fontInfoNonNegativeIntValidator(value):
	"""
	Generic. (Added at version 3.)
	"""
	if not isinstance(value, int):
		return False
	if value < 0:
		return False
	return True

def fontInfoNonNegativeNumberValidator(value):
	"""
	Generic. (Added at version 3.)
	"""
	if not isinstance(value, (int, float)):
		return False
	if value < 0:
		return False
	return True

def fontInfoDictValidator(value, prototype):
	"""
	Generic. (Added at version 3.)
	"""
	# not a dict
	if not isinstance(value, dict):
		return False
	# missing required keys
	for key, (typ, required) in prototype.items():
		if not required:
			continue
		if key not in value:
			return False
	# unknown keys
	for key in value.keys():
		if key not in prototype:
			return False
	# incorrect types
	for key, v in value.items():
		prototypeType = prototype[key][0]
		if not isinstance(v, prototypeType):
			return False
	return True

def fontInfoStyleMapStyleNameValidator(value):
	"""
	Version 2+.
	"""
	options = ["regular", "italic", "bold", "bold italic"]
	return value in options

def fontInfoOpenTypeGaspRangeRecordsValidator(value):
	"""
	Version 3+.
	"""
	if not isinstance(value, list):
		return False
	if len(value) == 0:
		return False
	validBehaviors = [0, 1, 2, 3]
	dictPrototype = dict(rangeMaxPPEM=(int, True), rangeGaspBehavior=(list, True))
	ppemOrder = []
	for rangeRecord in value:
		if not fontInfoDictValidator(rangeRecord, dictPrototype):
			return False
		ppem = rangeRecord["rangeMaxPPEM"]
		behavior = rangeRecord["rangeGaspBehavior"]
		ppemValidity = fontInfoNonNegativeIntValidator(ppem)
		if not ppemValidity:
			return False
		behaviorValidity = fontInfoIntListValidator(behavior, validBehaviors)
		if not behaviorValidity:
			return False
		ppemOrder.append(ppem)
	if ppemOrder != sorted(ppemOrder):
		return False
	if ppemOrder[-1] != 0xFFFF:
		return False
	return True

def fontInfoOpenTypeHeadCreatedValidator(value):
	"""
	Version 2+.
	"""
	# format: 0000/00/00 00:00:00
	if not isinstance(value, basestring):
		return False
	# basic formatting
	if not len(value) == 19:
		return False
	if value.count(" ") != 1:
		return False
	date, time = value.split(" ")
	if date.count("/") != 2:
		return False
	if time.count(":") != 2:
		return False
	# date
	year, month, day = date.split("/")
	if len(year) != 4:
		return False
	if len(month) != 2:
		return False
	if len(day) != 2:
		return False
	try:
		year = int(year)
		month = int(month)
		day = int(day)
	except ValueError:
		return False
	if month < 1 or month > 12:
		return False
	monthMaxDay = calendar.monthrange(year, month)
	if month > monthMaxDay:
		return False
	# time
	hour, minute, second = time.split(":")
	if len(hour) != 2:
		return False
	if len(minute) != 2:
		return False
	if len(second) != 2:
		return False
	try:
		hour = int(hour)
		minute = int(minute)
		second = int(second)
	except ValueError:
		return False
	if hour < 0 or hour > 23:
		return False
	if minute < 0 or minute > 59:
		return False
	if second < 0 or second > 59:
		return True
	# fallback
	return True

def fontInfoOpenTypeNameRecordsValidator(value):
	"""
	Version 3+.
	"""
	if not isinstance(value, list):
		return False
	validKeys = set(["nameID", "platformID", "encodingID", "languageID", "string"])
	dictPrototype = dict(nameID=(int, True), platformID=(int, True), encodingID=(int, True), languageID=(int, True), string=(basestring, True))
	seenRecords = []
	for nameRecord in value:
		if not fontInfoDictValidator(nameRecord, dictPrototype):
			return False
		recordKey = (nameRecord["nameID"], nameRecord["platformID"], nameRecord["encodingID"], nameRecord["languageID"])
		if recordKey in seenRecords:
			return False
		seenRecords.append(recordKey)
	return True

def fontInfoOpenTypeOS2WeightClassValidator(value):
	"""
	Version 2+.
	"""
	if not isinstance(value, int):
		return False
	if value < 0:
		return False
	return True

def fontInfoOpenTypeOS2WidthClassValidator(value):
	"""
	Version 2+.
	"""
	if not isinstance(value, int):
		return False
	if value < 1:
		return False
	if value > 9:
		return False
	return True

def fontInfoVersion2OpenTypeOS2PanoseValidator(values):
	"""
	Version 2.
	"""
	if not isinstance(values, (list, tuple)):
		return False
	if len(values) != 10:
		return False
	for value in values:
		if not isinstance(value, int):
			return False
	# XXX further validation?
	return True

def fontInfoVersion3OpenTypeOS2PanoseValidator(values):
	"""
	Version 3+.
	"""
	if not isinstance(values, (list, tuple)):
		return False
	if len(values) != 10:
		return False
	for value in values:
		if not isinstance(value, int):
			return False
		if value < 0:
			return False
	# XXX further validation?
	return True

def fontInfoOpenTypeOS2FamilyClassValidator(values):
	"""
	Version 2+.
	"""
	if not isinstance(values, (list, tuple)):
		return False
	if len(values) != 2:
		return False
	for value in values:
		if not isinstance(value, int):
			return False
	classID, subclassID = values
	if classID < 0 or classID > 14:
		return False
	if subclassID < 0 or subclassID > 15:
		return False
	return True

def fontInfoPostscriptBluesValidator(values):
	"""
	Version 2+.
	"""
	if not isinstance(values, (list, tuple)):
		return False
	if len(values) > 14:
		return False
	if len(values) % 2:
		return False
	for value in values:
		if not isinstance(value, (int, float)):
			return False
	return True

def fontInfoPostscriptOtherBluesValidator(values):
	"""
	Version 2+.
	"""
	if not isinstance(values, (list, tuple)):
		return False
	if len(values) > 10:
		return False
	if len(values) % 2:
		return False
	for value in values:
		if not isinstance(value, (int, float)):
			return False
	return True

def fontInfoPostscriptStemsValidator(values):
	"""
	Version 2+.
	"""
	if not isinstance(values, (list, tuple)):
		return False
	if len(values) > 12:
		return False
	for value in values:
		if not isinstance(value, (int, float)):
			return False
	return True

def fontInfoPostscriptWindowsCharacterSetValidator(value):
	"""
	Version 2+.
	"""
	validValues = range(1, 21)
	if value not in validValues:
		return False
	return True

def fontInfoWOFFMetadataUniqueIDValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(id=(basestring, True))
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	return True

def fontInfoWOFFMetadataVendorValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = {"name" : (basestring, True), "url" : (basestring, False), "dir" : (basestring, False), "class" : (basestring, False)}
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	if "dir" in value and value.get("dir") not in ("ltr", "rtl"):
		return False
	return True

def fontInfoWOFFMetadataCreditsValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(credits=(list, True))
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	if not len(value["credits"]):
		return False
	dictPrototype = {"name" : (basestring, True), "url" : (basestring, False), "role" : (basestring, False), "dir" : (basestring, False), "class" : (basestring, False)}
	for credit in value["credits"]:
		if not fontInfoDictValidator(credit, dictPrototype):
			return False
		if "dir" in credit and credit.get("dir") not in ("ltr", "rtl"):
			return False
	return True

def fontInfoWOFFMetadataDescriptionValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(url=(basestring, False), text=(list, True))
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	for text in value["text"]:
		if not fontInfoWOFFMetadataTextValue(text):
			return False
	return True

def fontInfoWOFFMetadataLicenseValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(url=(basestring, False), text=(list, False), id=(basestring, False))
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	if "text" in value:
		for text in value["text"]:
			if not fontInfoWOFFMetadataTextValue(text):
				return False
	return True

def fontInfoWOFFMetadataTrademarkValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(text=(list, True))
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	for text in value["text"]:
		if not fontInfoWOFFMetadataTextValue(text):
			return False
	return True

def fontInfoWOFFMetadataCopyrightValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(text=(list, True))
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	for text in value["text"]:
		if not fontInfoWOFFMetadataTextValue(text):
			return False
	return True

def fontInfoWOFFMetadataLicenseeValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = {"name" : (basestring, True), "dir" : (basestring, False), "class" : (basestring, False)}
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	if "dir" in value and value.get("dir") not in ("ltr", "rtl"):
		return False
	return True

def fontInfoWOFFMetadataTextValue(value):
	"""
	Version 3+.
	"""
	dictPrototype = {"text" : (basestring, True), "language" : (basestring, False), "dir" : (basestring, False), "class" : (basestring, False)}
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	if "dir" in value and value.get("dir") not in ("ltr", "rtl"):
		return False
	return True

def fontInfoWOFFMetadataExtensionsValidator(value):
	"""
	Version 3+.
	"""
	if not isinstance(value, list):
		return False
	if not value:
		return False
	for extension in value:
		if not fontInfoWOFFMetadataExtensionValidator(extension):
			return False
	return True

def fontInfoWOFFMetadataExtensionValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(names=(list, False), items=(list, True))
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	if "names" in value:
		for name in value["names"]:
			if not fontInfoWOFFMetadataExtensionNameValidator(name):
				return False
	for item in value["items"]:
		if not fontInfoWOFFMetadataExtensionItemValidator(item):
			return False
	return True

def fontInfoWOFFMetadataExtensionItemValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(id=(basestring, False), names=(list, True), values=(list, True))
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	for name in value["names"]:
		if not fontInfoWOFFMetadataExtensionNameValidator(name):
			return False
	for value in value["values"]:
		if not fontInfoWOFFMetadataExtensionValueValidator(name):
			return False
	return True

def fontInfoWOFFMetadataExtensionNameValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = {"text" : (basestring, True), "language" : (basestring, False), "dir" : (basestring, False), "class" : (basestring, False)}
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	return True

def fontInfoWOFFMetadataExtensionValueValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = {"text" : (basestring, True), "language" : (basestring, False), "dir" : (basestring, False), "class" : (basestring, False)}
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	return True

def fontInfoKerningPrefixesValidator(info):
	"""
	Version 3+.
	"""
	prefix1 = info.get("firstKerningGroupPrefix")
	prefix2 = info.get("secondKerningGroupPrefix")
	# both are None
	if prefix1 is None and prefix2 is None:
		return True
	# one is None
	if prefix1 is None and prefix2 is not None:
		return False
	if prefix2 is None and prefix1 is not None:
		return False
	# they are the same
	if prefix1 == prefix2:
		return False
	# one starts with the other
	if prefix1.startswith(prefix2):
		return False
	if prefix2.startswith(prefix1):
		return False
	return True

def fontInfoKerningPrefixValidator(value):
	"""
	Version 3+.
	"""
	if not isinstance(value, basestring):
		return False
	if not len(value):
		return False
	return True

def fontInfoGuidelinesValidator(value):
	"""
	Version 3+.
	"""
	if not isinstance(value, list):
		return True
	identifiers = set()
	for guide in value:
		if not fontInfoGuidelineValidator(guide):
			return False
		identifier = guide.get("identifier")
		if identifier is not None:
			if identifier in identifiers:
				return False
			identifiers.add(identifier)
	return True

def fontInfoGuidelineValidator(value):
	"""
	Version 3+.
	"""
	dictPrototype = dict(
		x=((int, float), False), y=((int, float), False), angle=((int, float), False),
		name=(basestring, False), color=(basestring, False), identifier=(basestring, False)
	)
	if not fontInfoDictValidator(value, dictPrototype):
		return False
	x = value.get("x")
	y = value.get("y")
	angle = value.get("angle")
	# x or y must be present
	if x is None and y is None:
		return False
	# if x or y are None, angle must not be present
	if x is None or y is None:
		if angle is not None:
			return False
	# angle must be between 0 and 360
	if angle is not None:
		if angle < 0:
			return False
		if angle > 360:
			return False
	# identifier must be 1 or more characters
	identifier = value.get("identifier")
	if identifier is not None and not fontInfoIdentifierValidator(identifier):
		return False
	# color must follow the proper format
	color = value.get("color")
	if color is not None and not fontInfoColorValidator(color):
		return False
	return True

def fontInfoIdentifierValidator(value):
	"""
	Version 3+.
	"""
	validCharactersMin = 0x20
	validCharactersMax = 0x7E
	if not isinstance(value, basestring):
		return False
	if not value:
		return False
	for c in value:
		c = ord(c)
		if c < validCharactersMin or c > validCharactersMax:
			return False
	return True

def fontInfoColorValidator(value):
	"""
	Version 3+.
	"""
	if not isinstance(value, basestring):
		return False
	parts = value.split(",")
	if len(parts) != 4:
		return False
	for part in parts:
		part = part.strip()
		converted = False
		try:
			part = int(part)
			converted = True
		except ValueError:
			pass
		if not converted:
			try:
				part = float(part)
				converted = True
			except ValueError:
				pass
		if not converted:
			return False
		if part < 0:
			return False
		if part > 1:
			return False
	return True

# ---------------------------
# layercontents.plist Support
# ---------------------------

def layerContentsValidator(value, ufoPath):
	"""
	Check the validity of layercontents.plist.
	Version 3+.
	"""
	from ufoLib import DEFAULT_GLYPHS_DIRNAME
	bogusFileMessage = "layercontents.plist in not in the correct format."
	# file isn't in the right format
	if not isinstance(value, list):
		return False, bogusFileMessage
	# work through each entry
	usedLayerNames = set()
	usedDirectories = set()
	contents = {}
	for entry in value:
		# layer entry in the incorrect format
		if not isinstance(entry, list):
			return False, bogusFileMessage
		if not len(entry) == 2:
			return False, bogusFileMessage
		for i in entry:
			if not isinstance(i, basestring):
				return False, bogusFileMessage
		layerName, directoryName = entry
		if not directoryName.startswith("glyphs"):
			return False, bogusFileMessage
		# directory doesn't exist
		p = os.path.join(ufoPath, directoryName)
		if not os.path.exists(p):
			return False, "A glyphset does not exist at %s." % directoryName
		# check usage
		if layerName in usedLayerNames:
			return False, "The layer name %s is used by more than one layer." % layerName
		usedLayerNames.add(layerName)
		if directoryName in usedDirectories:
			return False, "The directory %s is used by more than one layer." % directoryName
		usedDirectories.add(directoryName)
		# store
		contents[layerName] = directoryName
	# missing default layer
	foundDefault = True
	for layerName, directory in contents.items():
		if directory == DEFAULT_GLYPHS_DIRNAME:
			foundDefault = True
			break
	if not foundDefault:
		return False, "The required default glyph set is not in the UFO."
	return True, None


