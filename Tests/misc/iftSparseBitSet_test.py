import unittest
from fontTools.misc.iftSparseBitSet import encode, decode, SparseBitSetDecodeError


class IftSparseBitSetTest(unittest.TestCase):
    def test_roundtrip_empty_success(self):
        values = set()
        encoded = encode(values)
        decoded, consumed = decode(encoded)
        self.assertEqual(decoded, values)
        self.assertEqual(consumed, len(encoded))

    def test_roundtrip_singleValue_success(self):
        values = {42}
        encoded = encode(values)
        decoded, consumed = decode(encoded)
        self.assertEqual(decoded, values)
        self.assertEqual(consumed, len(encoded))

    def test_roundtrip_multipleValues_success(self):
        values = {1, 10, 100, 1000}
        encoded = encode(values)
        decoded, consumed = decode(encoded)
        self.assertEqual(decoded, values)
        self.assertEqual(consumed, len(encoded))

    def test_roundtrip_largeRange_success(self):
        # Test zero-node optimization (filling subtrees).
        # A range of 1000 values should be very compact.
        values = set(range(100, 1100))
        encoded = encode(values)
        decoded, consumed = decode(encoded)
        self.assertEqual(decoded, values)
        self.assertEqual(consumed, len(encoded))
        # 1000 values would take ~125 bytes if 1 bit per value.
        # With zero-node optimization, it should be much smaller.
        self.assertLess(len(encoded), 50)

    def test_roundtrip_sparseValues_success(self):
        values = {1, 1000000}
        encoded = encode(values)
        decoded, consumed = decode(encoded)
        self.assertEqual(decoded, values)
        self.assertEqual(consumed, len(encoded))

    def test_decode_positiveBias_shiftsValues(self):
        # b"\x04\x01" is {0} with BF=2, height=1.
        decoded, consumed = decode(b"\x04\x01", bias=100)
        self.assertEqual(decoded, {100})
        self.assertEqual(consumed, 2)

    def test_decode_negativeBias_clipsToZero(self):
        # b"\x04\x01" is {0}. With bias -1, it becomes -1 and should be ignored.
        decoded, consumed = decode(b"\x04\x01", bias=-1)
        self.assertEqual(decoded, set())
        self.assertEqual(consumed, 2)

    def test_decode_headerOnlyHeight0_success(self):
        # Height 0 always means empty set.
        self.assertEqual(decode(b"\x00"), (set(), 1))

    def test_decode_emptyData_raisesError(self):
        with self.assertRaisesRegex(SparseBitSetDecodeError, "Empty data"):
            decode(b"")

    def test_decode_truncatedData_raisesError(self):
        # Encoded {0} is b"\x04\x01". Truncate to b"\x04".
        with self.assertRaisesRegex(SparseBitSetDecodeError, "Unexpected end of data"):
            decode(b"\x04")

    def test_decode_invalidHeight_raisesError(self):
        # BF=32 (id 3), Max Height=7. Try height 8.
        header = (8 << 2) | 3
        with self.assertRaisesRegex(SparseBitSetDecodeError, "exceeds max 7"):
            decode(bytes([header]))

    def test_encode_valueOutOfRange_raisesError(self):
        # BF=32, Max Height=7, Max Capacity=32^7 = 2^35.
        # Value 2^35 requires height 8, which is not supported.
        with self.assertRaisesRegex(ValueError, "Cannot encode max value"):
            encode([2**35])

    def test_decode_maxValue_truncates_output(self):
        values = {1, 2, 10, 20}
        encoded = encode(values)
        decoded, consumed = decode(encoded, maxValue=15)
        self.assertEqual(decoded, {1, 2, 10})
        self.assertEqual(consumed, len(encoded))

    def test_decode_maxValue_with_zero_node(self):
        # A dense range from 0 to 99 will use the zero-node optimization.
        values = set(range(100))
        encoded = encode(values)
        # maxValue should truncate this dense range.
        decoded, consumed = decode(encoded, maxValue=49)
        self.assertEqual(decoded, set(range(50)))
        self.assertEqual(consumed, len(encoded))

    def test_decode_maxValue_leaves_empty_set(self):
        values = {100, 200, 300}
        encoded = encode(values)
        decoded, consumed = decode(encoded, maxValue=50)
        self.assertEqual(decoded, set())
        self.assertEqual(consumed, len(encoded))

    def test_roundtrip_almost_full_range(self):
        # A range of 64 with one value missing should NOT use zero-node optimization
        values = set(range(64))
        values.remove(32)
        encoded = encode(values)
        decoded, consumed = decode(encoded)
        self.assertEqual(decoded, values)
        self.assertEqual(consumed, len(encoded))

    def test_roundtrip_full_child_sparse_parent(self):
        # This set fills one child node completely (e.g., 8-15 for bf=8),
        # but the parent node is sparse.
        values = set(range(8, 16))
        encoded = encode(values)
        decoded, consumed = decode(encoded)
        self.assertEqual(decoded, values)
        self.assertEqual(consumed, len(encoded))


if __name__ == "__main__":
    unittest.main()
