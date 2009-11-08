"""fontTools.misc.eexec.py -- Module implementing the eexec and 
charstring encryption algorithm as used by PostScript Type 1 fonts.
"""

# Warning: Although a Python implementation is provided here, 
# all four public functions get overridden by the *much* faster 
# C extension module eexecOp, if available.

import string

error = "eexec.error"


def _decryptChar(cipher, R):
	cipher = ord(cipher)
	plain = ( (cipher ^ (R>>8)) ) & 0xFF
	R = ( (cipher + R) * 52845L + 22719L ) & 0xFFFF
	return chr(plain), R

def _encryptChar(plain, R):
	plain = ord(plain)
	cipher = ( (plain ^ (R>>8)) ) & 0xFF
	R = ( (cipher + R) * 52845L + 22719L ) & 0xFFFF
	return chr(cipher), R


def decrypt(cipherstring, R):
	# I could probably speed this up by inlining _decryptChar,
	# but... we've got eexecOp, so who cares ;-)
	plainList = []
	for cipher in cipherstring:
		plain, R = _decryptChar(cipher, R)
		plainList.append(plain)
	plainstring = string.join(plainList, '')
	return plainstring, int(R)

def encrypt(plainstring, R):
	cipherList = []
	for plain in plainstring:
		cipher, R = _encryptChar(plain, R)
		cipherList.append(cipher)
	cipherstring = string.join(cipherList, '')
	return cipherstring, int(R)


def hexString(s):
	import binascii
	return binascii.hexlify(s)

def deHexString(h):
	import binascii
	h = "".join(h.split())
	return binascii.unhexlify(h)


def _test():
	import fontTools.misc.eexecOp as eexecOp
	testStr = "\0\0asdadads asds\265"
	print decrypt, decrypt(testStr, 12321)
	print eexecOp.decrypt, eexecOp.decrypt(testStr, 12321)
	print encrypt, encrypt(testStr, 12321)
	print eexecOp.encrypt, eexecOp.encrypt(testStr, 12321)


if __name__ == "__main__":
	_test()


try:
	from fontTools.misc.eexecOp import *
except ImportError:
	pass # Use the slow Python versions

