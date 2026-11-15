from pathlib import Path
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.varLib import builder
from fontTools.varLib.avar.map import map as map_avar, main as map_main
from fontTools.varLib.avar.reverse import _AvarMapping, ReverseMapper, reverse, main
from fontTools.varLib.avar.roundtrip import roundtrip, main as roundtrip_main
from fontTools.varLib.avar import _mapping


def make_font(tags=("aaaa", "bbbb", "cccc"), hidden=(), positive=()):
    font = TTFont()
    font["fvar"] = newTable("fvar")
    for tag in tags:
        axis = Axis()
        axis.axisTag = tag
        axis.minValue = 400 if tag in positive else 100
        axis.defaultValue = 400
        axis.maxValue = 900
        axis.flags = int(tag in hidden)
        axis.axisNameID = 256
        font["fvar"].axes.append(axis)
    return font


def add_avar2(font, supports, deltas):
    tags = [a.axisTag for a in font["fvar"].axes]
    avar = font["avar"] = newTable("avar")
    avar.majorVersion, avar.minorVersion = 2, 0
    avar.segments = {tag: {-1: -1, 0: 0, 1: 1} for tag in tags}
    avar.table = otTables.avar()
    avar.table.VarIdxMap = None
    region_list = builder.buildVarRegionList(supports, tags)
    data = builder.buildVarData(
        range(len(supports)),
        [
            [round(v * 16384) for v in deltas.get(tag, [0] * len(supports))]
            for tag in tags
        ],
    )
    avar.table.VarStore = builder.buildVarStore(region_list, [data])
    return avar


def forward(font, location):
    return map_avar(font, location, outputNormalized=True, dropZeroes=False)


def assert_target(font, result, target, atol=1 / 16384):
    actual = forward(font, result)
    assert np.linalg.norm([v - target.get(tag, 0) for tag, v in actual.items()]) <= atol


def test_packed_evaluator_matches_python():
    font = make_font()
    add_avar2(
        font,
        [
            {},
            {"aaaa": (0, 0.5, 0.5)},
            {"aaaa": (-0.5, -0.5, 0.0), "bbbb": (0, 1, 1)},
            {"aaaa": (0.5, 0.5, 0.5), "bbbb": (0, 0.5, 1), "cccc": (0, 1, 1)},
        ],
        {
            "aaaa": [0.125, 0.25, -0.5, 1],
            "bbbb": [0, -0.5, 0.75, 0],
            "cccc": [0, 0, 0, 1],
        },
    )
    mapping = _AvarMapping(font)
    points = [np.array([v, v, v], dtype=float) for v in (-1, -0.5, 0, 0.5, 1)]
    points.extend(np.random.default_rng(0).uniform(-1, 1, (20, 3)))
    for index, z in enumerate(points):
        slopes = np.array([0.5, 1, 2.0])
        actual = _mapping.evaluate(
            z, slopes, mapping.deltas, *mapping._packed, mapping.supports
        )
        expected = _mapping._evaluatePython(z, slopes, mapping.deltas, mapping.supports)
        for a, b in zip(actual, expected):
            if index < 5:
                np.testing.assert_array_equal(a, b)
            else:
                # Compilers may contract arithmetic on random inputs. Keep
                # exact boundary checks, with a few ULPs allowed elsewhere.
                np.testing.assert_allclose(a, b, rtol=2e-15, atol=2e-15)


def test_packed_segments_match_scalar_mapping():
    from fontTools.varLib.avar.reverse import _segment

    segments = [[], [(0, 0.125)], [(-1, -1), (0, 0), (0.25, 0.5), (0.5, 0.5), (1, 1)]]
    packed = _mapping.packSegments(segments)
    points = [-2, -1, -0.5, 0, 0.25, 0.5, 1, 2]
    points.extend(np.random.default_rng(0).uniform(-2, 2, 100))
    for v in points:
        actual = _mapping.mapSegments(np.full(3, v, dtype=float), *packed, segments)
        expected = np.array([_segment(v, s) for s in segments]).T
        np.testing.assert_allclose(actual, expected, rtol=2e-15, atol=2e-15)


@pytest.mark.parametrize("pinned", [{}, {"bbbb": 650}])
def test_constant_output_error_floor_needs_no_iterations(pinned):
    font = make_font(hidden=("cccc",))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"bbbb": [0.5]})
    solver = ReverseMapper(font, pinned=pinned)

    def forbidden(*args, **kwargs):
        pytest.fail("The default inputs already attain the proven error floor")

    solver._least_squares = forbidden
    target = forward(font, pinned)
    target["cccc"] = 1
    result, error = solver.reverse(target, inputNormalized=True)
    assert result == {"aaaa": 400, "bbbb": pinned.get("bbbb", 400), "cccc": 400}
    assert error == 1


@pytest.mark.parametrize("target", [1 / 65536, 1 / 32768, -1 / 32768])
@pytest.mark.parametrize("store", [True, False])
def test_default_attains_quantization_floor(target, store):
    font = make_font(hidden=("cccc",))
    avar = add_avar2(font, [{"aaaa": (0, 1, 1)}], {"cccc": [1]})
    if not store:
        avar.table.VarStore = None
    solver = ReverseMapper(font)

    def forbidden(*args, **kwargs):
        pytest.fail("Default inputs already attain the quantization error floor")

    solver._score = forbidden
    solver._least_squares = forbidden
    result, error = solver.reverse(
        {"aaaa": target}, inputNormalized=True, tolerance=0, dropZeroes=True
    )
    assert result == {}
    assert error == abs(target)


