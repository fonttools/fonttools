from fontTools.misc.fixedTools import floatToFixedToFloat
from fontTools.misc.roundTools import noRound
from fontTools.misc.testTools import stripVariableItemsFromTTX
from fontTools.misc.textTools import Tag
from fontTools import ttLib
from fontTools import designspaceLib
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib.tables import _f_v_a_r, _g_l_y_f
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools import varLib
from fontTools.varLib import instancer
from fontTools.varLib.mvar import MVAR_ENTRIES
from fontTools.varLib import builder
from fontTools.varLib import featureVars
from fontTools.varLib import models
import collections
from copy import deepcopy
from io import BytesIO, StringIO
import logging
import os
import re
from types import SimpleNamespace
import pytest


# see Tests/varLib/instancer/conftest.py for "varfont" fixture definition

TESTDATA = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture(params=[True, False], ids=["optimize", "no-optimize"])
def optimize(request):
    return request.param


@pytest.fixture
def fvarAxes():
    wght = _f_v_a_r.Axis()
    wght.axisTag = Tag("wght")
    wght.minValue = 100
    wght.defaultValue = 400
    wght.maxValue = 900
    wdth = _f_v_a_r.Axis()
    wdth.axisTag = Tag("wdth")
    wdth.minValue = 70
    wdth.defaultValue = 100
    wdth.maxValue = 100
    return [wght, wdth]


def _get_coordinates(varfont, glyphname):
    # converts GlyphCoordinates to a list of (x, y) tuples, so that pytest's
    # assert will give us a nicer diff
    return list(
        varfont["glyf"]._getCoordinatesAndControls(
            glyphname,
            varfont["hmtx"].metrics,
            varfont["vmtx"].metrics,
            # the tests expect float coordinates
            round=noRound,
        )[0]
    )


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
                        (0, 536),
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
                        (0, 536),
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
                        (0, 536),
                        (0, 0),
                    ]
                },
                id="wdth=0.0",
            ),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, glyph_name, location, expected, optimize):
        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateGvar(varfont, location, optimize=optimize)

        assert _get_coordinates(varfont, glyph_name) == expected[glyph_name]

        # check that the pinned axis has been dropped from gvar
        assert not any(
            "wdth" in t.axes
            for tuples in varfont["gvar"].variations.values()
            for t in tuples
        )

    def test_full_instance(self, varfont, optimize):
        location = instancer.NormalizedAxisLimits(wght=0.0, wdth=-0.5)

        instancer.instantiateGvar(varfont, location, optimize=optimize)

        assert _get_coordinates(varfont, "hyphen") == [
            (33.5, 229),
            (33.5, 308.5),
            (264.5, 308.5),
            (264.5, 229),
            (0, 0),
            (298, 0),
            (0, 536),
            (0, 0),
        ]

        assert "gvar" not in varfont

    def test_composite_glyph_not_in_gvar(self, varfont):
        """The 'minus' glyph is a composite glyph, which references 'hyphen' as a
        component, but has no tuple variations in gvar table, so the component offset
        and the phantom points do not change; however the sidebearings and bounding box
        do change as a result of the parent glyph 'hyphen' changing.
        """
        hmtx = varfont["hmtx"]
        vmtx = varfont["vmtx"]

        hyphenCoords = _get_coordinates(varfont, "hyphen")
        assert hyphenCoords == [
            (40, 229),
            (40, 307),
            (282, 307),
            (282, 229),
            (0, 0),
            (322, 0),
            (0, 536),
            (0, 0),
        ]
        assert hmtx["hyphen"] == (322, 40)
        assert vmtx["hyphen"] == (536, 229)

        minusCoords = _get_coordinates(varfont, "minus")
        assert minusCoords == [(0, 0), (0, 0), (422, 0), (0, 536), (0, 0)]
        assert hmtx["minus"] == (422, 40)
        assert vmtx["minus"] == (536, 229)

        location = instancer.NormalizedAxisLimits(wght=-1.0, wdth=-1.0)

        instancer.instantiateGvar(varfont, location)

        # check 'hyphen' coordinates changed
        assert _get_coordinates(varfont, "hyphen") == [
            (26, 259),
            (26, 286),
            (237, 286),
            (237, 259),
            (0, 0),
            (263, 0),
            (0, 536),
            (0, 0),
        ]
        # check 'minus' coordinates (i.e. component offset and phantom points)
        # did _not_ change
        assert _get_coordinates(varfont, "minus") == minusCoords

        assert hmtx["hyphen"] == (263, 26)
        assert vmtx["hyphen"] == (536, 250)

        assert hmtx["minus"] == (422, 26)  # 'minus' left sidebearing changed
        assert vmtx["minus"] == (536, 250)  # 'minus' top sidebearing too


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
        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateCvar(varfont, location)

        assert list(varfont["cvt "].values) == expected

        # check that the pinned axis has been dropped from cvar
        pinned_axes = location.keys()
        assert not any(
            axis in t.axes for t in varfont["cvar"].variations for axis in pinned_axes
        )

    def test_full_instance(self, varfont):
        location = instancer.NormalizedAxisLimits(wght=-0.5, wdth=-0.5)

        instancer.instantiateCvar(varfont, location)

        assert list(varfont["cvt "].values) == [500, -400, 165, 225]

        assert "cvar" not in varfont


class InstantiateMVARTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param(
                {"wght": 1.0},
                {"strs": 100, "undo": -200, "unds": 150, "xhgt": 530},
                id="wght=1.0",
            ),
            pytest.param(
                {"wght": 0.5},
                {"strs": 75, "undo": -150, "unds": 100, "xhgt": 515},
                id="wght=0.5",
            ),
            pytest.param(
                {"wght": 0.0},
                {"strs": 50, "undo": -100, "unds": 50, "xhgt": 500},
                id="wght=0.0",
            ),
            pytest.param(
                {"wdth": -1.0},
                {"strs": 20, "undo": -100, "unds": 50, "xhgt": 500},
                id="wdth=-1.0",
            ),
            pytest.param(
                {"wdth": -0.5},
                {"strs": 35, "undo": -100, "unds": 50, "xhgt": 500},
                id="wdth=-0.5",
            ),
            pytest.param(
                {"wdth": 0.0},
                {"strs": 50, "undo": -100, "unds": 50, "xhgt": 500},
                id="wdth=0.0",
            ),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, location, expected):
        mvar = varfont["MVAR"].table
        # initially we have two VarData: the first contains deltas associated with 3
        # regions: 1 with only wght, 1 with only wdth, and 1 with both wght and wdth
        assert len(mvar.VarStore.VarData) == 2
        assert mvar.VarStore.VarRegionList.RegionCount == 3
        assert mvar.VarStore.VarData[0].VarRegionCount == 3
        assert all(len(item) == 3 for item in mvar.VarStore.VarData[0].Item)
        # The second VarData has deltas associated only with 1 region (wght only).
        assert mvar.VarStore.VarData[1].VarRegionCount == 1
        assert all(len(item) == 1 for item in mvar.VarStore.VarData[1].Item)

        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateMVAR(varfont, location)

        for mvar_tag, expected_value in expected.items():
            table_tag, item_name = MVAR_ENTRIES[mvar_tag]
            assert getattr(varfont[table_tag], item_name) == expected_value

        # check that regions and accompanying deltas have been dropped
        num_regions_left = len(mvar.VarStore.VarRegionList.Region)
        assert num_regions_left < 3
        assert mvar.VarStore.VarRegionList.RegionCount == num_regions_left
        assert mvar.VarStore.VarData[0].VarRegionCount == num_regions_left
        # VarData subtables have been merged
        assert len(mvar.VarStore.VarData) == 1

    @pytest.mark.parametrize(
        "location, expected, sync_vmetrics",
        [
            pytest.param(
                {"wght": 1.0, "wdth": 0.0},
                {"strs": 100, "undo": -200, "unds": 150, "hasc": 1100},
                True,
                id="wght=1.0,wdth=0.0",
            ),
            pytest.param(
                {"wght": 0.0, "wdth": -1.0},
                {"strs": 20, "undo": -100, "unds": 50, "hasc": 1000},
                True,
                id="wght=0.0,wdth=-1.0",
            ),
            pytest.param(
                {"wght": 0.5, "wdth": -0.5},
                {"strs": 55, "undo": -145, "unds": 95, "hasc": 1050},
                True,
                id="wght=0.5,wdth=-0.5",
            ),
            pytest.param(
                {"wght": 1.0, "wdth": -1.0},
                {"strs": 50, "undo": -180, "unds": 130, "hasc": 1100},
                True,
                id="wght=0.5,wdth=-0.5",
            ),
            pytest.param(
                {"wght": 1.0, "wdth": 0.0},
                {"strs": 100, "undo": -200, "unds": 150, "hasc": 1100},
                False,
                id="wght=1.0,wdth=0.0,no_sync_vmetrics",
            ),
        ],
    )
    def test_full_instance(self, varfont, location, sync_vmetrics, expected):
        location = instancer.NormalizedAxisLimits(location)

        # check vertical metrics are in sync before...
        if sync_vmetrics:
            assert varfont["OS/2"].sTypoAscender == varfont["hhea"].ascender
            assert varfont["OS/2"].sTypoDescender == varfont["hhea"].descender
            assert varfont["OS/2"].sTypoLineGap == varfont["hhea"].lineGap
        else:
            # force them not to be in sync
            varfont["OS/2"].sTypoDescender -= 100
            varfont["OS/2"].sTypoLineGap += 200

        instancer.instantiateMVAR(varfont, location)

        for mvar_tag, expected_value in expected.items():
            table_tag, item_name = MVAR_ENTRIES[mvar_tag]
            assert getattr(varfont[table_tag], item_name) == expected_value

        # ... as well as after instancing, but only if they were already
        # https://github.com/fonttools/fonttools/issues/3297
        if sync_vmetrics:
            assert varfont["OS/2"].sTypoAscender == varfont["hhea"].ascender
            assert varfont["OS/2"].sTypoDescender == varfont["hhea"].descender
            assert varfont["OS/2"].sTypoLineGap == varfont["hhea"].lineGap
        else:
            assert varfont["OS/2"].sTypoDescender != varfont["hhea"].descender
            assert varfont["OS/2"].sTypoLineGap != varfont["hhea"].lineGap

        assert "MVAR" not in varfont


