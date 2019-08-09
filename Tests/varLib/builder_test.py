from fontTools.varLib.builder import buildVarData
import pytest


@pytest.mark.parametrize("region_indices, items, expected_num_shorts", [
    ([], [], 0),
    ([0], [[1]], 0),
    ([0], [[128]], 1),
    ([0, 1, 2], [[128, 1, 2], [3, -129, 5], [6, 7, 8]], 2),
    ([0, 1, 2], [[0, 128, 2], [3, 4, 5], [6, 7, -129]], 3),
], ids=[
    "0_regions_0_deltas",
    "1_region_1_uint8",
    "1_region_1_short",
    "3_regions_2_shorts_ordered",
    "3_regions_2_shorts_unordered",
])
def test_buildVarData_no_optimize(region_indices, items, expected_num_shorts):
    data = buildVarData(region_indices, items, optimize=False)

    assert data.ItemCount == len(items)
    assert data.NumShorts == expected_num_shorts
    assert data.VarRegionCount == len(region_indices)
    assert data.VarRegionIndex == region_indices
    assert data.Item == items


@pytest.mark.parametrize([
    "region_indices", "items", "expected_num_shorts",
    "expected_regions", "expected_items"
], [
    ([0, 1, 2], [[0, 1, 2], [3, 4, 5], [6, 7, 8]], 0,
     [0, 1, 2], [[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
    ([0, 1, 2], [[0, 128, 2], [3, 4, 5], [6, 7, 8]], 1,
     [1, 0, 2], [[128, 0, 2], [4, 3, 5], [7, 6, 8]]),
    ([0, 1, 2], [[0, 1, 128], [3, 4, 5], [6, -129, 8]], 2,
     [1, 2, 0], [[1, 128, 0], [4, 5, 3], [-129, 8, 6]]),
    ([0, 1, 2], [[128, 1, -129], [3, 4, 5], [6, 7, 8]], 2,
     [0, 2, 1], [[128, -129, 1], [3, 5, 4], [6, 8, 7]]),
    ([0, 1, 2], [[0, 1, 128], [3, -129, 5], [256, 7, 8]], 3,
     [0, 1, 2], [[0, 1, 128], [3, -129, 5], [256, 7, 8]]),
    ([0, 1, 2], [[0, 128, 2], [0, 4, 5], [0, 7, 8]], 1,
     [1, 2], [[128, 2], [4, 5], [7, 8]]),
], ids=[
    "0/3_shorts_no_reorder",
    "1/3_shorts_reorder",
    "2/3_shorts_reorder",
    "2/3_shorts_same_row_reorder",
    "3/3_shorts_no_reorder",
    "1/3_shorts_1/3_zeroes",
])
def test_buildVarData_optimize(
        region_indices, items, expected_num_shorts, expected_regions,
        expected_items):
    data = buildVarData(region_indices, items, optimize=True)

    assert data.ItemCount == len(items)
    assert data.NumShorts == expected_num_shorts
    assert data.VarRegionCount == len(expected_regions)
    assert data.VarRegionIndex == expected_regions
    assert data.Item == expected_items


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(sys.argv))