def test_equivalent_clipped_problem_does_not_restart():
    from types import SimpleNamespace

    font = make_font(hidden=("cccc",))
    add_avar2(font, [{"aaaa": (0, 1, 1), "bbbb": (0, 1, 1)}], {"cccc": [1]})
    solver = ReverseMapper(font)
    starts = []

    def exact_solution(fun, x0, *, jac, **kwargs):
        starts.append(tuple(x0))
        x = np.array([0.5, 0.25])
        return SimpleNamespace(x=x, fun=fun(x), jac=jac(x), optimality=0)

    solver._least_squares = exact_solution
    target = forward(font, {"aaaa": 650, "bbbb": 525})
    result, error = solver.reverse(target, inputNormalized=True)
    assert error == 0
    assert_target(font, result, target)
    # A clipped restart would start at the solution just returned. Every
    # optimizer invocation here should instead explore a distinct seed.
    assert len(starts) == len(set(starts))


@pytest.mark.parametrize("case", ["clipped", "bound"])
def test_clipped_restart_is_retained_when_problem_can_change(case):
    from types import SimpleNamespace

    font = make_font(hidden=("cccc",))
    add_avar2(
        font,
        [{"aaaa": (0, 1, 1), "bbbb": (0, 1, 1)}],
        {"cccc": [3 if case == "clipped" else 1]},
    )
    solver = ReverseMapper(font)
    starts = []
    point = np.array([0.75, 0.75] if case == "clipped" else [1, 0.25])

    def solution(fun, x0, *, jac, **kwargs):
        starts.append(tuple(x0))
        return SimpleNamespace(
            x=point.copy(), fun=fun(point), jac=jac(point), optimality=0
        )

    solver._least_squares = solution
    solver.reverse({"aaaa": 0.25, "bbbb": 0.5, "cccc": 0}, inputNormalized=True)
    # Clipping changes the first problem; a bound would change the second
    # problem's initial point. Both need the clipped restart despite gtol.
    assert starts.count(tuple(point)) > 1


def test_changing_hidden_output_is_not_constant():
    font = make_font(hidden=("cccc",))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"cccc": [1]})
    target = forward(font, {"aaaa": 650})
    result, error = reverse(font, target, inputNormalized=True)
    assert error <= 1 / 16384
    assert_target(font, result, target)


@pytest.mark.parametrize("columns", [[], [0], [2, 0], [0, 1, 2]])
def test_mapping_reduced_jacobian(columns):
    font = make_font()
    add_avar2(font, [{"aaaa": (0, 1, 1), "bbbb": (0, 1, 1)}], {"cccc": [1]})
    mapping = _AvarMapping(font)
    for x in (np.array([0.2, 0.7, 0.1]), np.array([0.0, 0.7, 0.1])):
        values, full = mapping(x)
        actual_values, reduced = mapping(x, columns=columns)
        np.testing.assert_array_equal(actual_values, values)
        np.testing.assert_array_equal(reduced, full[:, columns])


@pytest.mark.parametrize("version", [None, 1, 2])
def test_separable_inverse_needs_no_iterations(version):
    font = make_font()
    if version == 2:
        add_avar2(font, [{}], {"bbbb": [0.125]})
    elif version == 1:
        font["avar"] = newTable("avar")
        font["avar"].segments = {"aaaa": {-1: -1, 0: 0, 0.5: 0.75, 1: 1}}
    solver = ReverseMapper(font)
    solver._least_squares = lambda *a, **kw: pytest.fail("Separable inverse used SciPy")
    target = forward(font, {"aaaa": 650, "bbbb": 525})
    result, error = solver.reverse(target, inputNormalized=True)
    assert error <= 1 / 16384
    assert_target(font, result, target)


@pytest.mark.parametrize("saturating", [False, True])
@pytest.mark.parametrize("zero_default", [False, True])
def test_one_dimensional_inverse_minimizes_all_outputs(saturating, zero_default):
    font = make_font(("aaaa", "bbbb"), hidden=("bbbb",))
    axis = font["fvar"].axes[0]
    if zero_default:
        axis.minValue, axis.defaultValue, axis.maxValue = -16384, 0, 16384
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"bbbb": [2 if saturating else 1]})
    solver = ReverseMapper(font)
    solver._least_squares = lambda *a, **kw: pytest.fail(
        "One-dimensional inverse used SciPy"
    )
    target = {"aaaa": 0.8 if saturating else 0.2, "bbbb": 0.8 if saturating else 0.6}
    result, error = solver.reverse(target, inputNormalized=True)
    expected = 0.8 if saturating else 0.4
    extent = axis.maxValue - axis.defaultValue
    assert result["aaaa"] == pytest.approx(
        axis.defaultValue + extent * expected, abs=max(0.05, extent / 16384)
    )
    assert error == pytest.approx(0.2 if saturating else np.sqrt(0.08), abs=1 / 16384)