class InstantiateHVARTest(object):
    # the 'expectedDeltas' below refer to the VarData item deltas for the "hyphen"
    # glyph in the PartialInstancerTest-VF.ttx test font, that are left after
    # partial instancing
    @pytest.mark.parametrize(
        "location, expectedRegions, expectedDeltas",
        [
            ({"wght": -1.0}, [{"wdth": (-1.0, -1.0, 0)}], [-59]),
            ({"wght": 0}, [{"wdth": (-1.0, -1.0, 0)}], [-48]),
            ({"wght": 1.0}, [{"wdth": (-1.0, -1.0, 0)}], [7]),
            (
                {"wdth": -1.0},
                [
                    {"wght": (-1.0, -1.0, 0.0)},
                    {"wght": (0.0, 0.6099854, 1.0)},
                    {"wght": (0.6099854, 1.0, 1.0)},
                ],
                [-11, 31, 51],
            ),
            ({"wdth": 0}, [{"wght": (0.6099854, 1.0, 1.0)}], [-4]),
        ],
    )
    def test_partial_instance(self, varfont, location, expectedRegions, expectedDeltas):
        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateHVAR(varfont, location)

        assert "HVAR" in varfont
        hvar = varfont["HVAR"].table
        varStore = hvar.VarStore

        regions = varStore.VarRegionList.Region
        fvarAxes = [a for a in varfont["fvar"].axes if a.axisTag not in location]
        regionDicts = [reg.get_support(fvarAxes) for reg in regions]
        assert len(regionDicts) == len(expectedRegions)
        for region, expectedRegion in zip(regionDicts, expectedRegions):
            assert region.keys() == expectedRegion.keys()
            for axisTag, support in region.items():
                assert support == pytest.approx(expectedRegion[axisTag])

        assert len(varStore.VarData) == 1
        assert varStore.VarData[0].ItemCount == 2

        assert hvar.AdvWidthMap is not None
        advWithMap = hvar.AdvWidthMap.mapping

        assert advWithMap[".notdef"] == advWithMap["space"]
        varIdx = advWithMap[".notdef"]
        # these glyphs have no metrics variations in the test font
        assert varStore.VarData[varIdx >> 16].Item[varIdx & 0xFFFF] == (
            [0] * varStore.VarData[0].VarRegionCount
        )

        varIdx = advWithMap["hyphen"]
        assert varStore.VarData[varIdx >> 16].Item[varIdx & 0xFFFF] == expectedDeltas

    def test_full_instance(self, varfont):
        location = instancer.NormalizedAxisLimits(wght=0, wdth=0)

        instancer.instantiateHVAR(varfont, location)

        assert "HVAR" not in varfont

    def test_partial_instance_keep_empty_table(self, varfont):
        # Append an additional dummy axis to fvar, for which the current HVAR table
        # in our test 'varfont' contains no variation data.
        # Instancing the other two wght and wdth axes should leave HVAR table empty,
        # to signal there are variations to the glyph's advance widths.
        fvar = varfont["fvar"]
        axis = _f_v_a_r.Axis()
        axis.axisTag = "TEST"
        fvar.axes.append(axis)

        location = instancer.NormalizedAxisLimits(wght=0, wdth=0)

        instancer.instantiateHVAR(varfont, location)

        assert "HVAR" in varfont

        varStore = varfont["HVAR"].table.VarStore

        assert varStore.VarRegionList.RegionCount == 0
        assert not varStore.VarRegionList.Region
        assert varStore.VarRegionList.RegionAxisCount == 1


class InstantiateItemVariationStoreTest(object):
    def test_VarRegion_get_support(self):
        axisOrder = ["wght", "wdth", "opsz"]
        regionAxes = {"wdth": (-1.0, -1.0, 0.0), "wght": (0.0, 1.0, 1.0)}
        region = builder.buildVarRegion(regionAxes, axisOrder)

        assert len(region.VarRegionAxis) == 3
        assert region.VarRegionAxis[2].PeakCoord == 0

        fvarAxes = [SimpleNamespace(axisTag=axisTag) for axisTag in axisOrder]

        assert region.get_support(fvarAxes) == regionAxes

    @pytest.fixture
    def varStore(self):
        return builder.buildVarStore(
            builder.buildVarRegionList(
                [
                    {"wght": (-1.0, -1.0, 0)},
                    {"wght": (0, 0.5, 1.0)},
                    {"wght": (0.5, 1.0, 1.0)},
                    {"wdth": (-1.0, -1.0, 0)},
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)},
                    {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)},
                    {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)},
                ],
                ["wght", "wdth"],
            ),
            [
                builder.buildVarData([0, 1, 2], [[100, 100, 100], [100, 100, 100]]),
                builder.buildVarData(
                    [3, 4, 5, 6], [[100, 100, 100, 100], [100, 100, 100, 100]]
                ),
            ],
        )

    @pytest.mark.parametrize(
        "location, expected_deltas, num_regions",
        [
            ({"wght": 0}, [[0, 0], [0, 0]], 1),
            ({"wght": 0.25}, [[50, 50], [0, 0]], 1),
            ({"wdth": 0}, [[0, 0], [0, 0]], 3),
            ({"wdth": -0.75}, [[0, 0], [75, 75]], 3),
            ({"wght": 0, "wdth": 0}, [[0, 0], [0, 0]], 0),
            ({"wght": 0.25, "wdth": 0}, [[50, 50], [0, 0]], 0),
            ({"wght": 0, "wdth": -0.75}, [[0, 0], [75, 75]], 0),
        ],
    )
    def test_instantiate_default_deltas(
        self, varStore, fvarAxes, location, expected_deltas, num_regions
    ):
        location = instancer.NormalizedAxisLimits(location)

        defaultDeltas = instancer.instantiateItemVariationStore(
            varStore, fvarAxes, location
        )

        defaultDeltaArray = []
        for varidx, delta in sorted(defaultDeltas.items()):
            if varidx == varStore.NO_VARIATION_INDEX:
                continue
            major, minor = varidx >> 16, varidx & 0xFFFF
            if major == len(defaultDeltaArray):
                defaultDeltaArray.append([])
            assert len(defaultDeltaArray[major]) == minor
            defaultDeltaArray[major].append(delta)

        assert defaultDeltaArray == expected_deltas
        assert varStore.VarRegionList.RegionCount == num_regions


class TupleVarStoreAdapterTest(object):
    def test_instantiate(self):
        regions = [
            {"wght": (-1.0, -1.0, 0)},
            {"wght": (0.0, 1.0, 1.0)},
            {"wdth": (-1.0, -1.0, 0)},
            {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)},
        ]
        axisOrder = ["wght", "wdth"]
        tupleVarData = [
            [
                TupleVariation({"wght": (-1.0, -1.0, 0)}, [10, 70]),
                TupleVariation({"wght": (0.0, 1.0, 1.0)}, [30, 90]),
                TupleVariation(
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)}, [-40, -100]
                ),
                TupleVariation(
                    {"wght": (0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)}, [-60, -120]
                ),
            ],
            [
                TupleVariation({"wdth": (-1.0, -1.0, 0)}, [5, 45]),
                TupleVariation(
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)}, [-15, -55]
                ),
                TupleVariation(
                    {"wght": (0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)}, [-35, -75]
                ),
            ],
        ]
        adapter = instancer._TupleVarStoreAdapter(
            regions, axisOrder, tupleVarData, itemCounts=[2, 2]
        )
        location = instancer.NormalizedAxisLimits(wght=0.5)

        defaultDeltaArray = adapter.instantiate(location)

        assert defaultDeltaArray == [[15, 45], [0, 0]]
        assert adapter.regions == [{"wdth": (-1.0, -1.0, 0)}]
        assert adapter.tupleVarData == [
            [TupleVariation({"wdth": (-1.0, -1.0, 0)}, [-30, -60])],
            [TupleVariation({"wdth": (-1.0, -1.0, 0)}, [-12, 8])],
        ]

    def test_rebuildRegions(self):
        regions = [
            {"wght": (-1.0, -1.0, 0)},
            {"wght": (0.0, 1.0, 1.0)},
            {"wdth": (-1.0, -1.0, 0)},
            {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)},
        ]
        axisOrder = ["wght", "wdth"]
        variations = []
        for region in regions:
            variations.append(TupleVariation(region, [100]))
        tupleVarData = [variations[:3], variations[3:]]
        adapter = instancer._TupleVarStoreAdapter(
            regions, axisOrder, tupleVarData, itemCounts=[1, 1]
        )

        adapter.rebuildRegions()

        assert adapter.regions == regions

        del tupleVarData[0][2]
        tupleVarData[1][0].axes = {"wght": (-1.0, -0.5, 0)}
        tupleVarData[1][1].axes = {"wght": (0, 0.5, 1.0)}

        adapter.rebuildRegions()

        assert adapter.regions == [
            {"wght": (-1.0, -1.0, 0)},
            {"wght": (0.0, 1.0, 1.0)},
            {"wght": (-1.0, -0.5, 0)},
            {"wght": (0, 0.5, 1.0)},
        ]

    def test_roundtrip(self, fvarAxes):
        regions = [
            {"wght": (-1.0, -1.0, 0)},
            {"wght": (0, 0.5, 1.0)},
            {"wght": (0.5, 1.0, 1.0)},
            {"wdth": (-1.0, -1.0, 0)},
            {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)},
        ]
        axisOrder = [axis.axisTag for axis in fvarAxes]

        itemVarStore = builder.buildVarStore(
            builder.buildVarRegionList(regions, axisOrder),
            [
                builder.buildVarData(
                    [0, 1, 2, 4, 5, 6],
                    [[10, -20, 30, -40, 50, -60], [70, -80, 90, -100, 110, -120]],
                ),
                builder.buildVarData(
                    [3, 4, 5, 6], [[5, -15, 25, -35], [45, -55, 65, -75]]
                ),
            ],
        )

        adapter = instancer._TupleVarStoreAdapter.fromItemVarStore(
            itemVarStore, fvarAxes
        )

        assert adapter.tupleVarData == [
            [
                TupleVariation({"wght": (-1.0, -1.0, 0)}, [10, 70]),
                TupleVariation({"wght": (0, 0.5, 1.0)}, [-20, -80]),
                TupleVariation({"wght": (0.5, 1.0, 1.0)}, [30, 90]),
                TupleVariation(
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)}, [-40, -100]
                ),
                TupleVariation(
                    {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)}, [50, 110]
                ),
                TupleVariation(
                    {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)}, [-60, -120]
                ),
            ],
            [
                TupleVariation({"wdth": (-1.0, -1.0, 0)}, [5, 45]),
                TupleVariation(
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)}, [-15, -55]
                ),
                TupleVariation(
                    {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)}, [25, 65]
                ),
                TupleVariation(
                    {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)}, [-35, -75]
                ),
            ],
        ]
        assert adapter.itemCounts == [data.ItemCount for data in itemVarStore.VarData]
        assert adapter.regions == regions
        assert adapter.axisOrder == axisOrder

        itemVarStore2 = adapter.asItemVarStore()

        assert [
            reg.get_support(fvarAxes) for reg in itemVarStore2.VarRegionList.Region
        ] == regions

        assert itemVarStore2.VarDataCount == 2
        assert itemVarStore2.VarData[0].VarRegionIndex == [0, 1, 2, 4, 5, 6]
        assert itemVarStore2.VarData[0].Item == [
            [10, -20, 30, -40, 50, -60],
            [70, -80, 90, -100, 110, -120],
        ]
        assert itemVarStore2.VarData[1].VarRegionIndex == [3, 4, 5, 6]
        assert itemVarStore2.VarData[1].Item == [[5, -15, 25, -35], [45, -55, 65, -75]]


