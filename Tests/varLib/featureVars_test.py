from fontTools.varLib.featureVars import overlayFeatureVariations, overlayBox


def _test_linear(n):
    conds = []
    for i in range(n):
        end = i / n
        start = end - 1.0
        region = [{"X": (start, end)}]
        subst = {"g%.2g" % start: "g%.2g" % end}
        conds.append((region, subst))
    overlaps = overlayFeatureVariations(conds)
    assert len(overlaps) == 2 * n - 1, overlaps
    return conds, overlaps


def test_linear():
    _test_linear(10)


def _test_quadratic(n):
    conds = []
    for i in range(1, n + 1):
        region = [{"X": (0, i / n), "Y": (0, (n + 1 - i) / n)}]
        subst = {str(i): str(n + 1 - i)}
        conds.append((region, subst))
    overlaps = overlayFeatureVariations(conds)
    assert len(overlaps) == n * (n + 1) // 2, overlaps
    return conds, overlaps


def test_quadratic():
    _test_quadratic(10)


def _merge_substitutions(substitutions):
    merged = {}
    for subst in substitutions:
        merged.update(subst)
    return merged


def _match_condition(location, overlaps):
    for box, substitutions in overlaps:
        for tag, coord in location.items():
            start, end = box[tag]
            if start <= coord <= end:
                return _merge_substitutions(substitutions)
    return {}  # no match


def test_overlaps_1():
    # https://github.com/fonttools/fonttools/issues/1400
    conds = [
        ([{"abcd": (4, 9)}], {0: 0}),
        ([{"abcd": (5, 10)}], {1: 1}),
        ([{"abcd": (0, 8)}], {2: 2}),
        ([{"abcd": (3, 7)}], {3: 3}),
    ]
    overlaps = overlayFeatureVariations(conds)
    subst = _match_condition({"abcd": 0}, overlaps)
    assert subst == {2: 2}
    subst = _match_condition({"abcd": 1}, overlaps)
    assert subst == {2: 2}
    subst = _match_condition({"abcd": 3}, overlaps)
    assert subst == {2: 2, 3: 3}
    subst = _match_condition({"abcd": 4}, overlaps)
    assert subst == {0: 0, 2: 2, 3: 3}
    subst = _match_condition({"abcd": 5}, overlaps)
    assert subst == {0: 0, 1: 1, 2: 2, 3: 3}
    subst = _match_condition({"abcd": 7}, overlaps)
    assert subst == {0: 0, 1: 1, 2: 2, 3: 3}
    subst = _match_condition({"abcd": 8}, overlaps)
    assert subst == {0: 0, 1: 1, 2: 2}
    subst = _match_condition({"abcd": 9}, overlaps)
    assert subst == {0: 0, 1: 1}
    subst = _match_condition({"abcd": 10}, overlaps)
    assert subst == {1: 1}


def test_overlaps_2():
    # https://github.com/fonttools/fonttools/issues/1400
    conds = [
        ([{"abcd": (1, 9)}], {0: 0}),
        ([{"abcd": (8, 10)}], {1: 1}),
        ([{"abcd": (3, 4)}], {2: 2}),
        ([{"abcd": (1, 10)}], {3: 3}),
    ]
    overlaps = overlayFeatureVariations(conds)
    subst = _match_condition({"abcd": 0}, overlaps)
    assert subst == {}
    subst = _match_condition({"abcd": 1}, overlaps)
    assert subst == {0: 0, 3: 3}
    subst = _match_condition({"abcd": 2}, overlaps)
    assert subst == {0: 0, 3: 3}
    subst = _match_condition({"abcd": 3}, overlaps)
    assert subst == {0: 0, 2: 2, 3: 3}
    subst = _match_condition({"abcd": 5}, overlaps)
    assert subst == {0: 0, 3: 3}
    subst = _match_condition({"abcd": 10}, overlaps)
    assert subst == {1: 1, 3: 3}


def test_overlayBox():
    # https://github.com/fonttools/fonttools/issues/3003
    top = {"opsz": (0.75, 1.0), "wght": (0.5, 1.0)}
    bot = {"wght": (0.25, 1.0)}
    intersection, remainder = overlayBox(top, bot)
    assert intersection == {"opsz": (0.75, 1.0), "wght": (0.5, 1.0)}
    assert remainder == {"wght": (0.25, 1.0)}


def run(test, n, quiet):
    print()
    print("%s:" % test.__name__)
    input, output = test(n)
    if quiet:
        print(len(output))
    else:
        print()
        print("Input:")
        pprint(input)
        print()
        print("Output:")
        pprint(output)
        print()


if __name__ == "__main__":
    import sys
    from pprint import pprint

    quiet = False
    n = 3
    if len(sys.argv) > 1 and sys.argv[1] == "-q":
        quiet = True
        del sys.argv[1]
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    run(_test_linear, n=n, quiet=quiet)
    run(_test_quadratic, n=n, quiet=quiet)