@pytest.mark.parametrize("input_normalized", [False, True])
@pytest.mark.parametrize("output_normalized", [False, True])
@pytest.mark.parametrize("drop_zeroes", [False, True])
@pytest.mark.parametrize(
    "constraints", [{}, {"pinned": {"bbbb": 650}}, {"vary": ["aaaa", "cccc"]}]
)
def test_reusable_solver_matches_one_shot(
    input_normalized, output_normalized, drop_zeroes, constraints
):
    font = make_font(hidden=("cccc",))
    add_avar2(
        font,
        [{"aaaa": (0, 1, 1)}, {"bbbb": (-1, -1, 0)}],
        {"aaaa": [0.25, 0], "bbbb": [0.5, 0], "cccc": [0.5, -0.25]},
    )
    mapper = ReverseMapper(font, cache_size=0, **constraints)
    options = dict(
        inputNormalized=input_normalized,
        outputNormalized=output_normalized,
        dropZeroes=drop_zeroes,
    )
    sources = [{"aaaa": 600}, {"bbbb": 250}, {}]
    targets = [
        map_avar(font, source, outputNormalized=input_normalized) for source in sources
    ]
    expected = [reverse(font, target, **constraints, **options) for target in targets]
    # Revisit targets in a different order without memoization. Mutable
    # evaluator state and starting points must not affect later solutions.
    for i in [0, 1, 2, 1, 0]:
        result, error = mapper.reverse(targets[i], **options)
        assert result == expected[i][0]
        assert error == expected[i][1]


def count_solves(monkeypatch, mapper):
    calls = []
    solve = mapper._solve

    def counted(*args):
        calls.append(None)
        return solve(*args)

    monkeypatch.setattr(mapper, "_solve", counted)
    return calls


def test_solver_cache_reuses_units_and_returns_fresh_results(monkeypatch):
    mapper = ReverseMapper(make_font())
    calls = count_solves(monkeypatch, mapper)
    result, error = mapper.reverse({"aaaa": 600})
    assert result == pytest.approx({"aaaa": 600, "bbbb": 400, "cccc": 400})
    result["aaaa"] = -999
    result, cached_error = mapper.reverse(
        {"aaaa": 0.4}, inputNormalized=True, outputNormalized=True, dropZeroes=True
    )
    assert result == pytest.approx({"aaaa": 0.4})
    assert cached_error == error
    assert len(calls) == 1
    mapper.clear_cache()
    mapper.reverse({"aaaa": 600})
    assert len(calls) == 2


def test_solver_cache_distinguishes_omitted_fixed_outputs(monkeypatch):
    font = make_font(("aaaa", "bbbb"), hidden=("bbbb",))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"bbbb": [1]})
    mapper = ReverseMapper(font)
    calls = count_solves(monkeypatch, mapper)
    unconstrained, error = mapper.reverse({"aaaa": 0.5}, inputNormalized=True)
    constrained, constrained_error = mapper.reverse(
        {"aaaa": 0.5, "bbbb": 0}, inputNormalized=True
    )
    assert unconstrained["aaaa"] == pytest.approx(650)
    assert error <= 1 / 16384
    assert constrained["aaaa"] == pytest.approx(525, abs=0.1)
    assert constrained_error == pytest.approx(0.5 / np.sqrt(2), abs=1 / 16384)
    assert len(calls) == 2


def test_solver_cache_distinguishes_tolerance(monkeypatch):
    mapper = ReverseMapper(make_font())
    calls = count_solves(monkeypatch, mapper)
    mapper.reverse({"aaaa": 600}, tolerance=0)
    mapper.reverse({"aaaa": 600}, tolerance=1 / 16384)
    mapper.reverse({"aaaa": 600}, tolerance=0)
    assert len(calls) == 2


@pytest.mark.parametrize("cache_size, expected_calls", [(0, 6), (2, 4)])
def test_solver_cache_eviction(monkeypatch, cache_size, expected_calls):
    mapper = ReverseMapper(make_font(), cache_size=cache_size)
    calls = count_solves(monkeypatch, mapper)
    # Touch 600 before adding 800: 700 must be evicted first.
    for value in [600, 700, 600, 800, 600, 700]:
        mapper.reverse({"aaaa": value})
    assert len(calls) == expected_calls


def test_solver_copies_constraints():
    pinned = {"bbbb": 650}
    vary = ["aaaa", "cccc"]
    mapper = ReverseMapper(make_font(), pinned=pinned, vary=vary)
    pinned["bbbb"] = 800
    vary.clear()
    result, error = mapper.reverse({"aaaa": 600})
    assert result == pytest.approx({"aaaa": 600, "bbbb": 650, "cccc": 400})
    assert error <= 1 / 16384


@pytest.mark.parametrize("cache_size", [-1, 1.5, None])
def test_solver_rejects_invalid_cache_size(cache_size):
    with pytest.raises(ValueError, match="cache_size"):
        ReverseMapper(make_font(), cache_size=cache_size)


def test_solver_requires_fvar():
    with pytest.raises(ValueError, match="fvar"):
        ReverseMapper(TTFont())


def test_empty_solver_does_not_require_scipy(monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy.optimize", None)
    mapper = ReverseMapper(make_font(()))
    assert mapper.reverse({}) == ({}, 0)
    mapper.clear_cache()


def test_identity_units_and_omitted_targets():
    font = make_font()
    result, _ = reverse(font, {"aaaa": 0.4}, inputNormalized=True, dropZeroes=True)
    assert result == pytest.approx({"aaaa": 600})
    normalized, _ = reverse(font, {"aaaa": 600}, outputNormalized=True)
    assert normalized == pytest.approx({"aaaa": 0.4, "bbbb": 0, "cccc": 0})
    mapped, _ = map_avar(font, {"aaaa": 0.4}, reverse=True, inputNormalized=True)
    assert mapped == pytest.approx({"aaaa": 600, "bbbb": 400, "cccc": 400})


@pytest.mark.parametrize(
    "segment,target,expected",
    [
        ({-1: -1, 0: 0, 0.5: 0.25, 1: 1}, 0.25, 650),
        # A plateau has infinitely many preimages. Prefer its nearest end.
        ({-1: -1, 0: 0, 0.25: 0.5, 0.75: 0.5, 1: 1}, 0.5, 525),
    ],
)
def test_avar1(segment, target, expected):
    font = make_font(("aaaa",))
    font["avar"] = newTable("avar")
    font["avar"].segments = {"aaaa": segment}
    result, _ = reverse(font, {"aaaa": target}, inputNormalized=True)
    assert_target(font, result, {"aaaa": target})
    assert result["aaaa"] == pytest.approx(expected, abs=0.05)


def test_hidden_inputs_stay_default_but_outputs_can_change():
    font = make_font(("aaaa", "bbbb"), hidden=("bbbb",))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"bbbb": [1]})
    target = {"aaaa": 0.5, "bbbb": 0.5}
    result, _ = reverse(font, target, inputNormalized=True)
    assert result["bbbb"] == 400
    assert_target(font, result, target)


