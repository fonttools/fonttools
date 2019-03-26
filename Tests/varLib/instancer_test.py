from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.varLib.mvar import MVAR_ENTRIES
import os
import pytest


TESTDATA = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def varfont():
    f = TTFont()
    f.importXML(os.path.join(TESTDATA, "PartialInstancerTest-VF.ttx"))
    return f


def _get_coordinates(varfont, glyphname):
    # converts GlyphCoordinates to a list of (x, y) tuples, so that pytest's
    # assert will give us a nicer diff
    return list(varfont["glyf"].getCoordinates(glyphname, varfont))


class InstantiateGvarTest(object):
    @pytest.mark.parametrize("glyph_name", ["hyphen"])
    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param(
                {"wdth": -1.0},
                {
                    "hyphen": [
                        (27, 229),
                        (27, 310),
                        (247, 310),
                        (247, 229),
                        (0, 0),
                        (274, 0),
                        (0, 1000),
                        (0, 0),
                    ]
                },
                id="wdth=-1.0",
            ),
            pytest.param(
                {"wdth": -0.5},
                {
                    "hyphen": [
                        (33.5, 229),
                        (33.5, 308.5),
                        (264.5, 308.5),
                        (264.5, 229),
                        (0, 0),
                        (298, 0),
                        (0, 1000),
                        (0, 0),
                    ]
                },
                id="wdth=-0.5",
            ),
            # an axis pinned at the default normalized location (0.0) means
            # the default glyf outline stays the same
            pytest.param(
                {"wdth": 0.0},
                {
                    "hyphen": [
                        (40, 229),
                        (40, 307),
                        (282, 307),
                        (282, 229),
                        (0, 0),
                        (322, 0),
                        (0, 1000),
                        (0, 0),
                    ]
                },
                id="wdth=0.0",
            ),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, glyph_name, location, expected):
        instancer.instantiateGvar(varfont, location)

        assert _get_coordinates(varfont, glyph_name) == expected[glyph_name]

        # check that the pinned axis has been dropped from gvar
        assert not any(
            "wdth" in t.axes
            for tuples in varfont["gvar"].variations.values()
            for t in tuples
        )


class InstantiateCvarTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param({"wght": -1.0}, [500, -400, 150, 250], id="wght=-1.0"),
            pytest.param({"wdth": -1.0}, [500, -400, 180, 200], id="wdth=-1.0"),
            pytest.param({"wght": -0.5}, [500, -400, 165, 250], id="wght=-0.5"),
            pytest.param({"wdth": -0.3}, [500, -400, 180, 235], id="wdth=-0.3"),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, location, expected):
        instancer.instantiateCvar(varfont, location)

        assert list(varfont["cvt "].values) == expected

        # check that the pinned axis has been dropped from gvar
        pinned_axes = location.keys()
        assert not any(
            axis in t.axes for t in varfont["cvar"].variations for axis in pinned_axes
        )

    def test_full_instance(self, varfont):
        instancer.instantiateCvar(varfont, {"wght": -0.5, "wdth": -0.5})

        assert list(varfont["cvt "].values) == [500, -400, 165, 225]

        assert "cvar" not in varfont


class InstantiateMvarTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param(
                {"wght": 1.0}, {"strs": 100, "undo": -200, "unds": 150}, id="wght=1.0"
            ),
            pytest.param(
                {"wght": 0.5}, {"strs": 75, "undo": -150, "unds": 100}, id="wght=0.5"
            ),
            pytest.param(
                {"wght": 0.0}, {"strs": 50, "undo": -100, "unds": 50}, id="wght=0.0"
            ),
            pytest.param(
                {"wdth": -1.0}, {"strs": 20, "undo": -100, "unds": 50}, id="wdth=-1.0"
            ),
            pytest.param(
                {"wdth": -0.5}, {"strs": 35, "undo": -100, "unds": 50}, id="wdth=-0.5"
            ),
            pytest.param(
                {"wdth": 0.0}, {"strs": 50, "undo": -100, "unds": 50}, id="wdth=0.0"
            ),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, location, expected):
        mvar = varfont["MVAR"].table
        # initially we have a single VarData with deltas associated with 3 regions:
        # 1 with only wght, 1 with only wdth, and 1 with both wght and wdth.
        assert len(mvar.VarStore.VarData) == 1
        assert mvar.VarStore.VarRegionList.RegionCount == 3
        assert mvar.VarStore.VarData[0].VarRegionCount == 3
        assert all(len(item) == 3 for item in mvar.VarStore.VarData[0].Item)

        instancer.instantiateMvar(varfont, location)

        for mvar_tag, expected_value in expected.items():
            table_tag, item_name = MVAR_ENTRIES[mvar_tag]
            assert getattr(varfont[table_tag], item_name) == expected_value

        # check that the pinned axis does not influence any of the remaining regions
        # in MVAR VarStore
        pinned_axes = location.keys()
        fvar = varfont["fvar"]
        assert all(
            peak == 0
            for region in mvar.VarStore.VarRegionList.Region
            for axis, (start, peak, end) in region.get_support(fvar.axes).items()
            if axis in pinned_axes
        )

        # check that regions and accompanying deltas have been dropped
        num_regions_left = len(mvar.VarStore.VarRegionList.Region)
        assert num_regions_left < 3
        assert mvar.VarStore.VarRegionList.RegionCount == num_regions_left
        assert mvar.VarStore.VarData[0].VarRegionCount == num_regions_left

    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param(
                {"wght": 1.0, "wdth": 0.0},
                {"strs": 100, "undo": -200, "unds": 150},
                id="wght=1.0,wdth=0.0",
            ),
            pytest.param(
                {"wght": 0.0, "wdth": -1.0},
                {"strs": 20, "undo": -100, "unds": 50},
                id="wght=0.0,wdth=-1.0",
            ),
            pytest.param(
                {"wght": 0.5, "wdth": -0.5},
                {"strs": 55, "undo": -145, "unds": 95},
                id="wght=0.5,wdth=-0.5",
            ),
            pytest.param(
                {"wght": 1.0, "wdth": -1.0},
                {"strs": 50, "undo": -180, "unds": 130},
                id="wght=0.5,wdth=-0.5",
            ),
        ],
    )
    def test_full_instance(self, varfont, location, expected):
        instancer.instantiateMvar(varfont, location)

        for mvar_tag, expected_value in expected.items():
            table_tag, item_name = MVAR_ENTRIES[mvar_tag]
            assert getattr(varfont[table_tag], item_name) == expected_value

        assert "MVAR" not in varfont
