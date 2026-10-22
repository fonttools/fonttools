from fontTools.cffLib import PrivateDict


def _blend_private_dict(num_regions):
    from fontTools.cffLib import VarStoreData
    from fontTools.varLib.builder import buildVarData, buildVarRegionList, buildVarStore

    store = buildVarStore(
        buildVarRegionList([{"wght": (0, 1, 1)}] * num_regions, ["wght"]),
        [buildVarData(list(range(num_regions)), [], optimize=False)],
    )
    return PrivateDict(vstore=VarStoreData(otVarStore=store))


def test_private_dict_multiple_blend_groups():
    from fontTools.cffLib import encodeNumber

    private = _blend_private_dict(1)
    # Two delta-encoded values: 10, then 5 relative to the first. The empty
    # blend between them must leave the first result on the operand stack.
    data = b"".join(encodeNumber(n) for n in [10, 1, 1]) + bytes([23])
    data += encodeNumber(0) + bytes([23])
    data += b"".join(encodeNumber(n) for n in [5, 2, 1]) + bytes([23, 6])
    private.decompile(data)
    assert private.BlueValues == [[10, 1], [15, 2]]


def test_private_dict_split_blends_roundtrip():
    from fontTools.cffLib import PrivateDictDecompiler

    class StackCheckingDecompiler(PrivateDictDecompiler):
        def arg_blendList(self, name):
            assert len(self.stack) <= 513
            return super().arg_blendList(name)

    # At 250 regions the final groups must shrink to account for the results
    # of preceding groups still occupying the stack.
    for regions in [40, 250]:
        private = _blend_private_dict(regions)
        expected = [[-40 + 2 * i] + [i + 1] * regions for i in range(14)]
        private.BlueValues = expected
        data = private.getCompiler(None, None, isCFF2=True).compile("test")
        result = _blend_private_dict(regions)
        decoder = StackCheckingDecompiler(None, result)
        decoder.decompile(data)
        result.rawDict = decoder.getDict()
        assert result.BlueValues == expected


def test_private_dict_blend_preserves_constant_prefix():
    from fontTools.cffLib import encodeNumber

    private = _blend_private_dict(1)
    data = b"".join(encodeNumber(n) for n in [10, 5, 2, 1]) + bytes([23, 6])
    private.decompile(data)
    assert private.BlueValues == [[10, 0], [15, 2]]


def test_private_dict_blend_preserves_constant_suffix():
    from fontTools.cffLib import encodeNumber

    prefix = b"".join(encodeNumber(n) for n in [10, 1, 1]) + bytes([23])
    for zero_blend in [False, True]:
        private = _blend_private_dict(1)
        data = prefix + encodeNumber(5)
        if zero_blend:
            data += encodeNumber(0) + bytes([23])
        data += bytes([6])
        private.decompile(data)
        assert private.BlueValues == [[10, 1], [15, 0]]


def test_private_dict_unencodable_blend_rejected():
    import pytest

    private = _blend_private_dict(512)
    private.BlueValues = [[-20] + [0] * 512, [-10] + [0] * 512]
    with pytest.raises(ValueError, match="operand stack"):
        private.getCompiler(None, None, isCFF2=True).compile("test")