def test_pins_use_pre_fvar_units_with_normalized_flags():
    font = make_font(("aaaa", "bbbb"))
    result, _ = reverse(
        font,
        {"aaaa": 0.25, "bbbb": 0.5},
        inputNormalized=True,
        outputNormalized=True,
        pinned={"aaaa": 525},
    )
    assert result == pytest.approx({"aaaa": 0.25, "bbbb": 0.5})
    result, _ = reverse(
        font, {}, inputNormalized=True, pinned={"aaaa": 525, "bbbb": 400}
    )
    assert result == {"aaaa": 525, "bbbb": 400}


def test_pin_none_means_default_including_hidden_axes():
    font = make_font(hidden=("cccc",))
    result, _ = reverse(
        font,
        {"bbbb": 0.5},
        inputNormalized=True,
        pinned={"aaaa": None, "cccc": None},
    )
    assert result == pytest.approx({"aaaa": 400, "bbbb": 650, "cccc": 400})


def test_hidden_output_is_unconstrained():
    # bbbb is hidden (input fixed) and omitted from the target, so its coupled
    # output does not pull the solution: aaaa reaches its target exactly.
    font = make_font(("aaaa", "bbbb"), hidden=("bbbb",))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"bbbb": [1]})
    result, error = reverse(
        font, {"aaaa": 1}, inputNormalized=True, outputNormalized=True
    )
    assert result["aaaa"] == pytest.approx(1, abs=1 / 16384)
    assert error == pytest.approx(0, abs=1 / 16384)


def test_pinned_coupled_output_not_scored():
    # Pinning bbbb, whose output is coupled to aaaa, must not drag the free
    # axis: aaaa still reaches its target exactly and the error stays zero.
    font = make_font(("aaaa", "bbbb"))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"bbbb": [0.8]})
    result, error = reverse(
        font,
        {"aaaa": 0.5},
        inputNormalized=True,
        outputNormalized=True,
        pinned={"bbbb": None},
    )
    assert result["aaaa"] == pytest.approx(0.5, abs=1 / 16384)
    assert error == pytest.approx(0, abs=1 / 16384)


def test_unreachable_target_returns_error():
    # aaaa's output saturates at 0.5, so a normalized target of 1 is
    # unreachable; reverse() reports the residual as the returned error.
    font = make_font(("aaaa",))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"aaaa": [-0.5]})
    result, error = reverse(font, {"aaaa": 1}, inputNormalized=True)
    assert result["aaaa"] == pytest.approx(900, abs=1)
    assert error == pytest.approx(0.5, abs=0.01)


def test_cross_axis_product_roundtrip():
    font = make_font(hidden=("cccc",))
    add_avar2(
        font,
        [{"aaaa": (0, 1, 1), "bbbb": (0, 1, 1)}],
        {"cccc": [0.5]},
    )
    source = {"aaaa": 600, "bbbb": 700, "cccc": 400}
    target = forward(font, source)
    result, _ = reverse(font, target, inputNormalized=True)
    assert result["cccc"] == 400
    assert_target(font, result, target)


def test_multistart_escapes_zero_product_gradient():
    font = make_font(hidden=("cccc",))
    add_avar2(
        font,
        [{"aaaa": (0, 1, 1), "bbbb": (0, 1, 1)}],
        {"cccc": [1.5]},
    )
    result, _ = reverse(font, {"cccc": 1}, inputNormalized=True)
    # min 2*x^2 + (1.5*x^2 - 1)^2 occurs at x = sqrt(2)/3.
    expected = 400 + 500 * np.sqrt(2) / 3
    assert result["aaaa"] == pytest.approx(expected, abs=0.1)
    assert result["bbbb"] == pytest.approx(expected, abs=0.1)
    actual = forward(font, result)
    assert sum((actual[tag] - (tag == "cccc")) ** 2 for tag in actual) < 0.9


def test_prefers_one_nondefault_axis_over_two():
    font = make_font(hidden=("cccc",), positive=("aaaa", "bbbb"))
    add_avar2(
        font,
        [{"aaaa": (0, 1, 1)}, {"bbbb": (0, 1, 1)}],
        {"aaaa": [-1, 0], "bbbb": [0, -1], "cccc": [1, 1]},
    )
    target = {"cccc": 0.75}
    result, _ = reverse(font, target, inputNormalized=True)
    assert sum(value != 400 for value in result.values()) == 1
    assert_target(font, result, target)
    pinned, _ = reverse(font, target, inputNormalized=True, pinned={"aaaa": 400})
    assert pinned == pytest.approx({"aaaa": 400, "bbbb": 775, "cccc": 400}, abs=0.04)