def makeTTFont(glyphOrder, features):
    font = ttLib.TTFont()
    font.setGlyphOrder(glyphOrder)
    addOpenTypeFeaturesFromString(font, features)
    font["name"] = ttLib.newTable("name")
    return font


def _makeDSAxesDict(axes):
    dsAxes = collections.OrderedDict()
    for axisTag, axisValues in axes:
        axis = designspaceLib.AxisDescriptor()
        axis.name = axis.tag = axis.labelNames["en"] = axisTag
        axis.minimum, axis.default, axis.maximum = axisValues
        dsAxes[axis.tag] = axis
    return dsAxes


def makeVariableFont(masters, baseIndex, axes, masterLocations):
    vf = deepcopy(masters[baseIndex])
    dsAxes = _makeDSAxesDict(axes)
    fvar = varLib._add_fvar(vf, dsAxes, instances=())
    axisTags = [axis.axisTag for axis in fvar.axes]
    normalizedLocs = [models.normalizeLocation(m, dict(axes)) for m in masterLocations]
    model = models.VariationModel(normalizedLocs, axisOrder=axisTags)
    varLib._merge_OTL(vf, model, masters, axisTags)
    return vf


def makeParametrizedVF(glyphOrder, features, values, increments):
    # Create a test VF with given glyphs and parametrized OTL features.
    # The VF is built from 9 masters (3 x 3 along wght and wdth), with
    # locations hard-coded and base master at wght=400 and wdth=100.
    # 'values' is a list of initial values that are interpolated in the
    # 'features' string, and incremented for each subsequent master by the
    # given 'increments' (list of 2-tuple) along the two axes.
    assert values and len(values) == len(increments)
    assert all(len(i) == 2 for i in increments)
    masterLocations = [
        {"wght": 100, "wdth": 50},
        {"wght": 100, "wdth": 100},
        {"wght": 100, "wdth": 150},
        {"wght": 400, "wdth": 50},
        {"wght": 400, "wdth": 100},  # base master
        {"wght": 400, "wdth": 150},
        {"wght": 700, "wdth": 50},
        {"wght": 700, "wdth": 100},
        {"wght": 700, "wdth": 150},
    ]
    n = len(values)
    values = list(values)
    masters = []
    for _ in range(3):
        for _ in range(3):
            master = makeTTFont(glyphOrder, features=features % tuple(values))
            masters.append(master)
            for i in range(n):
                values[i] += increments[i][1]
        for i in range(n):
            values[i] += increments[i][0]
    baseIndex = 4
    axes = [("wght", (100, 400, 700)), ("wdth", (50, 100, 150))]
    vf = makeVariableFont(masters, baseIndex, axes, masterLocations)
    return vf


@pytest.fixture
def varfontGDEF():
    glyphOrder = [".notdef", "f", "i", "f_i"]
    features = (
        "feature liga { sub f i by f_i;} liga;"
        "table GDEF { LigatureCaretByPos f_i %d; } GDEF;"
    )
    values = [100]
    increments = [(+30, +10)]
    return makeParametrizedVF(glyphOrder, features, values, increments)


@pytest.fixture
def varfontGPOS():
    glyphOrder = [".notdef", "V", "A"]
    features = "feature kern { pos V A %d; } kern;"
    values = [-80]
    increments = [(-10, -5)]
    return makeParametrizedVF(glyphOrder, features, values, increments)


@pytest.fixture
def varfontGPOS2():
    glyphOrder = [".notdef", "V", "A", "acutecomb"]
    features = (
        "markClass [acutecomb] <anchor 150 -10> @TOP_MARKS;"
        "feature mark {"
        "  pos base A <anchor %d 450> mark @TOP_MARKS;"
        "} mark;"
        "feature kern {"
        "  pos V A %d;"
        "} kern;"
    )
    values = [200, -80]
    increments = [(+30, +10), (-10, -5)]
    return makeParametrizedVF(glyphOrder, features, values, increments)


class InstantiateOTLTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0}, 110),  # -60
            ({"wght": 0}, 170),
            ({"wght": 0.5}, 200),  # +30
            ({"wght": 1.0}, 230),  # +60
            ({"wdth": -1.0}, 160),  # -10
            ({"wdth": -0.3}, 167),  # -3
            ({"wdth": 0}, 170),
            ({"wdth": 1.0}, 180),  # +10
        ],
    )
    def test_pin_and_drop_axis_GDEF(self, varfontGDEF, location, expected):
        vf = varfontGDEF
        assert "GDEF" in vf

        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateOTL(vf, location)

        assert "GDEF" in vf
        gdef = vf["GDEF"].table
        assert gdef.Version == 0x00010003
        assert gdef.VarStore
        assert gdef.LigCaretList
        caretValue = gdef.LigCaretList.LigGlyph[0].CaretValue[0]
        assert caretValue.Format == 3
        assert hasattr(caretValue, "DeviceTable")
        assert caretValue.DeviceTable.DeltaFormat == 0x8000
        assert caretValue.Coordinate == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0, "wdth": -1.0}, 100),  # -60 - 10
            ({"wght": -1.0, "wdth": 0.0}, 110),  # -60
            ({"wght": -1.0, "wdth": 1.0}, 120),  # -60 + 10
            ({"wght": 0.0, "wdth": -1.0}, 160),  # -10
            ({"wght": 0.0, "wdth": 0.0}, 170),
            ({"wght": 0.0, "wdth": 1.0}, 180),  # +10
            ({"wght": 1.0, "wdth": -1.0}, 220),  # +60 - 10
            ({"wght": 1.0, "wdth": 0.0}, 230),  # +60
            ({"wght": 1.0, "wdth": 1.0}, 240),  # +60 + 10
        ],
    )
    def test_full_instance_GDEF(self, varfontGDEF, location, expected):
        vf = varfontGDEF
        assert "GDEF" in vf

        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateOTL(vf, location)

        assert "GDEF" in vf
        gdef = vf["GDEF"].table
        assert gdef.Version == 0x00010000
        assert not hasattr(gdef, "VarStore")
        assert gdef.LigCaretList
        caretValue = gdef.LigCaretList.LigGlyph[0].CaretValue[0]
        assert caretValue.Format == 1
        assert not hasattr(caretValue, "DeviceTable")
        assert caretValue.Coordinate == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0}, -85),  # +25
            ({"wght": 0}, -110),
            ({"wght": 1.0}, -135),  # -25
            ({"wdth": -1.0}, -105),  # +5
            ({"wdth": 0}, -110),
            ({"wdth": 1.0}, -115),  # -5
        ],
    )
    def test_pin_and_drop_axis_GPOS_kern(self, varfontGPOS, location, expected):
        vf = varfontGPOS
        assert "GDEF" in vf
        assert "GPOS" in vf

        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateOTL(vf, location)

        gdef = vf["GDEF"].table
        gpos = vf["GPOS"].table
        assert gdef.Version == 0x00010003
        assert gdef.VarStore

        assert gpos.LookupList.Lookup[0].LookupType == 2  # PairPos
        pairPos = gpos.LookupList.Lookup[0].SubTable[0]
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert valueRec1.XAdvDevice
        assert valueRec1.XAdvDevice.DeltaFormat == 0x8000
        assert valueRec1.XAdvance == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0, "wdth": -1.0}, -80),  # +25 + 5
            ({"wght": -1.0, "wdth": 0.0}, -85),  # +25
            ({"wght": -1.0, "wdth": 1.0}, -90),  # +25 - 5
            ({"wght": 0.0, "wdth": -1.0}, -105),  # +5
            ({"wght": 0.0, "wdth": 0.0}, -110),
            ({"wght": 0.0, "wdth": 1.0}, -115),  # -5
            ({"wght": 1.0, "wdth": -1.0}, -130),  # -25 + 5
            ({"wght": 1.0, "wdth": 0.0}, -135),  # -25
            ({"wght": 1.0, "wdth": 1.0}, -140),  # -25 - 5
        ],
    )
    def test_full_instance_GPOS_kern(self, varfontGPOS, location, expected):
        vf = varfontGPOS
        assert "GDEF" in vf
        assert "GPOS" in vf

        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateOTL(vf, location)

        assert "GDEF" not in vf
        gpos = vf["GPOS"].table

        assert gpos.LookupList.Lookup[0].LookupType == 2  # PairPos
        pairPos = gpos.LookupList.Lookup[0].SubTable[0]
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert not hasattr(valueRec1, "XAdvDevice")
        assert valueRec1.XAdvance == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0}, (210, -85)),  # -60, +25
            ({"wght": 0}, (270, -110)),
            ({"wght": 0.5}, (300, -122)),  # +30, -12
            ({"wght": 1.0}, (330, -135)),  # +60, -25
            ({"wdth": -1.0}, (260, -105)),  # -10, +5
            ({"wdth": -0.3}, (267, -108)),  # -3, +2
            ({"wdth": 0}, (270, -110)),
            ({"wdth": 1.0}, (280, -115)),  # +10, -5
        ],
    )
    def test_pin_and_drop_axis_GPOS_mark_and_kern(
        self, varfontGPOS2, location, expected
    ):
        vf = varfontGPOS2
        assert "GDEF" in vf
        assert "GPOS" in vf

        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateOTL(vf, location)

        v1, v2 = expected
        gdef = vf["GDEF"].table
        gpos = vf["GPOS"].table
        assert gdef.Version == 0x00010003
        assert gdef.VarStore
        assert gdef.GlyphClassDef

        assert gpos.LookupList.Lookup[0].LookupType == 4  # MarkBasePos
        markBasePos = gpos.LookupList.Lookup[0].SubTable[0]
        baseAnchor = markBasePos.BaseArray.BaseRecord[0].BaseAnchor[0]
        assert baseAnchor.Format == 3
        assert baseAnchor.XDeviceTable
        assert baseAnchor.XDeviceTable.DeltaFormat == 0x8000
        assert not baseAnchor.YDeviceTable
        assert baseAnchor.XCoordinate == v1
        assert baseAnchor.YCoordinate == 450

        assert gpos.LookupList.Lookup[1].LookupType == 2  # PairPos
        pairPos = gpos.LookupList.Lookup[1].SubTable[0]
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert valueRec1.XAdvDevice
        assert valueRec1.XAdvDevice.DeltaFormat == 0x8000
        assert valueRec1.XAdvance == v2

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0, "wdth": -1.0}, (200, -80)),  # -60 - 10, +25 + 5
            ({"wght": -1.0, "wdth": 0.0}, (210, -85)),  # -60, +25
            ({"wght": -1.0, "wdth": 1.0}, (220, -90)),  # -60 + 10, +25 - 5
            ({"wght": 0.0, "wdth": -1.0}, (260, -105)),  # -10, +5
            ({"wght": 0.0, "wdth": 0.0}, (270, -110)),
            ({"wght": 0.0, "wdth": 1.0}, (280, -115)),  # +10, -5
            ({"wght": 1.0, "wdth": -1.0}, (320, -130)),  # +60 - 10, -25 + 5
            ({"wght": 1.0, "wdth": 0.0}, (330, -135)),  # +60, -25
            ({"wght": 1.0, "wdth": 1.0}, (340, -140)),  # +60 + 10, -25 - 5
        ],
    )
    def test_full_instance_GPOS_mark_and_kern(self, varfontGPOS2, location, expected):
        vf = varfontGPOS2
        assert "GDEF" in vf
        assert "GPOS" in vf

        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateOTL(vf, location)

        v1, v2 = expected
        gdef = vf["GDEF"].table
        gpos = vf["GPOS"].table
        assert gdef.Version == 0x00010000
        assert not hasattr(gdef, "VarStore")
        assert gdef.GlyphClassDef

        assert gpos.LookupList.Lookup[0].LookupType == 4  # MarkBasePos
        markBasePos = gpos.LookupList.Lookup[0].SubTable[0]
        baseAnchor = markBasePos.BaseArray.BaseRecord[0].BaseAnchor[0]
        assert baseAnchor.Format == 1
        assert not hasattr(baseAnchor, "XDeviceTable")
        assert not hasattr(baseAnchor, "YDeviceTable")
        assert baseAnchor.XCoordinate == v1
        assert baseAnchor.YCoordinate == 450

        assert gpos.LookupList.Lookup[1].LookupType == 2  # PairPos
        pairPos = gpos.LookupList.Lookup[1].SubTable[0]
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert not hasattr(valueRec1, "XAdvDevice")
        assert valueRec1.XAdvance == v2

    def test_GPOS_ValueRecord_XAdvDevice_wtihout_XAdvance(self):
        # Test VF contains a PairPos adjustment in which the default instance
        # has no XAdvance but there are deltas in XAdvDevice (VariationIndex).
        vf = ttLib.TTFont()
        vf.importXML(os.path.join(TESTDATA, "PartialInstancerTest4-VF.ttx"))
        pairPos = vf["GPOS"].table.LookupList.Lookup[0].SubTable[0]
        assert pairPos.ValueFormat1 == 0x40
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert not hasattr(valueRec1, "XAdvance")
        assert valueRec1.XAdvDevice.DeltaFormat == 0x8000
        outer = valueRec1.XAdvDevice.StartSize
        inner = valueRec1.XAdvDevice.EndSize
        assert vf["GDEF"].table.VarStore.VarData[outer].Item[inner] == [-50]

        # check that MutatorMerger for ValueRecord doesn't raise AttributeError
        # when XAdvDevice is present but there's no corresponding XAdvance.
        instancer.instantiateOTL(vf, instancer.NormalizedAxisLimits(wght=0.5))

        pairPos = vf["GPOS"].table.LookupList.Lookup[0].SubTable[0]
        assert pairPos.ValueFormat1 == 0x4
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert not hasattr(valueRec1, "XAdvDevice")
        assert valueRec1.XAdvance == -25


class InstantiateAvarTest(object):
    @pytest.mark.parametrize("location", [{"wght": 0.0}, {"wdth": 0.0}])
    def test_pin_and_drop_axis(self, varfont, location):
        location = instancer.AxisLimits(location)

        instancer.instantiateAvar(varfont, location)

        assert set(varfont["avar"].segments).isdisjoint(location)

    def test_full_instance(self, varfont):
        location = instancer.AxisLimits(wght=0.0, wdth=0.0)

        instancer.instantiateAvar(varfont, location)

        assert "avar" not in varfont

    @staticmethod
    def quantizeF2Dot14Floats(mapping):
        return {
            floatToFixedToFloat(k, 14): floatToFixedToFloat(v, 14)
            for k, v in mapping.items()
        }

    # the following values come from NotoSans-VF.ttf
    DFLT_WGHT_MAPPING = {
        -1.0: -1.0,
        -0.6667: -0.7969,
        -0.3333: -0.5,
        0: 0,
        0.2: 0.18,
        0.4: 0.38,
        0.6: 0.61,
        0.8: 0.79,
        1.0: 1.0,
    }

    DFLT_WDTH_MAPPING = {-1.0: -1.0, -0.6667: -0.7, -0.3333: -0.36664, 0: 0, 1.0: 1.0}

    @pytest.fixture
    def varfont(self):
        fvarAxes = ("wght", (100, 400, 900)), ("wdth", (62.5, 100, 100))
        avarSegments = {
            "wght": self.quantizeF2Dot14Floats(self.DFLT_WGHT_MAPPING),
            "wdth": self.quantizeF2Dot14Floats(self.DFLT_WDTH_MAPPING),
        }
        varfont = ttLib.TTFont()
        varfont["name"] = ttLib.newTable("name")
        varLib._add_fvar(varfont, _makeDSAxesDict(fvarAxes), instances=())
        avar = varfont["avar"] = ttLib.newTable("avar")
        avar.segments = avarSegments
        return varfont

    @pytest.mark.parametrize(
        "axisLimits, expectedSegments",
        [
            pytest.param(
                {"wght": (100, 900)},
                {"wght": DFLT_WGHT_MAPPING, "wdth": DFLT_WDTH_MAPPING},
                id="wght=100:900",
            ),
            pytest.param(
                {"wght": (400, 900)},
                {
                    "wght": {
                        -1.0: -1.0,
                        0: 0,
                        0.2: 0.18,
                        0.4: 0.38,
                        0.6: 0.61,
                        0.8: 0.79,
                        1.0: 1.0,
                    },
                    "wdth": DFLT_WDTH_MAPPING,
                },
                id="wght=400:900",
            ),
            pytest.param(
                {"wght": (100, 400)},
                {
                    "wght": {
                        -1.0: -1.0,
                        -0.6667: -0.7969,
                        -0.3333: -0.5,
                        0: 0,
                        1.0: 1.0,
                    },
                    "wdth": DFLT_WDTH_MAPPING,
                },
                id="wght=100:400",
            ),
            pytest.param(
                {"wght": (400, 800)},
                {
                    "wght": {
                        -1.0: -1.0,
                        0: 0,
                        0.25: 0.22784,
                        0.50006: 0.48103,
                        0.75: 0.77214,
                        1.0: 1.0,
                    },
                    "wdth": DFLT_WDTH_MAPPING,
                },
                id="wght=400:800",
            ),
            pytest.param(
                {"wght": (400, 700)},
                {
                    "wght": {
                        -1.0: -1.0,
                        0: 0,
                        0.3334: 0.2951,
                        0.66675: 0.623,
                        1.0: 1.0,
                    },
                    "wdth": DFLT_WDTH_MAPPING,
                },
                id="wght=400:700",
            ),
            pytest.param(
                {"wght": (400, 600)},
                {
                    "wght": {-1.0: -1.0, 0: 0, 0.5: 0.47363, 1.0: 1.0},
                    "wdth": DFLT_WDTH_MAPPING,
                },
                id="wght=400:600",
            ),
            pytest.param(
                {"wdth": (62.5, 100)},
                {
                    "wght": DFLT_WGHT_MAPPING,
                    "wdth": {
                        -1.0: -1.0,
                        -0.6667: -0.7,
                        -0.3333: -0.36664,
                        0: 0,
                        1.0: 1.0,
                    },
                },
                id="wdth=62.5:100",
            ),
            pytest.param(
                {"wdth": (70, 100)},
                {
                    "wght": DFLT_WGHT_MAPPING,
                    "wdth": {
                        -1.0: -1.0,
                        -0.8334: -0.85364,
                        -0.4166: -0.44714,
                        0: 0,
                        1.0: 1.0,
                    },
                },
                id="wdth=70:100",
            ),
            pytest.param(
                {"wdth": (75, 100)},
                {
                    "wght": DFLT_WGHT_MAPPING,
                    "wdth": {-1.0: -1.0, -0.49994: -0.52374, 0: 0, 1.0: 1.0},
                },
                id="wdth=75:100",
            ),
            pytest.param(
                {"wdth": (77, 100)},
                {
                    "wght": DFLT_WGHT_MAPPING,
                    "wdth": {-1.0: -1.0, -0.54346: -0.56696, 0: 0, 1.0: 1.0},
                },
                id="wdth=77:100",
            ),
            pytest.param(
                {"wdth": (87.5, 100)},
                {"wght": DFLT_WGHT_MAPPING, "wdth": {-1.0: -1.0, 0: 0, 1.0: 1.0}},
                id="wdth=87.5:100",
            ),
        ],
    )
    def test_limit_axes(self, varfont, axisLimits, expectedSegments):
        axisLimits = instancer.AxisLimits(axisLimits)

        instancer.instantiateAvar(varfont, axisLimits)

        newSegments = varfont["avar"].segments
        expectedSegments = {
            axisTag: self.quantizeF2Dot14Floats(mapping)
            for axisTag, mapping in expectedSegments.items()
        }
        assert newSegments == expectedSegments

    @pytest.mark.parametrize(
        "invalidSegmentMap",
        [
            pytest.param({0.5: 0.5}, id="missing-required-maps-1"),
            pytest.param({-1.0: -1.0, 1.0: 1.0}, id="missing-required-maps-2"),
            pytest.param(
                {-1.0: -1.0, 0: 0, 0.5: 0.5, 0.6: 0.4, 1.0: 1.0},
                id="retrograde-value-maps",
            ),
        ],
    )
    def test_drop_invalid_segment_map(self, varfont, invalidSegmentMap, caplog):
        varfont["avar"].segments["wght"] = invalidSegmentMap

        axisLimits = instancer.AxisLimits(wght=(100, 400))

        with caplog.at_level(logging.WARNING, logger="fontTools.varLib.instancer"):
            instancer.instantiateAvar(varfont, axisLimits)

        assert "Invalid avar" in caplog.text
        assert "wght" not in varfont["avar"].segments

    def test_isValidAvarSegmentMap(self):
        assert instancer._isValidAvarSegmentMap("FOOO", {})
        assert instancer._isValidAvarSegmentMap("FOOO", {-1.0: -1.0, 0: 0, 1.0: 1.0})
        assert instancer._isValidAvarSegmentMap(
            "FOOO", {-1.0: -1.0, 0: 0, 0.5: 0.5, 1.0: 1.0}
        )
        assert instancer._isValidAvarSegmentMap(
            "FOOO", {-1.0: -1.0, 0: 0, 0.5: 0.5, 0.7: 0.5, 1.0: 1.0}
        )


