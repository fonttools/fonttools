from fontTools import designspaceLib
from fontTools import fontBuilder
from fontTools import varLib
from fontTools.ttLib import newTable
from fontTools.colorLib.builder import buildCOLR
from fontTools.misc.testTools import getXML
from fontTools.ttLib.tables import otTables as ot


def dump(table, ttFont=None):
    print("\n".join(getXML(table.toXML, ttFont)))


def _minimal_font_builder(glyph_order):
    fb = fontBuilder.FontBuilder(unitsPerEm=1024, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    # varLib.build needs a 'name' to store the axes names
    fb.setupNameTable({})
    # TODO: Add more stuff to make it more realistic
    # fb.setupCharacterMap(...)
    # fb.setupGlyf(...)
    # fb.setupHorizontalMetrics(...)
    # fb.setupHorizontalHeader()
    # fb.setupOS2()
    # fb.setupPost()
    return fb


glyph_order = [".notdef", "A", "B", "C", "D", "E"]

fb1 = _minimal_font_builder(glyph_order)
fb2 = _minimal_font_builder(glyph_order)
fb3 = _minimal_font_builder(glyph_order)

# Build interpolation-compatible COLR tables for each master TTF; only the variable
# fields may vary, the paint structure and the non-variable fields must stay identical
# otherwise Bad Things happen.
# One could also build one COLR master, then deepcopy and modify things here and there.
# NOTE: I pass allowLayerReuse=False to disable PaintColrLayers reuse, to ensure each
# master's LayerList has the same number of Paints. We'll automatically recompute the
# PaintColrLayers reuse after a variable COLRv1 table has been built.
fb1.setupCOLR(
    {
        "A": {
            "Format": ot.PaintFormat.PaintColrLayers,
            "Layers": [
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0, 1.0), "C"),
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0, 1.0), "D"),
            ],
        },
        "B": {
            "Format": ot.PaintFormat.PaintTransform,
            # "Format": ot.PaintFormat.PaintTranslate,
            "Paint": (
                ot.PaintFormat.PaintGlyph,
                {
                    # "Format": ot.PaintFormat.PaintLinearGradient,
                    # "Format": ot.PaintFormat.PaintRadialGradient,
                    "Format": ot.PaintFormat.PaintSweepGradient,
                    "ColorLine": {
                        "Extend": "pad",
                        "ColorStop": [
                            {"StopOffset": 0.0, "PaletteIndex": 1},
                            {"StopOffset": 1.0, "PaletteIndex": 2, "Alpha": 0.5},
                        ],
                    },
                    # "x0": 0,
                    # "y0": 0,
                    # "x1": 100,
                    # "y1": 0,
                    # "x2": 0,
                    # "y2": 100,
                    # "r0": 0,
                    # "r1": 100,
                    "centerX": 0,
                    "centerY": 0,
                    "startAngle": -360,
                    "endAngle": 0,
                },
                "C",
            ),
            "Transform": (1.0, 0, 0, 1.0, 0, 0),
            # "dx": 0,
            # "dy": 0,
        },
        # "E": (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0), "C"),
    },
    clipBoxes={
        "A": (0, 0, 1000, 1000),
        "B": (0, 0, 1000, 1000),
        # "E": (0, 0, 1000, 1000),
    },
    allowLayerReuse=False,
)

