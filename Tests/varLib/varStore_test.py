import itertools
import pytest
import random
from io import StringIO
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.misc.roundTools import noRound, otRound
from fontTools.varLib.builder import (
    buildVarRegionList,
    buildVarData,
    buildVarStore,
)
from fontTools.varLib.models import VariationModel, supportScalar
from fontTools.varLib.varStore import OnlineVarStoreBuilder, VarStoreInstancer
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter
from fontTools.ttLib.tables.otTables import VarStore


@pytest.mark.parametrize(
    "locations, masterValues",
    [
        (
            [{}, {"a": 1}],
            [
                [10, 10],  # Test NO_VARIATION_INDEX
                [100, 2000],
                [100, 22000],
            ],
        ),
        (
            [{}, {"a": 1}, {"b": 1}, {"a": 1, "b": 1}],
            [
                [10, 20, 40, 60],
                [100, 2000, 400, 6000],
                [7100, 22000, 4000, 30000],
            ],
        ),
        (
            [{}, {"a": 1}],
            [
                [10, 20],
                [42000, 100],
                [100, 52000],
            ],
        ),
        (
            [{}, {"a": 1}, {"b": 1}, {"a": 1, "b": 1}],
            [
                [10, 20, 40, 60],
                [40000, 42000, 400, 6000],
                [100, 22000, 4000, 173000],
            ],
        ),
        (
            [{}, {"a": 1}, {"b": 1}, {"a": 1, "b": 1}],
            [
                [random.randint(-128, 127) for _ in range(4)],
                [random.randint(-128, 127) for _ in range(4)],
                [random.randint(-128, 127) for _ in range(4)],
                [random.randint(-32768, 32767) for _ in range(4)],
                [random.randint(-32768, 32767) for _ in range(4)],
                [random.randint(-32768, 32767) for _ in range(4)],
            ],
        ),
    ],
)
def test_onlineVarStoreBuilder(locations, masterValues):
    axisTags = sorted({k for loc in locations for k in loc})
    model = VariationModel(locations)
    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)
    varIdxs = []
    # shuffle input order to ensure optimizer produces stable results
    random.shuffle(masterValues)
    for masters in masterValues:
        _, varIdx = builder.storeMasters(masters)
        varIdxs.append(varIdx)

    varStore = builder.finish()
    mapping = varStore.optimize()
    varIdxs = [mapping[varIdx] for varIdx in varIdxs]

    dummyFont = TTFont()
    writer = OTTableWriter()
    varStore.compile(writer, dummyFont)
    data = writer.getAllData()
    reader = OTTableReader(data)
    varStore = VarStore()
    varStore.decompile(reader, dummyFont)

    fvarAxes = [buildAxis(axisTag) for axisTag in axisTags]
    instancer = VarStoreInstancer(varStore, fvarAxes)
    for masters, varIdx in zip(masterValues, varIdxs):
        base, *rest = masters
        for expectedValue, loc in zip(masters, locations):
            instancer.setLocation(loc)
            value = base + instancer[varIdx]
            assert expectedValue == value


def buildAxis(axisTag):
    axis = Axis()
    axis.axisTag = axisTag
    return axis


def test_VarStoreInstancer_out_of_range_index_returns_zero():
    varData = buildVarData([], [[]], optimize=False)
    varStore = buildVarStore(buildVarRegionList([], ["wght"]), [varData])
    instancer = VarStoreInstancer(varStore, [buildAxis("wght")])

    assert instancer[0] == 0
    assert instancer[1] == 0  # inner index beyond the single item
    assert instancer[1 << 16] == 0  # outer index beyond the single VarData