class InstantiateFvarTest(object):
    @pytest.mark.parametrize(
        "location, instancesLeft",
        [
            (
                {"wght": 400.0},
                ["Regular", "SemiCondensed", "Condensed", "ExtraCondensed"],
            ),
            (
                {"wght": 100.0},
                ["Thin", "SemiCondensed Thin", "Condensed Thin", "ExtraCondensed Thin"],
            ),
            (
                {"wdth": 100.0},
                [
                    "Thin",
                    "ExtraLight",
                    "Light",
                    "Regular",
                    "Medium",
                    "SemiBold",
                    "Bold",
                    "ExtraBold",
                    "Black",
                ],
            ),
            # no named instance at pinned location
            ({"wdth": 90.0}, []),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, location, instancesLeft):
        location = instancer.AxisLimits(location)

        instancer.instantiateFvar(varfont, location)

        fvar = varfont["fvar"]
        assert {a.axisTag for a in fvar.axes}.isdisjoint(location)

        for instance in fvar.instances:
            assert set(instance.coordinates).isdisjoint(location)

        name = varfont["name"]
        assert [
            name.getDebugName(instance.subfamilyNameID) for instance in fvar.instances
        ] == instancesLeft

    def test_full_instance(self, varfont):
        location = instancer.AxisLimits({"wght": 0.0, "wdth": 0.0})

        instancer.instantiateFvar(varfont, location)

        assert "fvar" not in varfont

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": (30, 40, 700)}, (100, 100, 700)),
            ({"wght": (30, 40, None)}, (100, 100, 900)),
            ({"wght": (30, None, 700)}, (100, 400, 700)),
            ({"wght": (None, 200, 700)}, (100, 200, 700)),
            ({"wght": (40, None, None)}, (100, 400, 900)),
            ({"wght": (None, 40, None)}, (100, 100, 900)),
            ({"wght": (None, None, 700)}, (100, 400, 700)),
            ({"wght": (None, None, None)}, (100, 400, 900)),
        ],
    )
    def test_axis_limits(self, varfont, location, expected):
        location = instancer.AxisLimits(location)

        varfont = instancer.instantiateVariableFont(varfont, location)

        fvar = varfont["fvar"]
        axes = {a.axisTag: a for a in fvar.axes}
        assert axes["wght"].minValue == expected[0]
        assert axes["wght"].defaultValue == expected[1]
        assert axes["wght"].maxValue == expected[2]


class InstantiateSTATTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": 400}, ["Regular", "Condensed", "Upright", "Normal"]),
            (
                {"wdth": 100},
                ["Thin", "Regular", "Medium", "Black", "Upright", "Normal"],
            ),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, location, expected):
        location = instancer.AxisLimits(location)

        instancer.instantiateSTAT(varfont, location)

        stat = varfont["STAT"].table
        designAxes = {a.AxisTag for a in stat.DesignAxisRecord.Axis}

        assert designAxes == {"wght", "wdth", "ital"}

        name = varfont["name"]
        valueNames = []
        for axisValueTable in stat.AxisValueArray.AxisValue:
            valueName = name.getDebugName(axisValueTable.ValueNameID)
            valueNames.append(valueName)

        assert valueNames == expected

    def test_skip_table_no_axis_value_array(self, varfont):
        varfont["STAT"].table.AxisValueArray = None

        instancer.instantiateSTAT(varfont, instancer.AxisLimits(wght=100))

        assert len(varfont["STAT"].table.DesignAxisRecord.Axis) == 3
        assert varfont["STAT"].table.AxisValueArray is None

    def test_skip_table_axis_value_array_empty(self, varfont):
        varfont["STAT"].table.AxisValueArray.AxisValue = []

        instancer.instantiateSTAT(varfont, {"wght": 100})

        assert len(varfont["STAT"].table.DesignAxisRecord.Axis) == 3
        assert not varfont["STAT"].table.AxisValueArray.AxisValue

    def test_skip_table_no_design_axes(self, varfont):
        stat = otTables.STAT()
        stat.Version = 0x00010001
        stat.populateDefaults()
        assert not stat.DesignAxisRecord
        assert not stat.AxisValueArray
        varfont["STAT"].table = stat

        instancer.instantiateSTAT(varfont, {"wght": 100})

        assert not varfont["STAT"].table.DesignAxisRecord

    @staticmethod
    def get_STAT_axis_values(stat):
        axes = stat.DesignAxisRecord.Axis
        result = []
        for axisValue in stat.AxisValueArray.AxisValue:
            if axisValue.Format == 1:
                result.append((axes[axisValue.AxisIndex].AxisTag, axisValue.Value))
            elif axisValue.Format == 3:
                result.append(
                    (
                        axes[axisValue.AxisIndex].AxisTag,
                        (axisValue.Value, axisValue.LinkedValue),
                    )
                )
            elif axisValue.Format == 2:
                result.append(
                    (
                        axes[axisValue.AxisIndex].AxisTag,
                        (
                            axisValue.RangeMinValue,
                            axisValue.NominalValue,
                            axisValue.RangeMaxValue,
                        ),
                    )
                )
            elif axisValue.Format == 4:
                result.append(
                    tuple(
                        (axes[rec.AxisIndex].AxisTag, rec.Value)
                        for rec in axisValue.AxisValueRecord
                    )
                )
            else:
                raise AssertionError(axisValue.Format)
        return result

    def test_limit_axes(self, varfont2):
        axisLimits = instancer.AxisLimits({"wght": (400, 500), "wdth": (75, 100)})

        instancer.instantiateSTAT(varfont2, axisLimits)

        assert len(varfont2["STAT"].table.AxisValueArray.AxisValue) == 5
        assert self.get_STAT_axis_values(varfont2["STAT"].table) == [
            ("wght", (400.0, 700.0)),
            ("wght", 500.0),
            ("wdth", (93.75, 100.0, 100.0)),
            ("wdth", (81.25, 87.5, 93.75)),
            ("wdth", (68.75, 75.0, 81.25)),
        ]

    def test_limit_axis_value_format_4(self, varfont2):
        stat = varfont2["STAT"].table

        axisValue = otTables.AxisValue()
        axisValue.Format = 4
        axisValue.AxisValueRecord = []
        for tag, value in (("wght", 575), ("wdth", 90)):
            rec = otTables.AxisValueRecord()
            rec.AxisIndex = next(
                i for i, a in enumerate(stat.DesignAxisRecord.Axis) if a.AxisTag == tag
            )
            rec.Value = value
            axisValue.AxisValueRecord.append(rec)
        stat.AxisValueArray.AxisValue.append(axisValue)

        instancer.instantiateSTAT(varfont2, instancer.AxisLimits(wght=(100, 600)))

        assert axisValue in varfont2["STAT"].table.AxisValueArray.AxisValue

        instancer.instantiateSTAT(varfont2, instancer.AxisLimits(wdth=(62.5, 87.5)))

        assert axisValue not in varfont2["STAT"].table.AxisValueArray.AxisValue

    def test_unknown_axis_value_format(self, varfont2, caplog):
        stat = varfont2["STAT"].table
        axisValue = otTables.AxisValue()
        axisValue.Format = 5
        stat.AxisValueArray.AxisValue.append(axisValue)

        with caplog.at_level(logging.WARNING, logger="fontTools.varLib.instancer"):
            instancer.instantiateSTAT(varfont2, instancer.AxisLimits(wght=400))

        assert "Unknown AxisValue table format (5)" in caplog.text
        assert axisValue in varfont2["STAT"].table.AxisValueArray.AxisValue