fb2.setupCOLR(
    {
        "A": {
            "Format": ot.PaintFormat.PaintColrLayers,
            "Layers": [
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0, 1.0), "C"),
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0, 1.0), "D"),
            ],
        },
        "B": {
            "Format": ot.PaintFormat.PaintTransform,
            # "Format": ot.PaintFormat.PaintTranslate,
            "Paint": (
                ot.PaintFormat.PaintGlyph,
                {
                    # "Format": ot.PaintFormat.PaintLinearGradient,
                    # "Format": ot.PaintFormat.PaintRadialGradient,
                    "Format": ot.PaintFormat.PaintSweepGradient,
                    "ColorLine": {
                        "Extend": "pad",
                        "ColorStop": [
                            {"StopOffset": 0.0, "PaletteIndex": 1},
                            {"StopOffset": 1.0, "PaletteIndex": 2, "Alpha": 0.5},
                        ],
                    },
                    # "x0": 0,
                    # "y0": 0,
                    # "x1": 100,
                    # "y1": 0,
                    # "x2": 0,
                    # "y2": 100,
                    # "r0": 0,
                    # "r1": 100,
                    "centerX": 0,
                    "centerY": 0,
                    "startAngle": -360,
                    "endAngle": 0,
                },
                "C",
            ),
            "Transform": (1.0, 0, 0, 1.0, 0, 0),
            # "dx": 0,
            # "dy": 0,
        },
    },
    clipBoxes={
        "A": (0, 0, 1000, 1000),
        "B": (0, 0, 1000, 1000),
    },
    allowLayerReuse=False,
)

fb3.setupCOLR(
    {
        "A": {
            "Format": ot.PaintFormat.PaintColrLayers,
            "Layers": [
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0, 1.0), "C"),
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0, 1.0), "D"),
            ],
        },
        "B": {
            "Format": ot.PaintFormat.PaintTransform,
            # "Format": ot.PaintFormat.PaintTranslate,
            "Paint": (
                ot.PaintFormat.PaintGlyph,
                {
                    # "Format": ot.PaintFormat.PaintLinearGradient,
                    # "Format": ot.PaintFormat.PaintRadialGradient,
                    "Format": ot.PaintFormat.PaintSweepGradient,
                    "ColorLine": {
                        "Extend": "pad",
                        "ColorStop": [
                            {"StopOffset": 0.0, "PaletteIndex": 1},
                            {"StopOffset": 1.0, "PaletteIndex": 2, "Alpha": 0.5},
                        ],
                    },
                    # "x0": 0,
                    # "y0": 0,
                    # "x1": 100,
                    # "y1": 0,
                    # "x2": 0,
                    # "y2": 100,
                    # "r0": 0,
                    # "r1": 100,
                    "centerX": 0,
                    "centerY": 0,
                    "startAngle": -360,
                    "endAngle": 0,
                },
                "C",
            ),
            "Transform": (1.0, 0, 0, 1.0, 0, 0),
            # "dx": 0,
            # "dy": 0,
        },
    },
    clipBoxes={
        "A": (0, 0, 1000, 1000),
        "B": (0, 0, 1000, 1000),
    },
    allowLayerReuse=False,
)

# Now we need a designspace to define axes and assign each master a location
designspace = designspaceLib.DesignSpaceDocument()

axis_defs = [
    dict(
        tag="wght",
        name="Weight",
        minimum=400,
        default=400,
        maximum=700,
    ),
    dict(
        tag="wdth",
        name="Width",
        minimum=100,
        default=100,
        maximum=150,
    ),
]
for axis_def in axis_defs:
    designspace.addAxisDescriptor(**axis_def)

designspace.addSourceDescriptor(
    name="Master 1",
    location={"Weight": 400, "Width": 100},
    font=fb1.font,
)
designspace.addSourceDescriptor(
    name="Master 2",
    location={"Weight": 700, "Width": 100},
    font=fb2.font,
)
designspace.addSourceDescriptor(
    name="Master 3",
    location={"Weight": 400, "Width": 150},
    font=fb3.font,
)

# Optionally add named instances
# designspace.addInstanceDescriptor(
#     styleName="Regular",
#     location={"Weight": 400, "Width": 100},
# )

# print(designspace.tostring().decode())

# Build the variable font.
# I exclude HVAR otherwise the masters also need to contain hmtx (which is pretty
# standard for actual fonts, but here I just care about COLR table).
# varLib.build returns a (vf, model, master_ttfs) tuple but I only care about the first.
vf = varLib.build(designspace, exclude=["HVAR"])[0]

# Compile/decompile to check it's sane
data = vf.getTableData("COLR")
colr = newTable("COLR")
colr.decompile(data, vf)
vf["COLR"] = colr

# Print XML to see what we got
dump(vf["COLR"], vf)

# Save binary VF to disk
# vf.save("/tmp/VF.ttf")