@pytest.mark.parametrize(
    "numRegions, varData, expectedNumVarData, expectedBytes",
    [
        (
            5,
            [
                [10, 10, 0, 0, 20],
                {3: 300},
            ],
            1,
            126,
        ),
        (
            5,
            [
                [10, 10, 0, 0, 20],
                [10, 11, 0, 0, 20],
                [10, 12, 0, 0, 20],
                [10, 13, 0, 0, 20],
                {3: 300},
            ],
            1,
            175,
        ),
        (
            5,
            [
                [10, 11, 0, 0, 20],
                [10, 300, 0, 0, 20],
                [10, 301, 0, 0, 20],
                [10, 302, 0, 0, 20],
                [10, 303, 0, 0, 20],
                [10, 304, 0, 0, 20],
            ],
            1,
            180,
        ),
        (
            5,
            [
                [0, 11, 12, 0, 20],
                [0, 13, 12, 0, 20],
                [0, 14, 12, 0, 20],
                [0, 15, 12, 0, 20],
                [0, 16, 12, 0, 20],
                [10, 300, 0, 0, 20],
                [10, 301, 0, 0, 20],
                [10, 302, 0, 0, 20],
                [10, 303, 0, 0, 20],
                [10, 304, 0, 0, 20],
            ],
            1,
            200,
        ),
        (
            5,
            [
                [0, 11, 12, 0, 20],
                [0, 13, 12, 0, 20],
                [0, 14, 12, 0, 20],
                [0, 15, 12, 0, 20],
                [0, 16, 12, 0, 20],
                [0, 17, 12, 0, 20],
                [0, 18, 12, 0, 20],
                [0, 19, 12, 0, 20],
                [0, 20, 12, 0, 20],
                [10, 300, 0, 0, 20],
                [10, 301, 0, 0, 20],
                [10, 302, 0, 0, 20],
                [10, 303, 0, 0, 20],
                [10, 304, 0, 0, 20],
            ],
            2,
            218,
        ),
        (
            3,
            [
                [10, 10, 10],
            ],
            0,
            12,
        ),
    ],
)
def test_optimize(numRegions, varData, expectedNumVarData, expectedBytes):
    locations = [{i: i / 16384.0} for i in range(numRegions)]
    axisTags = sorted({k for loc in locations for k in loc})

    model = VariationModel(locations)
    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)

    random.shuffle(varData)
    for data in varData:
        if type(data) is dict:
            newData = [0] * numRegions
            for k, v in data.items():
                newData[k] = v
            data = newData

        builder.storeMasters(data)

    varStore = builder.finish()
    varStore.optimize()

    dummyFont = TTFont()

    writer = XMLWriter(StringIO())
    varStore.toXML(writer, dummyFont)
    xml = writer.file.getvalue()

    assert len(varStore.VarData) == expectedNumVarData, xml

    writer = OTTableWriter()
    varStore.compile(writer, dummyFont)
    data = writer.getAllData()

    assert len(data) == expectedBytes, xml


@pytest.mark.parametrize(
    "quantization, expectedBytes",
    [
        (1, 200),
        (2, 180),
        (3, 170),
        (4, 175),
        (8, 170),
        (32, 92),
        (64, 56),
    ],
)
def test_quantize(quantization, expectedBytes):
    varData = [
        [0, 11, 12, 0, 20],
        [0, 13, 12, 0, 20],
        [0, 14, 12, 0, 20],
        [0, 15, 12, 0, 20],
        [0, 16, 12, 0, 20],
        [10, 300, 0, 0, 20],
        [10, 301, 0, 0, 20],
        [10, 302, 0, 0, 20],
        [10, 303, 0, 0, 20],
        [10, 304, 0, 0, 20],
    ]

    numRegions = 5
    locations = [{i: i / 16384.0} for i in range(numRegions)]
    axisTags = sorted({k for loc in locations for k in loc})

    model = VariationModel(locations)

    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)

    random.shuffle(varData)
    for data in varData:
        builder.storeMasters(data)

    varStore = builder.finish()
    varStore.optimize(quantization=quantization)

    dummyFont = TTFont()

    writer = XMLWriter(StringIO())
    varStore.toXML(writer, dummyFont)
    xml = writer.file.getvalue()

    writer = OTTableWriter()
    varStore.compile(writer, dummyFont)
    data = writer.getAllData()

    assert len(data) == expectedBytes, xml


