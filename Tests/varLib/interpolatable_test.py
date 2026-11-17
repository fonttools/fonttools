from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    DiscreteAxisDescriptor,
    SourceDescriptor,
)
from fontTools.ttLib import TTFont
from fontTools.ttLib.beyond64k import upper_tables
from fontTools.ufoLib import UFOWriter, UFOLibError
from fontTools.varLib.interpolatable import (
    main as interpolatable_main,
    print_master_tree,
    test_gen as interpolatable_test_gen,
)
from types import SimpleNamespace
from fontTools.varLib.interpolatableHelpers import find_parents_and_order
from contextlib import redirect_stdout
from io import StringIO
import json
import os
import shutil
import sys
import tempfile
import unittest
import pytest

try:
    import scipy
except:
    scipy = None

try:
    import munkres
except ImportError:
    munkres = None


@unittest.skipUnless(scipy or munkres, "scipy or munkres not installed")
class InterpolatableTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def setUp(self):
        self.tempdir = None
        self.num_tempfiles = 0

    def tearDown(self):
        if self.tempdir:
            shutil.rmtree(self.tempdir)

    @staticmethod
    def get_test_input(*test_file_or_folder):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "data", *test_file_or_folder)

    @staticmethod
    def get_file_list(folder, suffix, prefix=""):
        all_files = os.listdir(folder)
        file_list = []
        for p in all_files:
            if p.startswith(prefix) and p.endswith(suffix):
                file_list.append(os.path.abspath(os.path.join(folder, p)))
        return sorted(file_list)

    def temp_path(self, suffix):
        self.temp_dir()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir, "tmp%d%s" % (self.num_tempfiles, suffix))

    def temp_dir(self):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()

    def compile_font(self, path, suffix, temp_dir):
        ttx_filename = os.path.basename(path)
        savepath = os.path.join(temp_dir, ttx_filename.replace(".ttx", suffix))
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(path)
        font.save(savepath, reorderTables=None)
        return font, savepath

    # -----
    # Tests
    # -----

    def test_interpolatable_ttf(self):
        suffix = ".ttf"
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        ttf_paths = self.get_file_list(self.tempdir, suffix)
        self.assertIsNone(interpolatable_main(ttf_paths))

    def test_interpolatable_beyond64k_variable_ttf(self):
        suffix = ".ttf"
        ttx_path = self.get_test_input("MutatorSans_All_Variable.ttx")

        self.temp_dir()
        font, font_path = self.compile_font(ttx_path, suffix, self.tempdir)
        upper_tables(font)
        font.save(font_path, reorderTables=None)

        self.assertIsNone(interpolatable_main([font_path]))

    def test_interpolatable_otf(self):
        suffix = ".otf"
        ttx_dir = self.get_test_input("master_ttx_interpolatable_otf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        otf_paths = self.get_file_list(self.tempdir, suffix)
        self.assertIsNone(interpolatable_main(otf_paths))

    def test_interpolatable_cff2(self):
        suffix = ".otf"
        ttx_dir = self.get_test_input("variable_ttx_interpolatable_cff2")
        ttx_path = os.path.abspath(os.path.join(ttx_dir, "interpolatable-test.ttx"))

        self.temp_dir()
        self.compile_font(ttx_path, suffix, self.tempdir)

        otf_path = self.get_file_list(self.tempdir, suffix)[0]

        problems = interpolatable_main([otf_path])
        print(problems)
        self.assertEqual(
            problems["uni0408"],
            [
                {
                    "type": "underweight",
                    "contour": 0,
                    "master_1": "'wght=200.0 opsz=20.0'",
                    "master_2": "'wght=200.0 opsz=60.0'",
                    "master_1_idx": 2,
                    "master_2_idx": 3,
                    "tolerance": pytest.approx(0.9184032411892079),
                    "actual_midpoint": True,
                },
            ],
        )

    def test_interpolatable_ufo(self):
        ttx_dir = self.get_test_input("master_ufo")
        ufo_paths = self.get_file_list(ttx_dir, ".ufo", "TestFamily2-")
        self.assertIsNone(interpolatable_main(ufo_paths))

    def test_interpolatable_cff2_json(self):
        ttx_path = self.get_test_input(
            "variable_ttx_interpolatable_cff2", "interpolatable-test.ttx"
        )
        self.temp_dir()
        _, otf_path = self.compile_font(ttx_path, ".otf", self.tempdir)
        output = StringIO()
        with redirect_stdout(output):
            problems = interpolatable_main(["--json", otf_path])

        self.assertEqual(json.loads(output.getvalue()), problems)
        self.assertEqual(problems["uni0408"][0]["master_1_idx"], 2)
        self.assertEqual(problems["uni0408"][0]["master_2_idx"], 3)

    def test_designspace(self):
        designspace_path = self.get_test_input("InterpolateLayout.designspace")
        self.assertIsNone(interpolatable_main([designspace_path]))

    def test_designspace_decreasing_axis_map(self):
        doc = DesignSpaceDocument.fromfile(
            self.get_test_input("InterpolateLayout.designspace")
        )
        doc.axes[0].map = [(0, 1000), (1000, 0)]
        for source in doc.sources:
            source.location = {"weight": 1000 - source.location["weight"]}
            # save absolute paths with tostring() rather than write(), which makes
            # them relative to the temp dir and fails if it's on another drive
            source.filename = source.path
        path = self.temp_path(".designspace")
        with open(path, "wb") as f:
            f.write(doc.tostring())
        self.assertIsNone(interpolatable_main([path]))

    def test_glyphsapp(self):
        pytest.importorskip("glyphsLib")
        glyphsapp_path = self.get_test_input("InterpolateLayout.glyphs")
        self.assertIsNone(interpolatable_main([glyphsapp_path]))

    def test_VF(self):
        suffix = ".ttf"
        ttx_dir = self.get_test_input("master_ttx_varfont_ttf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "SparseMasters-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        ttf_paths = self.get_file_list(self.tempdir, suffix)

        problems = interpolatable_main(["--quiet"] + ttf_paths)
        self.assertIsNone(problems)

    def test_sparse_interpolatable_ttfs(self):
        suffix = ".ttf"
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "SparseMasters-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        ttf_paths = self.get_file_list(self.tempdir, suffix)

        # without --ignore-missing
        problems = interpolatable_main(["--quiet"] + ttf_paths)
        self.assertEqual(
            problems["a"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["s"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["edotabove"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["dotabovecomb"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )

        # normal order, with --ignore-missing
        self.assertIsNone(interpolatable_main(["--ignore-missing"] + ttf_paths))
        # purposely putting the sparse master (medium) first
        self.assertIsNone(
            interpolatable_main(
                ["--ignore-missing"] + [ttf_paths[1]] + [ttf_paths[0]] + [ttf_paths[2]]
            )
        )
        # purposely putting the sparse master (medium) last
        self.assertIsNone(
            interpolatable_main(
                ["--ignore-missing"] + [ttf_paths[0]] + [ttf_paths[2]] + [ttf_paths[1]]
            )
        )

    def test_sparse_interpolatable_ufos(self):
        ttx_dir = self.get_test_input("master_ufo")
        ufo_paths = self.get_file_list(ttx_dir, ".ufo", "SparseMasters-")

        # without --ignore-missing
        problems = interpolatable_main(["--quiet"] + ufo_paths)
        self.assertEqual(
            problems["a"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["s"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["edotabove"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["dotabovecomb"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )

        # normal order, with --ignore-missing
        self.assertIsNone(interpolatable_main(["--ignore-missing"] + ufo_paths))
        # purposely putting the sparse master (medium) first
        self.assertIsNone(
            interpolatable_main(
                ["--ignore-missing"] + [ufo_paths[1]] + [ufo_paths[0]] + [ufo_paths[2]]
            )
        )
        # purposely putting the sparse master (medium) last
        self.assertIsNone(
            interpolatable_main(
                ["--ignore-missing"] + [ufo_paths[0]] + [ufo_paths[2]] + [ufo_paths[1]]
            )
        )

    def test_sparse_designspace(self):
        designspace_path = self.get_test_input("SparseMasters_ufo.designspace")

        self.assertIsNone(interpolatable_main(["--quiet", designspace_path]))

        # normal order, with --ignore-missing
        self.assertIsNone(interpolatable_main(["--ignore-missing", designspace_path]))

    def test_sparse_glyphsapp(self):
        pytest.importorskip("glyphsLib")
        glyphsapp_path = self.get_test_input("SparseMasters.glyphs")

        problems = interpolatable_main(["--quiet", glyphsapp_path])
        self.assertEqual(
            problems["a"],
            [{"type": "missing", "master": "Sparse Masters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["s"],
            [{"type": "missing", "master": "Sparse Masters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["edotabove"],
            [{"type": "missing", "master": "Sparse Masters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["dotabovecomb"],
            [{"type": "missing", "master": "Sparse Masters-Medium", "master_idx": 1}],
        )

        # normal order, with --ignore-missing
        self.assertIsNone(interpolatable_main(["--ignore-missing", glyphsapp_path]))

    def test_html_report_escapes_glyph_name(self):
        pytest.importorskip("cairo")
        from fontTools.fontBuilder import FontBuilder
        from fontTools.pens.ttGlyphPen import TTGlyphPen

        glyph_name = "<img src=x onerror=alert(1)>"

        def build_master(path, num_contours):
            fb = FontBuilder(1000, isTTF=True)
            fb.setupGlyphOrder([".notdef", glyph_name])
            fb.setupCharacterMap({0x41: glyph_name})
            pen = TTGlyphPen(None)
            for i in range(num_contours):
                y = i * 300
                pen.moveTo((0, y))
                pen.lineTo((0, y + 200))
                pen.lineTo((200, y + 200))
                pen.lineTo((200, y))
                pen.closePath()
            fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), glyph_name: pen.glyph()})
            fb.setupHorizontalMetrics({".notdef": (500, 0), glyph_name: (500, 0)})
            fb.setupHorizontalHeader(ascent=800, descent=-200)
            fb.setupNameTable({"familyName": "Test", "styleName": "Regular"})
            fb.setupOS2()
            fb.setupPost()
            fb.save(path)

        master_a = self.temp_path(".ttf")
        master_b = self.temp_path(".ttf")
        # different contour counts so the glyph is reported as a problem
        build_master(master_a, 1)
        build_master(master_b, 2)
        html_path = self.temp_path(".html")

        interpolatable_main(["--quiet", "--html", html_path, master_a, master_b])

        with open(html_path, "rb") as f:
            html = f.read().decode("utf-8")
        self.assertIn("<h1>Glyph &lt;img src=x onerror=alert(1)&gt;</h1>", html)
        self.assertNotIn(glyph_name, html)

    def test_interpolatable_varComposite(self):
        input_path = self.get_test_input(
            "..", "..", "ttLib", "data", "varc-ac00-ac01.ttf"
        )
        # Just make sure the code runs.
        interpolatable_main((input_path,))


def draw_contours(count, open_paths=False):
    def draw(pen):
        for i in range(count):
            y = i * 300
            pen.beginPath()
            for j, point in enumerate([(0, y), (200, y), (200, y + 200), (0, y + 200)]):
                segment_type = "move" if open_paths and j == 0 else "line"
                pen.addPoint(point, segmentType=segment_type)
            pen.endPath()

    return draw


@pytest.fixture
def layered_designspace(tmp_path):
    paths = [tmp_path / "Regular.ufo", tmp_path / "Bold.ufo"]
    for path in paths:
        with UFOWriter(path, formatVersion=3) as writer:
            writer.writeInfo(SimpleNamespace(unitsPerEm=1000))
            layers = [(None, 1, ["A", "B"])]
            if path == paths[0]:
                layers.append(("intermediate", 2, ["A"]))
            for layer, contours, glyphs in layers:
                glyphset = writer.getGlyphSet(
                    layerName=layer, defaultLayer=layer is None
                )
                for glyph in glyphs:
                    glyphset.writeGlyph(
                        glyph, SimpleNamespace(width=500), draw_contours(contours)
                    )
                glyphset.writeContents()
            writer.writeLayerContents()

    document = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name, axis.tag = "Weight", "wght"
    axis.minimum, axis.default, axis.maximum = 100, 100, 900
    document.addAxis(axis)
    for path, location, layer in [
        (paths[0], 100, None),
        (paths[0], 400, "intermediate"),
        (paths[1], 900, None),
    ]:
        source = SourceDescriptor()
        source.path = str(path)
        source.location = {"Weight": location}
        source.layerName = layer
        document.addSource(source)
    document.write(tmp_path / "Layered.designspace")
    return document


@pytest.mark.parametrize("axes", ["continuous", "decreasing", "discrete"])
@pytest.mark.parametrize("jobs", [1, 2])
def test_designspace_named_layer(layered_designspace, axes, jobs):
    if axes == "decreasing":
        layered_designspace.axes[0].map = [(100, 900), (900, 100)]
        for source in layered_designspace.sources:
            source.location["Weight"] = 1000 - source.location["Weight"]
    elif axes == "discrete":
        axis = DiscreteAxisDescriptor()
        axis.name, axis.tag, axis.values, axis.default = "Style", "STYL", [0, 1], 0
        layered_designspace.addAxis(axis)
        for i, source in enumerate(layered_designspace.sources):
            source.location["Style"] = int(i == 2)
        # Each discrete subspace needs its own default master.
        source = SourceDescriptor()
        source.path = layered_designspace.sources[0].path
        source.location = {"Weight": 100, "Style": 1}
        layered_designspace.addSource(source)
    layered_designspace.write(layered_designspace.path)
    problems = interpolatable_main(
        ["--quiet", "--jobs", str(jobs), "--glyphs", "A", layered_designspace.path]
    )
    assert problems["A"][0] == {
        "type": "path_count",
        "master_1": "Regular",
        "master_2": "Regular (intermediate)",
        "master_1_idx": 0,
        "master_2_idx": 1,
        "value_1": 1,
        "value_2": 2,
    }


@pytest.mark.parametrize("layer", [None, "public.default"])
def test_designspace_default_layer(layered_designspace, layer):
    layered_designspace.sources[1].layerName = layer
    layered_designspace.write(layered_designspace.path)
    assert interpolatable_main(["--quiet", layered_designspace.path]) is None


def test_designspace_sparse_layer(layered_designspace):
    args = ["--quiet", "--glyphs", "B", layered_designspace.path]
    assert interpolatable_main(args) is None
    assert interpolatable_main(["--ignore-missing"] + args) is None


@pytest.mark.parametrize(
    "layer", [None, "public.default", "foreground", "intermediate"]
)
@pytest.mark.parametrize("filter_names", [False, True])
def test_designspace_missing_default_source(
    layered_designspace, tmp_path, layer, filter_names
):
    # Completeness is required at the Designspace default, regardless of
    # which UFO layer it uses.
    path = tmp_path / "Missing.ufo"
    with UFOWriter(path, formatVersion=3) as writer:
        writer.writeInfo(SimpleNamespace(unitsPerEm=1000))
        if layer == "intermediate":
            glyphset = writer.getGlyphSet()
            glyphset.writeGlyph("A", SimpleNamespace(width=500), draw_contours(1))
            glyphset.writeContents()
        glyphset = writer.getGlyphSet(
            layerName=layer, defaultLayer=layer != "intermediate"
        )
        glyphset.writeGlyph("B", SimpleNamespace(width=500), draw_contours(1))
        glyphset.writeContents()
        writer.writeLayerContents()
    layered_designspace.sources[0].path = str(path)
    layered_designspace.sources[0].layerName = layer
    name = "Missing" if layer is None else f"Missing ({layer})"
    args = ["--quiet", "--glyphs", "A"]
    if filter_names:
        # Filtering out an earlier sparse source must keep the remaining
        # sources' sparse flags aligned with their glyph sets.
        path = layered_designspace.sources[0].path
        with UFOWriter(path) as writer:
            writer.getGlyphSet(layerName="unused", defaultLayer=False).writeContents()
            writer.writeLayerContents()
        source = SourceDescriptor(
            path=path, layerName="unused", location={"Weight": 250}
        )
        layered_designspace.sources.insert(0, source)
        for accepted_name in [name, "Regular (intermediate)", "Bold"]:
            args.extend(["--name", accepted_name])
    layered_designspace.write(layered_designspace.path)
    args.append(layered_designspace.path)
    problems = interpolatable_main(args)["A"]
    assert [p for p in problems if p["type"] == "missing"] == [
        {"type": "missing", "master": name, "master_idx": 0}
    ]
    assert not any(
        p["type"] == "missing"
        for p in interpolatable_main(["--ignore-missing"] + args)["A"]
    )


@pytest.mark.parametrize("layer", [None, "public.default", "foreground"])
@pytest.mark.parametrize("axes", ["continuous", "decreasing", "discrete"])
def test_designspace_sparse_source(layered_designspace, tmp_path, layer, axes):
    path = tmp_path / "Medium.ufo"
    with UFOWriter(path, formatVersion=3) as writer:
        writer.writeInfo(SimpleNamespace(unitsPerEm=1000))
        glyphset = writer.getGlyphSet(layerName=layer, defaultLayer=True)
        glyphset.writeGlyph("A", SimpleNamespace(width=500), draw_contours(1))
        glyphset.writeContents()
        writer.writeLayerContents()
    layered_designspace.sources[1].path = str(path)
    layered_designspace.sources[1].layerName = layer
    # Put the sparse source first and the actual default last.
    regular, medium, bold = layered_designspace.sources
    layered_designspace.sources = [medium, bold, regular]
    if axes == "decreasing":
        layered_designspace.axes[0].map = [(100, 900), (900, 100)]
        for source in layered_designspace.sources:
            source.location["Weight"] = 1000 - source.location["Weight"]
    elif axes == "discrete":
        axis = DiscreteAxisDescriptor()
        axis.name, axis.tag, axis.values, axis.default = "Style", "STYL", [0, 1], 0
        layered_designspace.addAxis(axis)
        for source in layered_designspace.sources:
            source.location["Style"] = 1
        layered_designspace.addSourceDescriptor(
            path=regular.path, location={"Weight": 100, "Style": 0}
        )
    layered_designspace.write(layered_designspace.path)
    assert (
        interpolatable_main(["--quiet", "--glyphs", "B", layered_designspace.path])
        is None
    )


def test_designspace_missing_discrete_default(layered_designspace):
    axis = DiscreteAxisDescriptor()
    axis.name, axis.tag, axis.values, axis.default = "Style", "STYL", [0, 1], 0
    layered_designspace.addAxis(axis)
    # The named layer contains A but lacks B. At the continuous default
    # location it must still report B as missing, even in discrete subspace 1.
    layered_designspace.addSourceDescriptor(
        path=layered_designspace.sources[0].path,
        layerName="intermediate",
        location={"Weight": 100, "Style": 1},
    )
    layered_designspace.addSourceDescriptor(
        path=layered_designspace.sources[2].path,
        location={"Weight": 900, "Style": 1},
    )
    layered_designspace.write(layered_designspace.path)
    problems = interpolatable_main(
        ["--quiet", "--glyphs", "B", layered_designspace.path]
    )
    assert problems["B"] == [
        {"type": "missing", "master": "Regular (intermediate)", "master_idx": 3}
    ]


@pytest.mark.parametrize("extra_sparse_source", [False, True])
@pytest.mark.parametrize("empty_intermediate", [False, True])
@pytest.mark.parametrize("bold_contours", [1, 2])
def test_designspace_sparse_layer_comparison(
    layered_designspace, extra_sparse_source, empty_intermediate, bold_contours
):
    if empty_intermediate:
        with UFOWriter(layered_designspace.sources[0].path) as writer:
            glyphset = writer.getGlyphSet(layerName="intermediate", defaultLayer=False)
            glyphset.writeGlyph("B", SimpleNamespace(width=500), draw_contours(0))
            glyphset.writeContents()
    with UFOWriter(layered_designspace.sources[-1].path) as writer:
        glyphset = writer.getGlyphSet()
        glyphset.writeGlyph(
            "B", SimpleNamespace(width=500), draw_contours(bold_contours)
        )
        glyphset.writeContents()
    if extra_sparse_source:
        source = SourceDescriptor(
            path=layered_designspace.sources[0].path,
            layerName="intermediate",
            location={"Weight": 600},
        )
        layered_designspace.sources.insert(2, source)
    layered_designspace.write(layered_designspace.path)
    expected = {
        "type": "nothing" if bold_contours == 1 else "path_count",
        "master_1": "Regular",
        "master_2": "Bold",
        "master_1_idx": 0,
        "master_2_idx": len(layered_designspace.sources) - 1,
    }
    if bold_contours != 1:
        expected.update(value_1=1, value_2=bold_contours)
    problems = interpolatable_main(
        ["--quiet", "--show-all", "--glyphs", "B", layered_designspace.path]
    )
    assert problems["B"] == [expected]


def test_designspace_sparse_layer_open_path(layered_designspace):
    with UFOWriter(layered_designspace.sources[0].path) as writer:
        glyphset = writer.getGlyphSet(layerName="intermediate", defaultLayer=False)
        glyphset.writeGlyph(
            "A", SimpleNamespace(width=500), draw_contours(2, open_paths=True)
        )
        glyphset.writeContents()
    problems = interpolatable_main(
        ["--quiet", "--glyphs", "A", layered_designspace.path]
    )["A"]
    assert [p for p in problems if p["type"] == "open_path"] == [
        {
            "type": "open_path",
            "master": "Regular (intermediate)",
            "master_idx": 1,
            "contour": i,
        }
        for i in range(2)
    ]


def test_designspace_missing_layer(layered_designspace):
    layered_designspace.sources[1].layerName = "nonexistent"
    layered_designspace.write(layered_designspace.path)
    with pytest.raises(UFOLibError, match="nonexistent"):
        interpolatable_main(["--quiet", layered_designspace.path])


@pytest.mark.parametrize("jobs", [1, 2])
def test_designspace_layer_name_filter(layered_designspace, jobs):
    assert (
        interpolatable_main(
            [
                "--quiet",
                "--jobs",
                str(jobs),
                "--name",
                "Regular",
                "--name",
                "Bold",
                layered_designspace.path,
            ]
        )
        is None
    )
    problems = interpolatable_main(
        [
            "--quiet",
            "--jobs",
            str(jobs),
            "--glyphs",
            "A",
            "--name",
            "Regular",
            "--name",
            "Regular (intermediate)",
            layered_designspace.path,
        ]
    )
    assert problems["A"][0]["type"] == "path_count"
    assert problems["A"][0]["master_2"] == "Regular (intermediate)"


@pytest.mark.parametrize("output_file", [False, True])
def test_show_graph(layered_designspace, tmp_path, capsys, monkeypatch, output_file):
    def unexpected_test(*args, **kwargs):
        pytest.fail("--show-graph must exit before checking glyphs")

    monkeypatch.setattr("fontTools.varLib.interpolatable.test_gen", unexpected_test)
    monkeypatch.setattr(
        "fontTools.varLib.interpolatable._parallel_test_gen", unexpected_test
    )
    args = ["--show-graph", "--jobs", "2", layered_designspace.path]
    if output_file:
        path = tmp_path / "graphs" / "masters.txt"
        args.extend(["--output", str(path)])
    assert interpolatable_main(args) is None
    expected = (
        "[0] Regular (normalized: default)\n"
        "└── [1] Regular (intermediate) (normalized: Weight=0.375)\n"
        "    └── [2] Bold (normalized: Weight=1.0)\n"
    )
    if output_file:
        assert capsys.readouterr().out == ""
        assert path.read_text(encoding="utf-8") == expected
    else:
        assert capsys.readouterr().out == expected


def test_show_graph_name_filter(layered_designspace, capsys):
    assert (
        interpolatable_main(
            [
                "--show-graph",
                "--name",
                "Regular",
                "--name",
                "Bold",
                layered_designspace.path,
            ]
        )
        is None
    )
    assert capsys.readouterr().out == (
        "[0] Regular (normalized: default)\n" "└── [1] Bold (normalized: Weight=1.0)\n"
    )


def test_print_master_tree_branches_and_roots(capsys):
    print_master_tree(
        [None, 0, 0, 1, None, 4],
        [0, 4, 1, 2, 5, 3],
        ["Regular", "Medium", "Wide", "Bold", "Italic", "Bold Italic"],
        [],
    )
    assert capsys.readouterr().out == (
        "[0] Regular\n"
        "├── [1] Medium\n"
        "│   └── [3] Bold\n"
        "└── [2] Wide\n"
        "[4] Italic\n"
        "└── [5] Bold Italic\n"
    )


def test_progress_callback_after_each_glyph():
    def make_glyph(count):
        def draw(pen, **kwargs):
            for i in range(count):
                y = i * 300
                pen.moveTo((0, y))
                pen.lineTo((200, y))
                pen.lineTo((200, y + 200))
                pen.lineTo((0, y + 200))
                pen.closePath()

        return SimpleNamespace(draw=draw)

    glyphsets = [
        {"A": make_glyph(1), "sparse": None, "empty": make_glyph(0)},
        {"A": make_glyph(2), "sparse": make_glyph(1), "empty": make_glyph(0)},
    ]
    completed = []
    problems = interpolatable_test_gen(
        glyphsets,
        glyphs=["A", "sparse", "empty"],
        progressFunc=completed.append,
    )
    assert next(problems)[1]["type"] == "path_count"
    assert completed == []
    assert list(problems) == []
    assert completed == ["A", "sparse", "empty"]


@pytest.mark.parametrize(
    "terminal, progress, quiet, expected",
    [
        (True, True, False, True),
        (False, True, False, False),
        (True, False, False, False),
        (True, True, True, False),
    ],
)
def test_progress_terminal_only(
    layered_designspace, capsys, monkeypatch, terminal, progress, quiet, expected
):
    stderr = StringIO()
    monkeypatch.setattr(stderr, "isatty", lambda: terminal)
    monkeypatch.setattr(sys, "stderr", stderr)
    args = ["--json", "--glyphs", "A B", layered_designspace.path]
    if progress:
        args.append("--progress")
    if quiet:
        args.append("--quiet")
    problems = interpolatable_main(args)
    output = capsys.readouterr().out
    if quiet:
        assert output == ""
    else:
        assert json.loads(output) == problems
    if expected:
        assert "Checking glyphs:" in stderr.getvalue()
        assert "2/2\n" in stderr.getvalue()
    else:
        assert stderr.getvalue() == ""


@pytest.mark.parametrize("start_method", ["default", "spawn"])
@pytest.mark.parametrize("kind", ["path_count", "missing", "open_path"])
def test_parallel_designspace(
    layered_designspace, capsys, monkeypatch, start_method, kind
):
    if kind == "missing":
        with UFOWriter(layered_designspace.sources[0].path) as writer:
            glyphset = writer.getGlyphSet()
            glyphset.deleteGlyph("A")
            glyphset.writeContents()
    elif kind == "open_path":
        with UFOWriter(layered_designspace.sources[0].path) as writer:
            glyphset = writer.getGlyphSet(layerName="intermediate", defaultLayer=False)
            glyphset.writeGlyph(
                "A", SimpleNamespace(width=500), draw_contours(2, open_paths=True)
            )
            glyphset.writeContents()

    args = ["--json", "--show-all", "--glyphs", "B A", layered_designspace.path]
    expected = interpolatable_main(args)
    serial_output = capsys.readouterr().out
    assert any(problem["type"] == kind for problem in expected["A"])

    if start_method == "spawn":
        # A multithreaded parent must use the spawn fallback even on Linux.
        monkeypatch.setattr("threading.active_count", lambda: 2)
    completed = []
    parent_pid = os.getpid()

    def progress(glyph):
        assert os.getpid() == parent_pid
        completed.append(glyph)

    monkeypatch.setattr(
        "fontTools.varLib.interpolatable._make_progress",
        lambda *args: progress,
    )
    actual = interpolatable_main(["--jobs", "2"] + args)
    assert actual == expected
    assert capsys.readouterr().out == serial_output
    assert list(actual) == list(expected)
    assert list(json.loads(serial_output)) == ["B", "A"]
    assert sorted(completed) == ["A", "B"]


@pytest.mark.parametrize("start_method", ["default", "spawn"])
@pytest.mark.parametrize(
    "source, suffix",
    [
        ("MutatorSans_All_Variable.ttx", ".ttf"),
        ("variable_ttx_interpolatable_cff2/interpolatable-test.ttx", ".otf"),
    ],
)
def test_parallel_variable_font(
    tmp_path, capsys, monkeypatch, start_method, source, suffix
):
    font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
    font.importXML(os.path.join(os.path.dirname(__file__), "data", source))
    path = tmp_path / ("font" + suffix)
    font.save(path)
    args = ["--json", "--show-all", str(path)]
    expected = interpolatable_main(args)
    serial_output = capsys.readouterr().out

    if start_method == "spawn":
        monkeypatch.setattr("threading.active_count", lambda: 2)
    assert interpolatable_main(["-j", "2"] + args) == expected
    assert capsys.readouterr().out == serial_output
    if suffix == ".otf":
        assert any(p.get("actual_midpoint") for p in expected["uni0408"])


@pytest.mark.parametrize("start_method", ["default", "spawn"])
def test_parallel_worker_error(layered_designspace, monkeypatch, start_method):
    from fontTools.varLib import interpolatable

    if start_method == "spawn":
        monkeypatch.setattr("threading.active_count", lambda: 2)
    args = ["--tolerance", "-1", layered_designspace.path]
    glyphsets, options = interpolatable_main(args, _prepare=True)
    # Tolerance is validated by test_gen, after input preparation succeeds.
    with pytest.raises(AssertionError):
        list(interpolatable._parallel_test_gen(glyphsets, options, 2, args))


def test_jobs_all_cpus(layered_designspace, monkeypatch):
    cpu_count = "process_cpu_count" if hasattr(os, "process_cpu_count") else "cpu_count"
    monkeypatch.setattr(os, cpu_count, lambda: 2)
    args = ["--quiet", "--show-all", layered_designspace.path]
    assert interpolatable_main(["--jobs", "0"] + args) == interpolatable_main(args)


def test_jobs_negative(capsys):
    with pytest.raises(SystemExit) as error:
        interpolatable_main(["--jobs", "-1", "font.ttf"])
    assert error.value.code == 2
    assert "--jobs must be zero or greater" in capsys.readouterr().err


@pytest.mark.parametrize(
    "source, suffix",
    [
        ("MutatorSans_All_Variable.ttx", ".ttf"),
        ("variable_ttx_interpolatable_cff2/interpolatable-test.ttx", ".otf"),
    ],
)
def test_show_graph_progress(tmp_path, capsys, monkeypatch, source, suffix):
    font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
    font.importXML(os.path.join(os.path.dirname(__file__), "data", source))
    total = len(font.getGlyphOrder())
    path = tmp_path / ("font" + suffix)
    font.save(path)
    stderr = StringIO()
    monkeypatch.setattr(stderr, "isatty", lambda: True)
    monkeypatch.setattr(sys, "stderr", stderr)
    assert interpolatable_main(["--show-graph", "--progress", str(path)]) is None
    output = capsys.readouterr().out
    assert "[0]" in output
    assert "Finding masters:" not in output
    assert "Finding masters:" in stderr.getvalue()
    assert f"{total}/{total}\n" in stderr.getvalue()
    assert "Checking glyphs:" not in stderr.getvalue()


@pytest.mark.parametrize(
    "locations, discrete_axes, parents, order",
    [
        ([{}, {"wght": 0.5}, {"wght": 1}], set(), [None, 0, 1], [0, 1, 2]),
        ([{"wght": 1}, {}, {"wght": 0.5}], set(), [2, None, 1], [1, 2, 0]),
        (
            [{}, {"wght": 1}, {"wdth": 2}, {"wght": 1, "wdth": 2}],
            set(),
            [None, 0, 0, 2],
            [0, 1, 2, 3],
        ),
        (
            [
                {"ital": 0},
                {"ital": 0, "wght": 0.5},
                {"ital": 1},
                {"ital": 1, "wght": 0.5},
            ],
            {"ital"},
            [None, 0, None, 2],
            [0, 2, 1, 3],
        ),
        pytest.param(
            [{}, {"wght": 1, "wdth": 0.1}, {"wght": 1, "opsz": 0.1}],
            set(),
            [None, 0, 0],
            [0, 1, 2],
            id="incomparable-axis-sets",
        ),
        pytest.param(
            [
                {"wght": 0, "wdth": 0, "opsz": 0},
                {"wght": 1, "wdth": 0.1, "opsz": 0},
                {"wght": 1, "wdth": 0, "opsz": 0.1},
            ],
            set(),
            [None, 0, 0],
            [0, 1, 2],
            id="explicit-zero-coordinates",
        ),
        pytest.param(
            [
                {},
                {"wght": 1},
                {"wght": 0.95, "wdth": 0.95},
                {"wght": 1, "wdth": 1},
            ],
            set(),
            [None, 0, 3, 1],
            [0, 1, 3, 2],
            id="fewer-coordinate-changes-before-distance",
        ),
        pytest.param(
            [{}, {"wght": 0.5}, {"wght": 1, "wdth": 1}],
            set(),
            [None, 0, 1],
            [0, 1, 2],
            id="subset-with-different-values",
        ),
        pytest.param(
            [
                {"ital": 0},
                {"ital": 0, "wght": 1, "wdth": 0.1},
                {"ital": 0, "wght": 1, "opsz": 0.1},
                {"ital": 1},
                {"ital": 1, "wght": 1, "wdth": 0.1},
                {"ital": 1, "wght": 1, "opsz": 0.1},
            ],
            {"ital"},
            [None, 0, 0, None, 3, 3],
            [0, 3, 1, 2, 4, 5],
            id="axis-subsets-in-discrete-subspaces",
        ),
        pytest.param(
            [{}, {"wght": 1 / 16384}, {"wght": 2 / 16384}],
            set(),
            [None, 0, 1],
            [0, 1, 2],
            id="nearby-masters",
        ),
        pytest.param(
            [{}, {}, {"wght": 1}],
            set(),
            [None, None, 0],
            [0, 1, 2],
            id="duplicate-defaults",
        ),
        pytest.param(
            [{}, {"wght": 1}, {"wght": 1}],
            set(),
            [None, 0, 1],
            [0, 1, 2],
            id="duplicate-nondefault-locations",
        ),
    ],
)
def test_find_parents_and_order(locations, discrete_axes, parents, order, monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy.sparse.csgraph", None)
    actual_parents, actual_order = find_parents_and_order(
        [None] * len(locations), locations, discrete_axes=discrete_axes
    )
    assert actual_parents == parents
    assert actual_order == order
    assert all(type(i) is int for i in actual_order)
    assert all(i is None or type(i) is int for i in actual_parents)
    assert json.loads(json.dumps([actual_parents, actual_order])) == [parents, order]


def test_find_parents_and_order_without_locations():
    parents, order = find_parents_and_order([None] * 3, None)
    assert (parents, order) == ([None, 0, 1], [0, 1, 2])
    assert json.loads(json.dumps([parents, order])) == [[None, 0, 1], [0, 1, 2]]


if __name__ == "__main__":
    sys.exit(unittest.main())