def test_setMacOverlapFlags():
    flagOverlapCompound = _g_l_y_f.OVERLAP_COMPOUND
    flagOverlapSimple = _g_l_y_f.flagOverlapSimple

    glyf = ttLib.newTable("glyf")
    glyf.glyphOrder = ["a", "b", "c"]
    a = _g_l_y_f.Glyph()
    a.numberOfContours = 1
    a.flags = [0]
    b = _g_l_y_f.Glyph()
    b.numberOfContours = -1
    comp = _g_l_y_f.GlyphComponent()
    comp.flags = 0
    b.components = [comp]
    c = _g_l_y_f.Glyph()
    c.numberOfContours = 0
    glyf.glyphs = {"a": a, "b": b, "c": c}

    instancer.setMacOverlapFlags(glyf)

    assert a.flags[0] & flagOverlapSimple != 0
    assert b.components[0].flags & flagOverlapCompound != 0


@pytest.fixture
def varfont2():
    f = ttLib.TTFont(recalcTimestamp=False)
    f.importXML(os.path.join(TESTDATA, "PartialInstancerTest2-VF.ttx"))
    return f


@pytest.fixture
def varfont3():
    f = ttLib.TTFont(recalcTimestamp=False)
    f.importXML(os.path.join(TESTDATA, "PartialInstancerTest3-VF.ttx"))
    return f


def _dump_ttx(ttFont):
    # compile to temporary bytes stream, reload and dump to XML
    tmp = BytesIO()
    ttFont.save(tmp)
    tmp.seek(0)
    ttFont2 = ttLib.TTFont(tmp, recalcBBoxes=False, recalcTimestamp=False)
    s = StringIO()
    ttFont2.saveXML(s)
    return stripVariableItemsFromTTX(s.getvalue())


def _get_expected_instance_ttx(
    name, *locations, overlap=instancer.OverlapMode.KEEP_AND_SET_FLAGS
):
    filename = f"{name}-VF-instance-{','.join(str(loc) for loc in locations)}"
    if overlap == instancer.OverlapMode.KEEP_AND_DONT_SET_FLAGS:
        filename += "-no-overlap-flags"
    elif overlap == instancer.OverlapMode.REMOVE:
        filename += "-no-overlaps"
    with open(
        os.path.join(TESTDATA, "test_results", f"{filename}.ttx"),
        "r",
        encoding="utf-8",
    ) as fp:
        return stripVariableItemsFromTTX(fp.read())


class InstantiateVariableFontTest(object):
    @pytest.mark.parametrize(
        "wght, wdth",
        [(100, 100), (400, 100), (900, 100), (100, 62.5), (400, 62.5), (900, 62.5)],
    )
    def test_multiple_instancing(self, varfont2, wght, wdth):
        partial = instancer.instantiateVariableFont(varfont2, {"wght": wght})
        instance = instancer.instantiateVariableFont(partial, {"wdth": wdth})

        expected = _get_expected_instance_ttx("PartialInstancerTest2", wght, wdth)

        assert _dump_ttx(instance) == expected

    def test_default_instance(self, varfont2):
        instance = instancer.instantiateVariableFont(
            varfont2, {"wght": None, "wdth": None}
        )

        expected = _get_expected_instance_ttx("PartialInstancerTest2", 400, 100)

        assert _dump_ttx(instance) == expected

    def test_move_weight_width_axis_default(self, varfont2):
        # https://github.com/fonttools/fonttools/issues/2885
        assert varfont2["OS/2"].usWeightClass == 400
        assert varfont2["OS/2"].usWidthClass == 5

        varfont = instancer.instantiateVariableFont(
            varfont2, {"wght": (100, 500, 900), "wdth": 87.5}
        )

        assert varfont["OS/2"].usWeightClass == 500
        assert varfont["OS/2"].usWidthClass == 4

    @pytest.mark.parametrize(
        "overlap, wght",
        [
            (instancer.OverlapMode.KEEP_AND_DONT_SET_FLAGS, 400),
            (instancer.OverlapMode.REMOVE, 400),
            (instancer.OverlapMode.REMOVE, 700),
        ],
    )
    def test_overlap(self, varfont3, wght, overlap):
        pytest.importorskip("pathops")

        location = {"wght": wght}

        instance = instancer.instantiateVariableFont(
            varfont3, location, overlap=overlap
        )

        expected = _get_expected_instance_ttx(
            "PartialInstancerTest3", wght, overlap=overlap
        )

        assert _dump_ttx(instance) == expected

    def test_singlepos(self):
        varfont = ttLib.TTFont(recalcTimestamp=False)
        varfont.importXML(os.path.join(TESTDATA, "SinglePos.ttx"))

        location = {"wght": 280, "opsz": 18}

        instance = instancer.instantiateVariableFont(
            varfont,
            location,
        )

        expected = _get_expected_instance_ttx("SinglePos", *location.values())

        assert _dump_ttx(instance) == expected

    def test_varComposite(self):
        input_path = os.path.join(
            TESTDATA, "..", "..", "..", "ttLib", "data", "varc-ac00-ac01.ttf"
        )
        varfont = ttLib.TTFont(input_path)

        location = {"wght": 600}

        instance = instancer.instantiateVariableFont(
            varfont,
            location,
        )

        location = {"0000": 0.5}

        instance = instancer.instantiateVariableFont(
            varfont,
            location,
        )


def _conditionSetAsDict(conditionSet, axisOrder):
    result = {}
    conditionSets = conditionSet.ConditionTable if conditionSet is not None else []
    for cond in conditionSets:
        assert cond.Format == 1
        axisTag = axisOrder[cond.AxisIndex]
        result[axisTag] = (cond.FilterRangeMinValue, cond.FilterRangeMaxValue)
    return result


def _getSubstitutions(gsub, lookupIndices):
    subs = {}
    for index, lookup in enumerate(gsub.LookupList.Lookup):
        if index in lookupIndices:
            for subtable in lookup.SubTable:
                subs.update(subtable.mapping)
    return subs


def makeFeatureVarsFont(conditionalSubstitutions):
    axes = set()
    glyphs = set()
    for region, substitutions in conditionalSubstitutions:
        for box in region:
            axes.update(box.keys())
        glyphs.update(*substitutions.items())

    varfont = ttLib.TTFont()
    varfont.setGlyphOrder(sorted(glyphs))

    fvar = varfont["fvar"] = ttLib.newTable("fvar")
    fvar.axes = []
    for axisTag in sorted(axes):
        axis = _f_v_a_r.Axis()
        axis.axisTag = Tag(axisTag)
        fvar.axes.append(axis)

    featureVars.addFeatureVariations(varfont, conditionalSubstitutions)

    return varfont