@pytest.mark.parametrize("target", [0.5, 1.0, -1.0])
def test_clipping_and_saturation(target):
    font = make_font(("aaaa",))
    add_avar2(
        font,
        [{"aaaa": (-1, -1, 0)}, {"aaaa": (0, 1, 1)}],
        {"aaaa": [-1, 1]},
    )
    result, _ = reverse(font, {"aaaa": target}, inputNormalized=True)
    assert_target(font, result, {"aaaa": target})


def test_jacobian_matches_unrounded_finite_differences():
    font = make_font()
    avar = add_avar2(
        font,
        [
            {},
            {"aaaa": (0, 0.8, 1), "bbbb": (0, 0.7, 1)},
            {"aaaa": (-1, -0.8, 0), "cccc": (0, 1, 1)},
        ],
        {"aaaa": [0.125, 0.5, 0], "bbbb": [0, 0, -0.25], "cccc": [0, 0.5, 0.25]},
    )
    avar.segments["aaaa"] = {-1: -1, 0: 0, 0.5: 0.7, 1: 1}
    mapping = _AvarMapping(font)
    for x in (np.array([0.3, 0.4, 0.2]), np.array([-0.4, 0.3, 0.7])):
        _, jac = mapping(x)
        numerical = np.column_stack(
            [(mapping(x + d)[0] - mapping(x - d)[0]) / 2e-6 for d in np.eye(3) * 1e-6]
        )
        assert jac == pytest.approx(numerical, abs=1e-8)


def test_jacobian_at_shared_tent_boundary():
    # The individual tents kink at zero, but their sum is linear there.
    font = make_font(("aaaa",))
    add_avar2(
        font,
        [{"aaaa": (-1, -1, 0)}, {"aaaa": (0, 1, 1)}],
        {"aaaa": [-0.25, 0.25]},
    )
    _, jac = _AvarMapping(font)(np.array([0.0]))
    assert jac == pytest.approx(np.array([[1.25]]))


@pytest.mark.parametrize("peak", [-1, -0.5, 0.5, 1])
def test_reverse_zero_width_support(peak):
    font = make_font(hidden=("cccc",))
    add_avar2(
        font,
        [{"aaaa": (peak, peak, peak), "bbbb": (0, 1, 1)}],
        {"aaaa": [-2 * peak], "cccc": [1]},
    )
    source = {"aaaa": 400 + (500 if peak > 0 else 300) * peak, "bbbb": 650}
    target = forward(font, source)
    result, error = reverse(font, target, inputNormalized=True)
    # The inverse exists only on this exact plane. Moving aaaa even one
    # representable input off it removes the hidden cccc contribution.
    assert result == pytest.approx({**source, "cccc": 400}, abs=0.01)
    assert error <= 1 / 16384
    assert_target(font, result, target)


def test_jump_solver_can_be_reused():
    font = make_font(hidden=("cccc",))
    add_avar2(
        font,
        [{"aaaa": (0.5, 0.5, 0.5), "bbbb": (0, 1, 1)}],
        {"aaaa": [-1], "cccc": [1]},
    )
    mapper = ReverseMapper(font, cache_size=0)
    for coordinate in [650, 525, 775, 650]:
        source = {"aaaa": 650, "bbbb": coordinate}
        target = forward(font, source)
        result, error = mapper.reverse(target, inputNormalized=True)
        assert result == pytest.approx({**source, "cccc": 400}, abs=0.01)
        assert error <= 1 / 16384
        assert_target(font, result, target)


def test_reverse_intersecting_jump_planes():
    font = make_font(("aaaa", "bbbb", "cccc", "dddd"), hidden=("dddd",))
    add_avar2(
        font,
        [{"aaaa": (0.5, 0.5, 0.5), "bbbb": (-0.5, -0.5, -0.5), "cccc": (0, 1, 1)}],
        {"aaaa": [-1], "bbbb": [1], "dddd": [1]},
    )
    source = {"aaaa": 650, "bbbb": 250, "cccc": 650}
    target = forward(font, source)
    result, error = reverse(font, target, inputNormalized=True)
    assert error <= 1 / 16384
    assert_target(font, result, target)


@pytest.mark.parametrize("direction", [-1, 1])
def test_reverse_searches_each_side_of_jump(direction):
    font = make_font(("aaaa", "bbbb"), hidden=("bbbb",))
    peak, width = 0.5, 1 / 128
    distractors = [-0.875, -0.75, -0.625, -0.5, -0.375, -0.25, -0.125, -0.0625]
    supports = [{"aaaa": (p - 1 / 64, p, p + 1 / 64)} for p in distractors]
    supports.append(
        {
            "aaaa": (
                peak if direction > 0 else peak - width,
                peak,
                peak + width if direction > 0 else peak,
            )
        }
    )
    add_avar2(
        font,
        supports,
        {
            "aaaa": [0.25 - p for p in distractors] + [-0.5],
            "bbbb": [0.25] * len(distractors) + [1],
        },
    )
    # The eight best region-peak seeds are distractors, and none of the
    # ordinary guesses lands inside this narrow interval. Only this side
    # of the jump can produce the target's hidden-axis contribution.
    source = {"aaaa": 400 + 500 * (peak + direction * width / 2)}
    target = forward(font, source)
    result, error = reverse(font, target, inputNormalized=True)
    assert error <= 1 / 16384
    assert_target(font, result, target)


