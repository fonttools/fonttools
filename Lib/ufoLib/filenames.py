"""
User name to file name conversion.
This was taken form the UFO 3 spec.
"""

illegalCharacters = "\" * + / : < > ? [ \ ] | \0".split(" ")
illegalCharacters += [chr(i) for i in range(1, 32)]
illegalCharacters += [chr(0x7F)]
reservedFileNames = "CON PRN AUX CLOCK$ NUL A:-Z: COM1".lower().split(" ")
reservedFileNames += "LPT1 LPT2 LPT3 COM2 COM3 COM4".lower().split(" ")
maxFileNameLength = 255


class NameTranslationError(Exception):
	pass


def userNameToFileName(userName, existing=[], prefix="", suffix=""):
	"""
	existing should be a case-insensitive list
	of all existing file names.

	>>> userNameToFileName(u"a")
	u'a'
	>>> userNameToFileName(u"A")
	u'A_'
	>>> userNameToFileName(u"AE")
	u'A_E_'
	>>> userNameToFileName(u"Ae")
	u'A_e'
	>>> userNameToFileName(u"ae")
	u'ae'
	>>> userNameToFileName(u"aE")
	u'aE_'
	>>> userNameToFileName(u"a.alt")
	u'a.alt'
	>>> userNameToFileName(u"A.alt")
	u'A_.alt'
	>>> userNameToFileName(u"A.Alt")
	u'A_.A_lt'
	>>> userNameToFileName(u"A.aLt")
	u'A_.aL_t'
	>>> userNameToFileName(u"A.alT")
	u'A_.alT_'
	>>> userNameToFileName(u"T_H")
	u'T__H_'
	>>> userNameToFileName(u"T_h")
	u'T__h'
	>>> userNameToFileName(u"t_h")
	u't_h'
	>>> userNameToFileName(u"F_F_I")
	u'F__F__I_'
	>>> userNameToFileName(u"f_f_i")
	u'f_f_i'
	>>> userNameToFileName(u"Aacute_V.swash")
	u'A_acute_V_.swash'
	>>> userNameToFileName(u".notdef")
	u'_notdef'
	>>> userNameToFileName(u"con")
	u'_con'
	>>> userNameToFileName(u"CON")
	u'C_O_N_'
	>>> userNameToFileName(u"con.alt")
	u'_con.alt'
	>>> userNameToFileName(u"alt.con")
	u'alt._con'
	"""
	# the incoming name must be a unicode string
	assert isinstance(userName, str), "The value for userName must be a unicode string."
	# establish the prefix and suffix lengths
	prefixLength = len(prefix)
	suffixLength = len(suffix)
	# replace an initial period with an _
	# if no prefix is to be added
	if not prefix and userName[0] == ".":
		userName = "_" + userName[1:]
	# filter the user name
	filteredUserName = []
	for character in userName:
		# replace illegal characters with _
		if character in illegalCharacters:
			character = "_"
		# add _ to all non-lower characters
		elif character != character.lower():
			character += "_"
		filteredUserName.append(character)
	userName = "".join(filteredUserName)
	# clip to 255
	sliceLength = maxFileNameLength - prefixLength - suffixLength
	userName = userName[:sliceLength]
	# test for illegal files names
	parts = []
	for part in userName.split("."):
		if part.lower() in reservedFileNames:
			part = "_" + part
		parts.append(part)
	userName = ".".join(parts)
	# test for clash
	fullName = prefix + userName + suffix
	if fullName.lower() in existing:
		fullName = handleClash1(userName, existing, prefix, suffix)
	# finished
	return fullName

def handleClash1(userName, existing=[], prefix="", suffix=""):
	"""
	existing should be a case-insensitive list
	of all existing file names.

	>>> prefix = ("0" * 5) + "."
	>>> suffix = "." + ("0" * 10)
	>>> existing = ["a" * 5]

	>>> e = list(existing)
	>>> handleClash1(userName="A" * 5, existing=e,
	...		prefix=prefix, suffix=suffix)
	'00000.AAAAA000000000000001.0000000000'

	>>> e = list(existing)
	>>> e.append(prefix + "aaaaa" + "1".zfill(15) + suffix)
	>>> handleClash1(userName="A" * 5, existing=e,
	...		prefix=prefix, suffix=suffix)
	'00000.AAAAA000000000000002.0000000000'

	>>> e = list(existing)
	>>> e.append(prefix + "AAAAA" + "2".zfill(15) + suffix)
	>>> handleClash1(userName="A" * 5, existing=e,
	...		prefix=prefix, suffix=suffix)
	'00000.AAAAA000000000000001.0000000000'
	"""
	# if the prefix length + user name length + suffix length + 15 is at
	# or past the maximum length, silce 15 characters off of the user name
	prefixLength = len(prefix)
	suffixLength = len(suffix)
	if prefixLength + len(userName) + suffixLength + 15 > maxFileNameLength:
		l = (prefixLength + len(userName) + suffixLength + 15)
		sliceLength = maxFileNameLength - l
		userName = userName[:sliceLength]
	finalName = None
	# try to add numbers to create a unique name
	counter = 1
	while finalName is None:
		name = userName + str(counter).zfill(15)
		fullName = prefix + name + suffix
		if fullName.lower() not in existing:
			finalName = fullName
			break
		else:
			counter += 1
		if counter >= 999999999999999:
			break
	# if there is a clash, go to the next fallback
	if finalName is None:
		finalName = handleClash2(existing, prefix, suffix)
	# finished
	return finalName

def handleClash2(existing=[], prefix="", suffix=""):
	"""
	existing should be a case-insensitive list
	of all existing file names.

	>>> prefix = ("0" * 5) + "."
	>>> suffix = "." + ("0" * 10)
	>>> existing = [prefix + str(i) + suffix for i in range(100)]

	>>> e = list(existing)
	>>> handleClash2(existing=e, prefix=prefix, suffix=suffix)
	'00000.100.0000000000'

	>>> e = list(existing)
	>>> e.remove(prefix + "1" + suffix)
	>>> handleClash2(existing=e, prefix=prefix, suffix=suffix)
	'00000.1.0000000000'

	>>> e = list(existing)
	>>> e.remove(prefix + "2" + suffix)
	>>> handleClash2(existing=e, prefix=prefix, suffix=suffix)
	'00000.2.0000000000'
	"""
	# calculate the longest possible string
	maxLength = maxFileNameLength - len(prefix) - len(suffix)
	maxValue = int("9" * maxLength)
	# try to find a number
	finalName = None
	counter = 1
	while finalName is None:
		fullName = prefix + str(counter) + suffix
		if fullName.lower() not in existing:
			finalName = fullName
			break
		else:
			counter += 1
		if counter >= maxValue:
			break
	# raise an error if nothing has been found
	if finalName is None:
		raise NameTranslationError("No unique name could be found.")
	# finished
	return finalName

if __name__ == "__main__":
	import doctest
	doctest.testmod()
