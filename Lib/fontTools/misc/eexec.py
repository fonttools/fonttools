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
	plainList = []
	for cipher in cipherstring:
		plain, R = _decryptChar(cipher, R)
		plainList.append(plain)
	plainstring = strjoin(plainList)
	return plainstring, int(R)

def encrypt(plainstring, R):
	cipherList = []
	for plain in plainstring:
		cipher, R = _encryptChar(plain, R)
		cipherList.append(cipher)
	cipherstring = strjoin(cipherList)
	return cipherstring, int(R)


def hexString(s):
	import binascii
	return binascii.hexlify(s)

def deHexString(h):
	import binascii
	h = strjoin(h.split())
	return binascii.unhexlify(h)


def _test():
	testStr = "\0\0asdadads asds\265"
	print(decrypt, decrypt(testStr, 12321))
	print(encrypt, encrypt(testStr, 12321))


if __name__ == "__main__":
	_test()
