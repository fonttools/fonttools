from fontTools.ttLib.tables.V_O_R_G_ import table_V_O_R_G_


class FakeFont:
    glyphNames = {10: "glyph10", 0x10000: "highGlyph"}
    glyphIDs = {name: gid for gid, name in glyphNames.items()}

    def getGlyphName(self, glyphID):
        return self.glyphNames[glyphID]

    def getGlyphOrder(self):
        return self

    def __getitem__(self, glyphID):
        return self.glyphNames[glyphID]

    def getReverseGlyphMap(self, rebuild=False):
        return self.glyphIDs


def test_version_2_round_trip():
    vorg = table_V_O_R_G_()
    vorg.majorVersion = 2
    vorg.minorVersion = 0
    vorg.defaultVertOriginY = 880
    vorg.VOriginRecords = {"highGlyph": 861, "glyph10": 889}

    data = vorg.compile(FakeFont())

    assert data == bytes.fromhex("0002 0000 0370 000002 00000A 0379 010000 035D")

    recompiled = table_V_O_R_G_()
    recompiled.decompile(data, FakeFont())
    assert recompiled.majorVersion == 2
    assert recompiled.minorVersion == 0
    assert recompiled.defaultVertOriginY == 880
    assert recompiled.VOriginRecords == {"glyph10": 889, "highGlyph": 861}
