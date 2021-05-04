import pytest
from fontTools.varLib.models import VariationModel
from fontTools.varLib.varStore import OnlineVarStoreBuilder, VarStoreInstancer
from fontTools.ttLib.tables._f_v_a_r import Axis


@pytest.mark.parametrize(
    "locations, masterValues",
    [
        (
            [{}, {"a": 1}],
            [
                [10, 20],
                [100, 2000],
                [100, 22000],
            ],
        ),
        (
            [{}, {"a": 1}, {"b": 1}, {"a": 1, "b": 1}],
            [
                [10, 20, 40, 60],
                [100, 2000, 400, 6000],
                [100, 22000, 4000, 30000],
            ],
        ),
    ],
)
def test_onlineVarStoreBuilder(locations, masterValues):
    axisTags = sorted({k for loc in locations for k in loc})
    model = VariationModel(locations)
    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)
    expectedDeltasAndVarIdxs = []
    for masters in masterValues:
        base, *deltas = model.getDeltas(masters)
        varIdx = builder.storeDeltas(deltas)
        expectedDeltasAndVarIdxs.append((deltas, varIdx))

    varStore = builder.finish()
    varData = varStore.VarData

    for deltas, varIdx in expectedDeltasAndVarIdxs:
        major, minor = varIdx >> 16, varIdx & 0xFFFF
        storedDeltas = varData[major].Item[minor]
        assert deltas == storedDeltas

    fvarAxes = [buildAxis(axisTag) for axisTag in axisTags]
    instancer = VarStoreInstancer(varStore, fvarAxes)
    for masters, (deltas, varIdx) in zip(masterValues, expectedDeltasAndVarIdxs):
        base, *rest = masters
        for expectedValue, loc in zip(masters, locations):
            instancer.setLocation(loc)
            value = base + instancer[varIdx]
            assert expectedValue == value


def buildAxis(axisTag):
    axis = Axis()
    axis.axisTag = axisTag
    return axis