class InstantiateFeatureVariationsTest(object):
    @pytest.mark.parametrize(
        "location, appliedSubs, expectedRecords",
        [
            ({"wght": 0}, {}, [({"cntr": (0.75, 1.0)}, {"uni0041": "uni0061"})]),
            (
                {"wght": -1.0},
                {"uni0061": "uni0041"},
                [
                    ({"cntr": (0, 0.25)}, {"uni0061": "uni0041"}),
                    ({"cntr": (0.75, 1.0)}, {"uni0041": "uni0061"}),
                    ({}, {}),
                ],
            ),
            (
                {"wght": 1.0},
                {"uni0024": "uni0024.nostroke"},
                [
                    (
                        {"cntr": (0.75, 1.0)},
                        {"uni0024": "uni0024.nostroke", "uni0041": "uni0061"},
                    ),
                    ({}, {}),
                ],
            ),
            (
                {"cntr": 0},
                {},
                [
                    ({"wght": (-1.0, -0.45654)}, {"uni0061": "uni0041"}),
                    ({"wght": (0.20886, 1.0)}, {"uni0024": "uni0024.nostroke"}),
                ],
            ),
            (
                {"cntr": 1.0},
                {"uni0041": "uni0061"},
                [
                    (
                        {"wght": (0.20886, 1.0)},
                        {"uni0024": "uni0024.nostroke", "uni0041": "uni0061"},
                    ),
                    ({}, {}),
                ],
            ),
            (
                {"cntr": (-0.5, 0, 1.0)},
                {},
                [
                    (
                        {"wght": (0.20886, 1.0), "cntr": (0.75, 1)},
                        {"uni0024": "uni0024.nostroke", "uni0041": "uni0061"},
                    ),
                    (
                        {"wght": (-1.0, -0.45654), "cntr": (0, 0.25)},
                        {"uni0061": "uni0041"},
                    ),
                    (
                        {"cntr": (0.75, 1.0)},
                        {"uni0041": "uni0061"},
                    ),
                    (
                        {"wght": (0.20886, 1.0)},
                        {"uni0024": "uni0024.nostroke"},
                    ),
                ],
            ),
            (
                {"cntr": (0.8, 0.9, 1.0)},
                {"uni0041": "uni0061"},
                [
                    (
                        {"wght": (0.20886, 1.0)},
                        {"uni0024": "uni0024.nostroke", "uni0041": "uni0061"},
                    ),
                    (
                        {},
                        {"uni0041": "uni0061"},
                    ),
                ],
            ),
            (
                {"cntr": (0.7, 0.9, 1.0)},
                {"uni0041": "uni0061"},
                [
                    (
                        {"cntr": (-0.7499999999999999, 1.0), "wght": (0.20886, 1.0)},
                        {"uni0024": "uni0024.nostroke", "uni0041": "uni0061"},
                    ),
                    (
                        {"cntr": (-0.7499999999999999, 1.0)},
                        {"uni0041": "uni0061"},
                    ),
                    (
                        {"wght": (0.20886, 1.0)},
                        {"uni0024": "uni0024.nostroke"},
                    ),
                    (
                        {},
                        {},
                    ),
                ],
            ),
        ],
    )
    def test_partial_instance(self, location, appliedSubs, expectedRecords):
        font = makeFeatureVarsFont(
            [
                ([{"wght": (0.20886, 1.0)}], {"uni0024": "uni0024.nostroke"}),
                ([{"cntr": (0.75, 1.0)}], {"uni0041": "uni0061"}),
                (
                    [{"wght": (-1.0, -0.45654), "cntr": (0, 0.25)}],
                    {"uni0061": "uni0041"},
                ),
            ]
        )

        limits = instancer.NormalizedAxisLimits(location)
        instancer.instantiateFeatureVariations(font, limits)

        gsub = font["GSUB"].table
        featureVariations = gsub.FeatureVariations

        assert featureVariations.FeatureVariationCount == len(expectedRecords)

        axisOrder = [
            a.axisTag
            for a in font["fvar"].axes
            if a.axisTag not in location or isinstance(location[a.axisTag], tuple)
        ]
        for i, (expectedConditionSet, expectedSubs) in enumerate(expectedRecords):
            rec = featureVariations.FeatureVariationRecord[i]
            conditionSet = _conditionSetAsDict(rec.ConditionSet, axisOrder)

            assert conditionSet == expectedConditionSet, i

            subsRecord = rec.FeatureTableSubstitution.SubstitutionRecord[0]
            lookupIndices = subsRecord.Feature.LookupListIndex
            substitutions = _getSubstitutions(gsub, lookupIndices)

            assert substitutions == expectedSubs, i

        appliedLookupIndices = gsub.FeatureList.FeatureRecord[0].Feature.LookupListIndex

        assert _getSubstitutions(gsub, appliedLookupIndices) == appliedSubs

    @pytest.mark.parametrize(
        "location, appliedSubs",
        [
            ({"wght": 0, "cntr": 0}, None),
            ({"wght": -1.0, "cntr": 0}, {"uni0061": "uni0041"}),
            ({"wght": 1.0, "cntr": 0}, {"uni0024": "uni0024.nostroke"}),
            ({"wght": 0.0, "cntr": 1.0}, {"uni0041": "uni0061"}),
            (
                {"wght": 1.0, "cntr": 1.0},
                {"uni0041": "uni0061", "uni0024": "uni0024.nostroke"},
            ),
            ({"wght": -1.0, "cntr": 0.3}, None),
        ],
    )
    def test_full_instance(self, location, appliedSubs):
        font = makeFeatureVarsFont(
            [
                ([{"wght": (0.20886, 1.0)}], {"uni0024": "uni0024.nostroke"}),
                ([{"cntr": (0.75, 1.0)}], {"uni0041": "uni0061"}),
                (
                    [{"wght": (-1.0, -0.45654), "cntr": (0, 0.25)}],
                    {"uni0061": "uni0041"},
                ),
            ]
        )
        gsub = font["GSUB"].table
        assert gsub.FeatureVariations
        assert gsub.Version == 0x00010001

        location = instancer.NormalizedAxisLimits(location)

        instancer.instantiateFeatureVariations(font, location)

        assert not hasattr(gsub, "FeatureVariations")
        assert gsub.Version == 0x00010000

        if appliedSubs:
            lookupIndices = gsub.FeatureList.FeatureRecord[0].Feature.LookupListIndex
            assert _getSubstitutions(gsub, lookupIndices) == appliedSubs
        else:
            assert not gsub.FeatureList.FeatureRecord

    def test_null_conditionset(self):
        # A null ConditionSet offset should be treated like an empty ConditionTable, i.e.
        # all contexts are matched; see https://github.com/fonttools/fonttools/issues/3211
        font = makeFeatureVarsFont(
            [([{"wght": (-1.0, 1.0)}], {"uni0024": "uni0024.nostroke"})]
        )
        gsub = font["GSUB"].table
        gsub.FeatureVariations.FeatureVariationRecord[0].ConditionSet = None

        location = instancer.NormalizedAxisLimits({"wght": 0.5})
        instancer.instantiateFeatureVariations(font, location)

        assert not hasattr(gsub, "FeatureVariations")
        assert gsub.Version == 0x00010000

        lookupIndices = gsub.FeatureList.FeatureRecord[0].Feature.LookupListIndex
        assert _getSubstitutions(gsub, lookupIndices) == {"uni0024": "uni0024.nostroke"}

    def test_unsupported_condition_format(self, caplog):
        font = makeFeatureVarsFont(
            [
                (
                    [{"wdth": (-1.0, -0.5), "wght": (0.5, 1.0)}],
                    {"dollar": "dollar.nostroke"},
                )
            ]
        )
        featureVariations = font["GSUB"].table.FeatureVariations
        rec1 = featureVariations.FeatureVariationRecord[0]
        assert len(rec1.ConditionSet.ConditionTable) == 2
        rec1.ConditionSet.ConditionTable[0].Format = 2

        with caplog.at_level(logging.WARNING, logger="fontTools.varLib.instancer"):
            instancer.instantiateFeatureVariations(
                font, instancer.NormalizedAxisLimits(wdth=0)
            )

        assert (
            "Condition table 0 of FeatureVariationRecord 0 "
            "has unsupported format (2); ignored"
        ) in caplog.text

        # check that record with unsupported condition format (but whose other
        # conditions do not reference pinned axes) is kept as is
        featureVariations = font["GSUB"].table.FeatureVariations
        assert featureVariations.FeatureVariationRecord[0] is rec1
        assert len(rec1.ConditionSet.ConditionTable) == 2
        assert rec1.ConditionSet.ConditionTable[0].Format == 2

    def test_GSUB_FeatureVariations_is_None(self, varfont2):
        varfont2["GSUB"].table.Version = 0x00010001
        varfont2["GSUB"].table.FeatureVariations = None
        tmp = BytesIO()
        varfont2.save(tmp)
        varfont = ttLib.TTFont(tmp)

        # DO NOT raise an exception when the optional 'FeatureVariations' attribute is
        # present but is set to None (e.g. with GSUB 1.1); skip and do nothing.
        assert varfont["GSUB"].table.FeatureVariations is None
        instancer.instantiateFeatureVariations(varfont, {"wght": 400, "wdth": 100})
        assert varfont["GSUB"].table.FeatureVariations is None


class LimitTupleVariationAxisRangesTest:
    def check_limit_single_var_axis_range(self, var, axisTag, axisRange, expected):
        result = instancer.changeTupleVariationAxisLimit(var, axisTag, axisRange)
        print(result)

        assert len(result) == len(expected)
        for v1, v2 in zip(result, expected):
            assert v1.coordinates == pytest.approx(v2.coordinates)
            assert v1.axes.keys() == v2.axes.keys()
            for k in v1.axes:
                p, q = v1.axes[k], v2.axes[k]
                assert p == pytest.approx(q)

    @pytest.mark.parametrize(
        "var, axisTag, newMax, expected",
        [
            (
                TupleVariation({"wght": (0.0, 1.0, 1.0)}, [100, 100]),
                "wdth",
                0.5,
                [TupleVariation({"wght": (0.0, 1.0, 1.0)}, [100, 100])],
            ),
            (
                TupleVariation({"wght": (0.0, 1.0, 1.0)}, [100, 100]),
                "wght",
                0.5,
                [TupleVariation({"wght": (0.0, 1.0, 1.0)}, [50, 50])],
            ),
            (
                TupleVariation({"wght": (0.0, 1.0, 1.0)}, [100, 100]),
                "wght",
                0.8,
                [TupleVariation({"wght": (0.0, 1.0, 1.0)}, [80, 80])],
            ),
            (
                TupleVariation({"wght": (0.0, 1.0, 1.0)}, [100, 100]),
                "wght",
                1.0,
                [TupleVariation({"wght": (0.0, 1.0, 1.0)}, [100, 100])],
            ),
            (TupleVariation({"wght": (0.0, 1.0, 1.0)}, [100, 100]), "wght", 0.0, []),
            (TupleVariation({"wght": (0.5, 1.0, 1.0)}, [100, 100]), "wght", 0.4, []),
            (
                TupleVariation({"wght": (0.0, 0.5, 1.0)}, [100, 100]),
                "wght",
                0.5,
                [TupleVariation({"wght": (0.0, 1.0, 1.0)}, [100, 100])],
            ),
            (
                TupleVariation({"wght": (0.0, 0.5, 1.0)}, [100, 100]),
                "wght",
                0.4,
                [TupleVariation({"wght": (0.0, 1.0, 1.0)}, [80, 80])],
            ),
            (
                TupleVariation({"wght": (0.0, 0.5, 1.0)}, [100, 100]),
                "wght",
                0.6,
                [TupleVariation({"wght": (0.0, 0.833334, 1.666667)}, [100, 100])],
            ),
            (
                TupleVariation({"wght": (0.0, 0.2, 1.0)}, [100, 100]),
                "wght",
                0.4,
                [
                    TupleVariation({"wght": (0.0, 0.5, 1.0)}, [100, 100]),
                    TupleVariation({"wght": (0.5, 1.0, 1.0)}, [75, 75]),
                ],
            ),
            (
                TupleVariation({"wght": (0.0, 0.2, 1.0)}, [100, 100]),
                "wght",
                0.5,
                [TupleVariation({"wght": (0.0, 0.4, 1.99994)}, [100, 100])],
            ),
            (
                TupleVariation({"wght": (0.5, 0.5, 1.0)}, [100, 100]),
                "wght",
                0.5,
                [TupleVariation({"wght": (1.0, 1.0, 1.0)}, [100, 100])],
            ),
        ],
    )
    def test_positive_var(self, var, axisTag, newMax, expected):
        axisRange = instancer.NormalizedAxisTripleAndDistances(0, 0, newMax)
        self.check_limit_single_var_axis_range(var, axisTag, axisRange, expected)

    @pytest.mark.parametrize(
        "var, axisTag, newMin, expected",
        [
            (
                TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [100, 100]),
                "wdth",
                -0.5,
                [TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [100, 100])],
            ),
            (
                TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [100, 100]),
                "wght",
                -0.5,
                [TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [50, 50])],
            ),
            (
                TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [100, 100]),
                "wght",
                -0.8,
                [TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [80, 80])],
            ),
            (
                TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [100, 100]),
                "wght",
                -1.0,
                [TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [100, 100])],
            ),
            (TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [100, 100]), "wght", 0.0, []),
            (
                TupleVariation({"wght": (-1.0, -1.0, -0.5)}, [100, 100]),
                "wght",
                -0.4,
                [],
            ),
            (
                TupleVariation({"wght": (-1.0, -0.5, 0.0)}, [100, 100]),
                "wght",
                -0.5,
                [TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [100, 100])],
            ),
            (
                TupleVariation({"wght": (-1.0, -0.5, 0.0)}, [100, 100]),
                "wght",
                -0.4,
                [TupleVariation({"wght": (-1.0, -1.0, 0.0)}, [80, 80])],
            ),
            (
                TupleVariation({"wght": (-1.0, -0.5, 0.0)}, [100, 100]),
                "wght",
                -0.6,
                [TupleVariation({"wght": (-1.666667, -0.833334, 0.0)}, [100, 100])],
            ),
            (
                TupleVariation({"wght": (-1.0, -0.2, 0.0)}, [100, 100]),
                "wght",
                -0.4,
                [
                    TupleVariation({"wght": (-1.0, -0.5, -0.0)}, [100, 100]),
                    TupleVariation({"wght": (-1.0, -1.0, -0.5)}, [75, 75]),
                ],
            ),
            (
                TupleVariation({"wght": (-1.0, -0.2, 0.0)}, [100, 100]),
                "wght",
                -0.5,
                [TupleVariation({"wght": (-2.0, -0.4, 0.0)}, [100, 100])],
            ),
            (
                TupleVariation({"wght": (-1.0, -0.5, -0.5)}, [100, 100]),
                "wght",
                -0.5,
                [TupleVariation({"wght": (-1.0, -1.0, -1.0)}, [100, 100])],
            ),
        ],
    )
    def test_negative_var(self, var, axisTag, newMin, expected):
        axisRange = instancer.NormalizedAxisTripleAndDistances(newMin, 0, 0, 1, 1)
        self.check_limit_single_var_axis_range(var, axisTag, axisRange, expected)


