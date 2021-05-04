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
                [177100, 22000, 4000, 30000],
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
    ],
)
def test_onlineVarStoreBuilder(locations, masterValues):
    axisTags = sorted({k for loc in locations for k in loc})
    model = VariationModel(locations)
    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)
    varIdxs = []
    for masters in masterValues:
        _, varIdx = builder.storeMasters(masters)
        varIdxs.append(varIdx)

    varStore = builder.finish()
    mapping = varStore.optimize()
    varIdxs = [mapping[varIdx] for varIdx in varIdxs]

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
