from pathlib import Path
from runpy import run_path

from fontTools.ttLib import TTFont, newTable
import pytest


@pytest.fixture
def variation_font():
    snippet = Path(__file__).resolve().parents[2] / "Snippets" / "interpolate.py"
    add_variations = run_path(str(snippet))["AddFontVariations"]
    font = TTFont()
    font["name"] = newTable("name")
    font["name"].setName("Existing name", 256, 1, 0, 0)
    add_variations(font)

    compiled = font["fvar"].compile(font)
    font["fvar"] = newTable("fvar")
    font["fvar"].decompile(compiled, font)
    return font


def test_axis_name(variation_font):
    axis = variation_font["fvar"].axes[0]
    assert axis.axisTag == "wght"
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (100, 400, 900)
    assert variation_font["name"].getDebugName(axis.axisNameID) == "Weight"
    assert variation_font["name"].getDebugName(256) == "Existing name"


def test_instance_names(variation_font):
    assert [
        (
            variation_font["name"].getDebugName(instance.subfamilyNameID),
            instance.coordinates,
        )
        for instance in variation_font["fvar"].instances
    ] == [
        ("Thin", {"wght": 100}),
        ("Light", {"wght": 300}),
        ("Regular", {"wght": 400}),
        ("Bold", {"wght": 700}),
        ("Black", {"wght": 900}),
    ]
