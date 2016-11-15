"""fontTools.misc.eexec.py -- Module implementing the eexec and
charstring encryption algorithm as used by PostScript Type 1 fonts.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

def _decryptChar(cipher, R):
	cipher = byteord(cipher)
	plain = ( (cipher ^ (R>>8)) ) & 0xFF
	R = ( (cipher + R) * 52845 + 22719 ) & 0xFFFF
	return bytechr(plain), R

def _encryptChar(plain, R):
	plain = byteord(plain)
	cipher = ( (plain ^ (R>>8)) ) & 0xFF
	R = ( (cipher + R) * 52845 + 22719 ) & 0xFFFF
	return bytechr(cipher), R


def decrypt(cipherstring, R):
	r"""
	>>> testStr = b"\0\0asdadads asds\265"
	>>> decryptedStr, R = decrypt(testStr, 12321)
	>>> decryptedStr == b'0d\nh\x15\xe8\xc4\xb2\x15\x1d\x108\x1a<6\xa1'
	True
	>>> R == 36142
	True
	"""
	plainList = []
	for cipher in cipherstring:
		plain, R = _decryptChar(cipher, R)
		plainList.append(plain)
	plainstring = bytesjoin(plainList)
	return plainstring, int(R)

def encrypt(plainstring, R):
	r"""
	>>> testStr = b'0d\nh\x15\xe8\xc4\xb2\x15\x1d\x108\x1a<6\xa1'
	>>> encryptedStr, R = encrypt(testStr, 12321)
	>>> encryptedStr == b"\0\0asdadads asds\265"
	True
	>>> R == 36142
	True
	"""
	cipherList = []
	for plain in plainstring:
		cipher, R = _encryptChar(plain, R)
		cipherList.append(cipher)
	cipherstring = bytesjoin(cipherList)
	return cipherstring, int(R)


def hexString(s):
	import binascii
	return binascii.hexlify(s)

def deHexString(h):
	import binascii
	h = bytesjoin(h.split())
	return binascii.unhexlify(h)


if __name__ == "__main__":
	import sys
	import doctest
	sys.exit(doctest.testmod().failed)