def test_reverse_unreachable_target_nearest_on_jump():
    font = make_font(hidden=("cccc",))
    add_avar2(
        font,
        [{"aaaa": (0.5, 0.5, 0.5), "bbbb": (0, 1, 1)}],
        {"aaaa": [-1], "cccc": [1]},
    )
    target = {"aaaa": 0, "bbbb": 0.5, "cccc": 0.25}
    result, error = reverse(font, target, inputNormalized=True)
    actual = forward(font, result)
    assert result["aaaa"] == 650
    assert error == pytest.approx(np.sqrt(1 / 24), abs=1 / 16384)
    assert error == pytest.approx(
        np.linalg.norm([actual[t] - target[t] for t in target])
    )


@pytest.mark.parametrize(
    "segments, input_coordinate",
    [
        ({-1: -1, 0: 0, 0.25: 0.5, 1: 1}, 525),
        # The same jump has two preimages in this folded segment map.
        ({-1: -1, 0: 0, 0.25: 0.5, 0.5: 0, 0.75: 0.5, 1: 1}, 525),
        # A point support becomes an interval after an avar1 plateau.
        ({-1: -1, 0: 0, 0.25: 0.5, 0.5: 0.5, 1: 1}, 525),
    ],
)
def test_reverse_jump_after_avar1(segments, input_coordinate):
    font = make_font(hidden=("cccc",))
    avar = add_avar2(
        font,
        [{"aaaa": (0.5, 0.5, 0.5), "bbbb": (0, 1, 1)}],
        {"aaaa": [-1], "cccc": [1]},
    )
    avar.segments["aaaa"] = segments
    target = forward(font, {"aaaa": input_coordinate, "bbbb": 650})
    result, error = reverse(font, target, inputNormalized=True)
    assert result["aaaa"] == pytest.approx(input_coordinate, abs=0.01)
    assert error <= 1 / 16384
    assert_target(font, result, target)


@pytest.mark.parametrize("constraint", ["hidden", "pinned", "vary"])
def test_jump_search_respects_fixed_inputs(constraint):
    font = make_font(hidden=("cccc", "aaaa") if constraint == "hidden" else ("cccc",))
    add_avar2(
        font,
        [{"aaaa": (0.5, 0.5, 0.5), "bbbb": (0, 1, 1)}],
        {"aaaa": [-1], "cccc": [1]},
    )
    target = forward(font, {"aaaa": 650, "bbbb": 650})
    options = (
        {"pinned": {"aaaa": None}}
        if constraint == "pinned"
        else {"vary": ["bbbb"]} if constraint == "vary" else {}
    )
    result, error = reverse(font, target, inputNormalized=True, **options)
    assert result["aaaa"] == 400
    assert error >= 0.5


def test_degenerate_and_one_sided_axes():
    font = make_font(("aaaa", "bbbb"), positive=("aaaa",))
    font["fvar"].axes[1].minValue = font["fvar"].axes[1].maxValue = 400
    result, _ = reverse(font, {"aaaa": -0.5, "bbbb": 1}, inputNormalized=True)
    assert result == {"aaaa": 400, "bbbb": 400}


@pytest.mark.parametrize("variant", ["null", "invalid", "shared"])
def test_varstore_index_variants(variant):
    font = make_font(("aaaa", "bbbb"))
    avar = add_avar2(font, [{"aaaa": (0, 1, 1)}], {"aaaa": [0.25], "bbbb": [0.5]})
    if variant == "null":
        avar.table.VarStore = None
    elif variant == "invalid":
        avar.table.VarIdxMap = builder.buildDeltaSetIndexMap([0xFFFFFFFF, 0x12345678])
    else:
        avar.table.VarIdxMap = builder.buildDeltaSetIndexMap([0, 0])
    target = forward(font, {"aaaa": 550, "bbbb": 650})
    result, _ = reverse(font, target, inputNormalized=True)
    assert_target(font, result, target)


def test_real_avar2_roundtrip():
    path = Path(__file__).parent.parent / "ttLib/tables/data/Amstelvar-avar2.subset.ttf"
    font = TTFont(path)
    source = {"wght": 650, "wdth": 85, "opsz": 24}
    target = forward(font, source)
    before = {tag: dict(seg) for tag, seg in font["avar"].segments.items()}
    result, _ = reverse(font, target, inputNormalized=True, dropZeroes=True)
    assert_target(font, result, target, atol=2 / 16384)
    assert len(result) <= len(source)
    assert font["avar"].segments == before


def test_vary_restricts_to_named_axes():
    path = Path(__file__).parent.parent / "ttLib/tables/data/Amstelvar-avar2.subset.ttf"
    font = TTFont(path)
    source = {"wght": 650, "wdth": 85, "opsz": 24}
    target = forward(font, source)
    result, _ = reverse(
        font,
        target,
        inputNormalized=True,
        dropZeroes=True,
        vary=["wght", "wdth", "opsz"],
    )
    assert set(result) <= {"wght", "wdth", "opsz"}
    assert_target(font, result, target, atol=2 / 16384)


def test_vary_can_use_a_hidden_axis():
    # bbbb is hidden, so by default it is held at its default and the target is
    # unreachable; listing it in `vary` overrides the flag and reaches it.
    font = make_font(("aaaa", "bbbb"), hidden=("bbbb",))
    _, default_error = reverse(
        font, {"bbbb": 0.5}, inputNormalized=True, outputNormalized=True
    )
    assert default_error == pytest.approx(0.5, abs=0.01)
    result, error = reverse(
        font, {"bbbb": 0.5}, inputNormalized=True, outputNormalized=True, vary=["bbbb"]
    )
    assert result["bbbb"] == pytest.approx(0.5, abs=1 / 16384)
    assert error == pytest.approx(0, abs=1 / 16384)


