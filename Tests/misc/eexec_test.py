from fontTools.misc.py23 import *
from fontTools.misc.eexec import decrypt, encrypt


def test_decrypt():
    testStr = b"\0\0asdadads asds\265"
    decryptedStr, R = decrypt(testStr, 12321)
    assert decryptedStr == b'0d\nh\x15\xe8\xc4\xb2\x15\x1d\x108\x1a<6\xa1'
    assert R == 36142


def test_encrypt():
    testStr = b'0d\nh\x15\xe8\xc4\xb2\x15\x1d\x108\x1a<6\xa1'
    encryptedStr, R = encrypt(testStr, 12321)
    assert encryptedStr == b"\0\0asdadads asds\265"
    assert R == 36142