def test_optimize_overflow():
    numRegions = 1
    locations = [{"wght": 0}, {"wght": 0.5}]
    axisTags = ["wght"]

    model = VariationModel(locations)
    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)

    varData = list(range(0, 0xFFFF * 2))
    random.shuffle(varData)
    for data in varData:
        data = [0, data]
        builder.storeMasters(data, round=noRound)

    varStore = builder.finish()
    varStore.optimize()

    for s in varStore.VarData:
        print(len(s.Item))

    # 5 data-sets:
    # - 0..127: 1-byte dataset
    # - 128..32767: 2-byte dataset
    # - 32768..32768+65535-1: 4-byte dataset
    # - 32768+65535..65535+65535-1: 4-byte dataset
    assert len(varStore.VarData) == 4


class GetExtremesTest:
    """VarStore.getExtremes must be CONSERVATIVE: the interval it returns
    must cover the truly reachable range of the store's output, because the
    avar2 instancer uses it to delete "unreachable" variation regions. An
    under-wide bound silently corrupts instanced fonts.

    For two-sided tents the output is piecewise multilinear, so its exact
    extremes are attained on the grid of per-axis tent breakpoints. A one-sided
    tent (start == peak or peak == end) is discontinuous at its peak, however,
    so the ground-truth grid must also include the adjacent F2Dot14 point on the
    open side.
    """

    @staticmethod
    def _buildStore(regions, deltas, axisTags):
        regionList = buildVarRegionList(regions, axisTags)
        varData = buildVarData(list(range(len(regions))), [deltas], optimize=False)
        return buildVarStore(regionList, [varData])

    @staticmethod
    def _makeAxes(axisTags):
        axes = []
        for tag in axisTags:
            axis = Axis()
            axis.axisTag = tag
            axes.append(axis)
        return axes

    @classmethod
    def _trueExtremes(cls, regions, deltas, axisTags, axisLimits, identityAxisIndex):
        breakpoints = {tag: {-1.0, 0.0, 1.0} for tag in axisTags}
        unit = 1 / 16384
        for region in regions:
            for tag, (start, peak, end) in region.items():
                breakpoints[tag].update((start, peak, end))
                if start == peak:
                    breakpoints[tag].add(peak - unit)
                if peak == end:
                    breakpoints[tag].add(peak + unit)
        for tag in axisTags:
            lo, hi = (-1.0, 1.0)
            if tag in axisLimits:
                lo, hi = axisLimits[tag][0], axisLimits[tag][2]
            breakpoints[tag] = {min(max(v, lo), hi) for v in breakpoints[tag]}
            breakpoints[tag].update((lo, hi))
        lo = hi = None
        for combo in itertools.product(*(sorted(breakpoints[tag]) for tag in axisTags)):
            location = dict(zip(axisTags, combo))
            value = otRound(
                sum(
                    supportScalar(location, region) * delta
                    for region, delta in zip(regions, deltas)
                )
            )
            if identityAxisIndex is not None:
                value += otRound(location[axisTags[identityAxisIndex]] * 16384)
            lo = value if lo is None else min(lo, value)
            hi = value if hi is None else max(hi, value)
        return lo, hi

    @classmethod
    def _check(cls, regions, deltas, axisTags, axisLimits, identityAxisIndex):
        store = cls._buildStore(regions, deltas, axisTags)
        boundLo, boundHi = store.getExtremes(
            0, cls._makeAxes(axisTags), axisLimits, identityAxisIndex
        )
        trueLo, trueHi = cls._trueExtremes(
            regions, deltas, axisTags, axisLimits, identityAxisIndex
        )
        assert boundLo <= trueLo + 1e-9 and boundHi >= trueHi - 1e-9, (
            f"getExtremes ({boundLo}, {boundHi}) does not cover true range "
            f"({trueLo}, {trueHi}) for regions={regions} deltas={deltas} "
            f"axisLimits={axisLimits} identityAxisIndex={identityAxisIndex}"
        )
        return (boundLo, boundHi), (trueLo, trueHi)

    def test_overlapping_same_axis_tents(self):
        # The peak-sampling implementation this replaced missed the extremum
        # of overlapping same-axis tents (it lies at another tent's start/end
        # kink, not at any peak) and returned max=0 here — culling then
        # deleted live gvar regions around wght=0.6.
        bound, true = self._check(
            [{"wght": (0.0, 0.4, 0.6)}, {"wght": (0.2, 0.5, 0.8)}],
            [-16384, 8192],
            ["wght"],
            {},
            None,
        )
        # Small stores take the exact (breakpoint-grid) path.
        assert bound == pytest.approx(true)

    def test_one_sided_support_extreme(self):
        # A peak=end tent contributes at the peak, then drops to zero at the
        # next F2Dot14 coordinate. The breakpoint-only grid sees the two rows
        # cancel at 0.25 and misses the live second row immediately to its
        # right, so the returned upper bound must also cover that grid point.
        regions = [
            {"wght": (0.0, 0.25, 0.25)},
            {"wght": (0.0, 0.25, 0.5)},
        ]
        deltas = [-16384, 16384]
        store = self._buildStore(regions, deltas, ["wght"])

        _, boundHi = store.getExtremes(0, self._makeAxes(["wght"]), {}, None)
        location = {"wght": 4097 / 16384}
        reachable = sum(
            supportScalar(location, region) * delta
            for region, delta in zip(regions, deltas)
        )
        _, trueHi = self._trueExtremes(regions, deltas, ["wght"], {}, None)

        assert reachable == 16380
        assert trueHi == reachable
        assert boundHi >= reachable

    def test_identity_axis(self):
        self._check(
            [{"wght": (0.0, 0.5, 1.0)}, {"wght": (-1.0, -0.5, 0.0)}],
            [8000, -4000],
            ["wght"],
            {},
            0,
        )

    def test_pinned_axis_limits(self):
        self._check(
            [{"wght": (0.0, 0.5, 1.0), "opsz": (0.0, 1.0, 1.0)}],
            [10000],
            ["wght", "opsz"],
            {"opsz": (0, 0, 0)},
            None,
        )

    def test_conservative_random(self):
        rng = random.Random(1234)
        for _ in range(300):
            nAxes = rng.randint(1, 3)
            axisTags = ["ax%d" % i for i in range(nAxes)]
            regions = []
            deltas = []
            for _ in range(rng.randint(1, 5)):
                region = {}
                for tag in axisTags:
                    if rng.random() < 0.6:
                        # OT-valid tent on one side of 0
                        if rng.random() < 0.5:
                            coords = sorted(
                                round(rng.uniform(0, 1), 2) for _ in range(3)
                            )
                        else:
                            coords = sorted(
                                round(rng.uniform(-1, 0), 2) for _ in range(3)
                            )
                        if coords[1] != 0:
                            region[tag] = tuple(coords)
                regions.append(region)
                deltas.append(rng.randint(-16384, 16384))
            axisLimits = {}
            for tag in axisTags:
                r = rng.random()
                if r < 0.25:
                    axisLimits[tag] = (0, 0, 0)  # pinned private axis
                elif r < 0.4:
                    axisLimits[tag] = (
                        round(rng.uniform(-1, 0), 2),
                        0,
                        round(rng.uniform(0, 1), 2),
                    )
            identityAxisIndex = rng.choice([None] + list(range(nAxes)))
            self._check(regions, deltas, axisTags, axisLimits, identityAxisIndex)

    def test_many_axes_falls_back_fast(self):
        # A row peaking on many distinct axes explodes the breakpoint grid;
        # getExtremes must fall back to the O(regions x axes) interval bound
        # instead of hanging (the recursion it replaced was exponential).
        # The fallback is looser but still conservative.
        k = 30
        axisTags = ["a%02d" % i for i in range(k)]
        regions = [{tag: (0.0, 0.5, 1.0)} for tag in axisTags]
        deltas = [1000] * k
        store = self._buildStore(regions, deltas, axisTags)
        boundLo, boundHi = store.getExtremes(0, self._makeAxes(axisTags), {}, None)
        assert boundLo <= 0 and boundHi >= k * 1000  # all peaks reachable at once