def test_map_vary_requires_reverse():
    font = make_font(("aaaa",))
    with pytest.raises(ValueError, match="vary"):
        map_avar(font, {"aaaa": 0}, vary=["aaaa"])


@pytest.mark.parametrize(
    "location,kwargs,message",
    [
        ({"XXXX": 0}, {}, "Unknown axis"),
        ({}, {"pinned": {"XXXX": 400}}, "Unknown axis"),
        ({"aaaa": float("nan")}, {}, "Invalid target"),
        ({"aaaa": 2}, {"inputNormalized": True}, "Invalid target"),
        ({}, {"pinned": {"aaaa": 1000}}, "Pinned coordinate"),
        ({}, {"pinned": {"bbbb": 500}}, "Hidden axis"),
        ({}, {"vary": ["XXXX"]}, "Unknown axis"),
        ({}, {"vary": ["aaaa"], "pinned": {"aaaa": 400}}, "both varied and pinned"),
        ({}, {"tolerance": -1}, "tolerance"),
    ],
)
def test_invalid_arguments(location, kwargs, message):
    font = make_font(("aaaa", "bbbb"), hidden=("bbbb",))
    with pytest.raises(ValueError, match=message):
        reverse(font, location, **kwargs)


def test_no_fvar():
    assert reverse(TTFont(), {}) is None
    assert roundtrip(TTFont(), {}) is None


def test_scipy_is_optional_for_forward_mapping(monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy.optimize", None)
    font = make_font(("aaaa",))
    assert forward(font, {"aaaa": 650}) == {"aaaa": 0.5}
    with pytest.raises(ImportError, match=r"install fonttools\[avar\]"):
        reverse(font, {"aaaa": 0.5}, inputNormalized=True)


@pytest.mark.parametrize("pin", ["bbbb=400", "bbbb"])
def test_cli_reverse_and_pins(tmp_path, capsys, pin):
    font = make_font(("aaaa", "bbbb"))
    path = tmp_path / "test.ttf"
    font.save(path)
    main(["-i", "--pin", pin, str(path), "aaaa=0.3333333333333333"])
    result = {
        k: float(v)
        for k, v in (line.split("=") for line in capsys.readouterr().out.splitlines())
    }
    assert set(result) == {"aaaa"}
    # CLI output is rounded to F2Dot14, so the round trip holds to ~one unit.
    assert_target(font, result, {"aaaa": 1 / 3}, atol=2 / 16384)


def test_cli_map_rejects_reverse_flags():
    # The reverse options moved to `fonttools varLib.avar.reverse`.
    for argv in (["--reverse", "font.ttf", "wght=0"], ["--pin", "wght=0", "font.ttf"]):
        with pytest.raises(SystemExit, match="2"):
            map_main(argv)


@pytest.mark.parametrize("input_normalized", [False, True])
@pytest.mark.parametrize("output_normalized", [False, True])
@pytest.mark.parametrize("drop_zeroes", [False, True])
@pytest.mark.parametrize(
    "command", [main, roundtrip_main], ids=["reverse", "roundtrip"]
)
def test_cli_empty_location(
    tmp_path, capsys, input_normalized, output_normalized, drop_zeroes, command
):
    font = make_font(("aaaa", "bbbb"))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"bbbb": [0.5]})
    path = tmp_path / "test.ttf"
    font.save(path)
    flags = []
    if input_normalized:
        flags.append("-i")
    if output_normalized:
        flags.append("-o")
    if not drop_zeroes:
        flags.append("-f")
    command([*flags, str(path)])
    result = {
        tag: float(value)
        for tag, value in (
            line.split("=") for line in capsys.readouterr().out.splitlines()
        )
    }
    expected = (
        {"aaaa": 0, "bbbb": 0} if output_normalized else {"aaaa": 400, "bbbb": 400}
    )
    assert result == ({} if drop_zeroes else expected)


@pytest.mark.parametrize("pin", ["XXXX", "aaaa=", "aaaa=nan", "aaaa=1000"])
def test_cli_invalid_pin(tmp_path, pin):
    font = make_font(("aaaa",))
    path = tmp_path / "test.ttf"
    font.save(path)
    with pytest.raises(SystemExit, match="2"):
        main(["-i", "--pin", pin, str(path), "aaaa=0"])


def test_cli_show_error(tmp_path, capsys):
    # aaaa's output saturates at 0.5, so a target of 1 is unreachable and the
    # residual is reported on stderr while stdout stays coordinates-only.
    font = make_font(("aaaa",))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"aaaa": [-0.5]})
    path = tmp_path / "test.ttf"
    font.save(path)
    main(["-i", "--show-error", str(path), "aaaa=1"])
    captured = capsys.readouterr()
    assert captured.out.startswith("aaaa=")
    assert "residual error" in captured.err


def test_cli_vary(tmp_path, capsys):
    # --vary accepts a comma-separated list; unlisted axes stay at default.
    font = make_font(("aaaa", "bbbb", "cccc"))
    path = tmp_path / "test.ttf"
    font.save(path)
    main(["-i", "-o", "--vary", "aaaa,bbbb", str(path), "aaaa=0.5", "bbbb=0.25"])
    result = {
        k: float(v)
        for k, v in (line.split("=") for line in capsys.readouterr().out.splitlines())
    }
    assert result == pytest.approx({"aaaa": 0.5, "bbbb": 0.25})