@pytest.mark.parametrize(
    "oldRange, newLimit, expected",
    [
        ((1.0, -1.0), (-1.0, 0, 1.0), None),  # invalid oldRange min > max
        ((0.6, 1.0), (0, 0, 0.5), None),
        ((-1.0, -0.6), (-0.5, 0, 0), None),
        ((0.4, 1.0), (0, 0, 0.5), (0.8, 1.0)),
        ((-1.0, -0.4), (-0.5, 0, 0), (-1.0, -0.8)),
        ((0.4, 1.0), (0, 0, 0.4), (1.0, 1.0)),
        ((-1.0, -0.4), (-0.4, 0, 0), (-1.0, -1.0)),
        ((-0.5, 0.5), (-0.4, 0, 0.4), (-1.0, 1.0)),
        ((0, 1.0), (-1.0, 0, 0), (0, 0)),  # or None?
        ((-1.0, 0), (0, 0, 1.0), (0, 0)),  # or None?
    ],
)
def test_limitFeatureVariationConditionRange(oldRange, newLimit, expected):
    condition = featureVars.buildConditionTable(0, *oldRange)

    result = instancer.featureVars._limitFeatureVariationConditionRange(
        condition, instancer.NormalizedAxisTripleAndDistances(*newLimit, 1, 1)
    )

    assert result == expected


@pytest.mark.parametrize(
    "limits, expected",
    [
        (["wght=400", "wdth=100"], {"wght": 400, "wdth": 100}),
        (["wght=400:900"], {"wght": (400, 900)}),
        (["wght=400:700:900"], {"wght": (400, 700, 900)}),
        (["slnt=11.4"], {"slnt": 11.399994}),
        (["ABCD=drop"], {"ABCD": None}),
        (["wght=:500:"], {"wght": (None, 500, None)}),
        (["wght=::700"], {"wght": (None, None, 700)}),
        (["wght=200::"], {"wght": (200, None, None)}),
        (["wght=200:300:"], {"wght": (200, 300, None)}),
        (["wght=:300:500"], {"wght": (None, 300, 500)}),
        (["wght=300::700"], {"wght": (300, None, 700)}),
        (["wght=300:700"], {"wght": (300, None, 700)}),
        (["wght=:700"], {"wght": (None, None, 700)}),
        (["wght=200:"], {"wght": (200, None, None)}),
    ],
)
def test_parseLimits(limits, expected):
    limits = instancer.parseLimits(limits)
    expected = instancer.AxisLimits(expected)

    assert limits.keys() == expected.keys()
    for axis, triple in limits.items():
        expected_triple = expected[axis]
        if expected_triple is None:
            assert triple is None
        else:
            assert isinstance(triple, instancer.AxisTriple)
            assert isinstance(expected_triple, instancer.AxisTriple)
            assert triple == pytest.approx(expected_triple)


@pytest.mark.parametrize(
    "limits", [["abcde=123", "=0", "wght=:", "wght=1:", "wght=abcd", "wght=x:y"]]
)
def test_parseLimits_invalid(limits):
    with pytest.raises(ValueError, match="invalid location format"):
        instancer.parseLimits(limits)


@pytest.mark.parametrize(
    "limits, expected",
    [
        # 300, 500 come from the font having 100,400,900 fvar axis limits.
        ({"wght": (100, 400)}, {"wght": (-1.0, 0, 0, 300, 500)}),
        ({"wght": (100, 400, 400)}, {"wght": (-1.0, 0, 0, 300, 500)}),
        ({"wght": (100, 300, 400)}, {"wght": (-1.0, -0.5, 0, 300, 500)}),
    ],
)
def test_normalizeAxisLimits(varfont, limits, expected):
    limits = instancer.AxisLimits(limits)

    normalized = limits.normalize(varfont)

    assert normalized == instancer.NormalizedAxisLimits(expected)


def test_normalizeAxisLimits_no_avar(varfont):
    del varfont["avar"]

    limits = instancer.AxisLimits(wght=(400, 400, 500))
    normalized = limits.normalize(varfont)

    assert normalized["wght"] == pytest.approx((0, 0, 0.2, 300, 500), 1e-4)


def test_normalizeAxisLimits_missing_from_fvar(varfont):
    with pytest.raises(ValueError, match="not present in fvar"):
        instancer.AxisLimits({"ZZZZ": 1000}).normalize(varfont)


def test_sanityCheckVariableTables(varfont):
    font = ttLib.TTFont()
    with pytest.raises(ValueError, match="Missing required table fvar"):
        instancer.sanityCheckVariableTables(font)

    del varfont["glyf"]

    with pytest.raises(ValueError, match="Can't have gvar without glyf"):
        instancer.sanityCheckVariableTables(varfont)


def test_main(varfont, tmpdir):
    fontfile = str(tmpdir / "PartialInstancerTest-VF.ttf")
    varfont.save(fontfile)
    args = [fontfile, "wght=400"]

    # exits without errors
    assert instancer.main(args) is None


def test_main_exit_nonexistent_file(capsys):
    with pytest.raises(SystemExit):
        instancer.main([""])
    captured = capsys.readouterr()

    assert "No such file ''" in captured.err


def test_main_exit_invalid_location(varfont, tmpdir, capsys):
    fontfile = str(tmpdir / "PartialInstancerTest-VF.ttf")
    varfont.save(fontfile)

    with pytest.raises(SystemExit):
        instancer.main([fontfile, "wght:100"])
    captured = capsys.readouterr()

    assert "invalid location format" in captured.err


def test_main_exit_multiple_limits(varfont, tmpdir, capsys):
    fontfile = str(tmpdir / "PartialInstancerTest-VF.ttf")
    varfont.save(fontfile)

    with pytest.raises(SystemExit):
        instancer.main([fontfile, "wght=400", "wght=90"])
    captured = capsys.readouterr()

    assert "Specified multiple limits for the same axis" in captured.err


def test_set_ribbi_bits():
    varfont = ttLib.TTFont()
    varfont.importXML(os.path.join(TESTDATA, "STATInstancerTest.ttx"))

    for location in [instance.coordinates for instance in varfont["fvar"].instances]:
        instance = instancer.instantiateVariableFont(
            varfont, location, updateFontNames=True
        )
        name_id_2 = instance["name"].getDebugName(2)
        mac_style = instance["head"].macStyle
        fs_selection = instance["OS/2"].fsSelection & 0b1100001  # Just bits 0, 5, 6

        if location["ital"] == 0:
            if location["wght"] == 700:
                assert name_id_2 == "Bold", location
                assert mac_style == 0b01, location
                assert fs_selection == 0b0100000, location
            else:
                assert name_id_2 == "Regular", location
                assert mac_style == 0b00, location
                assert fs_selection == 0b1000000, location
        else:
            if location["wght"] == 700:
                assert name_id_2 == "Bold Italic", location
                assert mac_style == 0b11, location
                assert fs_selection == 0b0100001, location
            else:
                assert name_id_2 == "Italic", location
                assert mac_style == 0b10, location
                assert fs_selection == 0b0000001, location