@pytest.mark.parametrize("input_normalized", [False, True])
@pytest.mark.parametrize("output_normalized", [False, True])
def test_cli_roundtrip(tmp_path, capsys, input_normalized, output_normalized):
    # The roundtrip command forward-maps the source, then reverses it. On this
    # injective font the normalized inputs come back unchanged.
    font = make_font(("aaaa", "bbbb"))
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"bbbb": [0.5]})
    path = tmp_path / "test.ttf"
    font.save(path)
    flags = ["--show-error"]
    if input_normalized:
        flags.append("-i")
    if output_normalized:
        flags.append("-o")
    coords = ["aaaa=0.4", "bbbb=0.6"] if input_normalized else ["aaaa=600", "bbbb=700"]
    roundtrip_main([*flags, str(path), *coords])
    captured = capsys.readouterr()
    result = {
        k: float(v) for k, v in (line.split("=") for line in captured.out.splitlines())
    }
    expected = (
        {"aaaa": 0.4, "bbbb": 0.6} if output_normalized else {"aaaa": 600, "bbbb": 700}
    )
    assert result == pytest.approx(
        expected, abs=1 / 16384 if output_normalized else 0.04
    )
    assert "residual error" in captured.err


@pytest.mark.parametrize("input_normalized", [False, True])
@pytest.mark.parametrize("output_normalized", [False, True])
@pytest.mark.parametrize(
    "avar_version", [None, 1, 2], ids=["no-avar", "avar1", "avar2"]
)
def test_roundtrip_api_includes_hidden_outputs(
    input_normalized, output_normalized, avar_version
):
    font = make_font(hidden=("cccc",))
    if avar_version == 2:
        add_avar2(
            font,
            [{"aaaa": (0, 1, 1), "bbbb": (0, 1, 1)}],
            {"cccc": [0.5]},
        )
    elif avar_version == 1:
        font["avar"] = newTable("avar")
        font["avar"].segments = {
            "aaaa": {-1: -1, 0: 0, 0.5: 0.75, 1: 1},
            "bbbb": {-1: -1, 0: 0, 1: 1},
            "cccc": {-1: -1, 0: 0, 1: 1},
        }
    source = (
        {"aaaa": 0.4, "bbbb": 0.6} if input_normalized else {"aaaa": 600, "bbbb": 700}
    )
    result, error = roundtrip(
        font,
        source,
        inputNormalized=input_normalized,
        outputNormalized=output_normalized,
        dropZeroes=True,
    )
    assert set(result) == {"aaaa", "bbbb"}
    target = map_avar(
        font, source, inputNormalized=input_normalized, outputNormalized=True
    )
    actual = map_avar(
        font, result, inputNormalized=output_normalized, outputNormalized=True
    )
    actual_error = np.linalg.norm([actual[tag] - target[tag] for tag in target])
    assert error == pytest.approx(actual_error, abs=1e-12)
    assert error <= 2 / 16384


def test_cli_roundtrip_pins_and_vary(tmp_path, capsys):
    font = make_font()
    add_avar2(font, [{"aaaa": (0, 1, 1)}], {"cccc": [0.5]})
    path = tmp_path / "test.ttf"
    font.save(path)
    roundtrip_main(
        [
            "-o",
            "--show-error",
            "--vary",
            "aaaa",
            "--pin",
            "bbbb=650,cccc",
            str(path),
            "aaaa=600",
            "bbbb=650",
        ]
    )
    captured = capsys.readouterr()
    result = {
        k: float(v) for k, v in (line.split("=") for line in captured.out.splitlines())
    }
    assert result == pytest.approx({"aaaa": 0.4, "bbbb": 0.5}, abs=1 / 16384)
    assert "residual error" in captured.err


@pytest.mark.parametrize(
    "command", [main, roundtrip_main], ids=["reverse", "roundtrip"]
)
def test_cli_rejects_roundtrip_flag(command):
    with pytest.raises(SystemExit, match="2"):
        command(["--roundtrip", "font.ttf", "aaaa=600"])


@pytest.mark.parametrize(
    "command", [main, roundtrip_main], ids=["reverse", "roundtrip"]
)
def test_cli_missing_scipy(tmp_path, monkeypatch, command):
    font = make_font(("aaaa",))
    path = tmp_path / "test.ttf"
    font.save(path)
    monkeypatch.setitem(sys.modules, "scipy.optimize", None)
    with pytest.raises(SystemExit, match=r"install fonttools\[avar\]"):
        command([str(path), "aaaa=600"])


def test_cli_pin_comma_separated(tmp_path, capsys):
    # --pin accepts a comma-separated list, like --vary (bare tag = default).
    font = make_font(("aaaa", "bbbb", "cccc"))
    path = tmp_path / "test.ttf"
    font.save(path)
    main(["-i", "-o", "--pin", "bbbb=650,cccc", str(path), "aaaa=0.3"])
    result = {
        k: float(v)
        for k, v in (line.split("=") for line in capsys.readouterr().out.splitlines())
    }
    assert result["aaaa"] == pytest.approx(0.3, abs=1 / 16384)
    assert result["bbbb"] == pytest.approx(0.5, abs=1 / 16384)
    assert "cccc" not in result


def test_cli_output_rounds_to_f2dot14(tmp_path, capsys):
    # Output reads cleanly at F2Dot14 resolution, not as solver noise.
    font = make_font(("aaaa",))
    path = tmp_path / "test.ttf"
    font.save(path)
    main(["-i", "-o", str(path), "aaaa=0.6"])
    assert capsys.readouterr().out.strip() == "aaaa=0.6"
    main(["-i", str(path), "aaaa=0.6"])  # user units: norm 0.6 -> wght 700
    assert capsys.readouterr().out.strip() == "aaaa=700.0"
