from pathlib import Path

import pytest
from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.designspaceLib.split import Range
from fontTools.varLib.stat import getStatAxes, getStatLocations


@pytest.fixture
def datadir():
    return Path(__file__).parent / "../designspaceLib/data"


def test_getStatAxes(datadir):
    doc = DesignSpaceDocument.fromfile(datadir / "test_v5.designspace")

    assert getStatAxes(
        doc, {"Italic": 0, "Width": Range(50, 150), "Weight": Range(200, 900)}
    ) == [
        {
            "values": [
                {
                    "flags": 0,
                    "name": {
                        "de": "Extraleicht",
                        "en": "Extra Light",
                        "fr": "Extra léger",
                    },
                    "nominalValue": 200.0,
                    "rangeMaxValue": 250.0,
                    "rangeMinValue": 200.0,
                },
                {
                    "flags": 0,
                    "name": {"en": "Light"},
                    "nominalValue": 300.0,
                    "rangeMaxValue": 350.0,
                    "rangeMinValue": 250.0,
                },
                {
                    "flags": 2,
                    "name": {"en": "Regular"},
                    "nominalValue": 400.0,
                    "rangeMaxValue": 450.0,
                    "rangeMinValue": 350.0,
                },
                {
                    "flags": 0,
                    "name": {"en": "Semi Bold"},
                    "nominalValue": 600.0,
                    "rangeMaxValue": 650.0,
                    "rangeMinValue": 450.0,
                },
                {
                    "flags": 0,
                    "name": {"en": "Bold"},
                    "nominalValue": 700.0,
                    "rangeMaxValue": 850.0,
                    "rangeMinValue": 650.0,
                },
                {
                    "flags": 0,
                    "name": {"en": "Black"},
                    "nominalValue": 900.0,
                    "rangeMaxValue": 900.0,
                    "rangeMinValue": 850.0,
                },
                {
                    "flags": 2,
                    "name": {"en": "Regular"},
                    "value": 400.0,
                    "linkedValue": 700.0,
                },
                {
                    "flags": 0,
                    "name": {"en": "Bold"},
                    "value": 700.0,
                    "linkedValue": 400.0,
                },
            ],
            "name": {"en": "Wéíght", "fa-IR": "قطر"},
            "ordering": 2,
            "tag": "wght",
        },
        {
            "values": [
                {"flags": 0, "name": {"en": "Condensed"}, "value": 50.0},
                {"flags": 3, "name": {"en": "Normal"}, "value": 100.0},
                {"flags": 0, "name": {"en": "Wide"}, "value": 125.0},
                {
                    "flags": 0,
                    "name": {"en": "Extra Wide"},
                    "nominalValue": 150.0,
                    "rangeMinValue": 150.0,
                },
            ],
            "name": {"en": "Width", "fr": "Chasse"},
            "ordering": 1,
            "tag": "wdth",
        },
        {
            "values": [
                {"flags": 2, "linkedValue": 1.0, "name": {"en": "Roman"}, "value": 0.0},
            ],
            "name": {"en": "Italic"},
            "ordering": 3,
            "tag": "ital",
        },
    ]

    assert getStatAxes(doc, {"Italic": 1, "Width": 100, "Weight": Range(400, 700)}) == [
        {
            "values": [
                {
                    "flags": 2,
                    "name": {"en": "Regular"},
                    "nominalValue": 400.0,
                    "rangeMaxValue": 450.0,
                    "rangeMinValue": 350.0,
                },
                {
                    "flags": 0,
                    "name": {"en": "Semi Bold"},
                    "nominalValue": 600.0,
                    "rangeMaxValue": 650.0,
                    "rangeMinValue": 450.0,
                },
                {
                    "flags": 0,
                    "name": {"en": "Bold"},
                    "nominalValue": 700.0,
                    "rangeMaxValue": 850.0,
                    "rangeMinValue": 650.0,
                },
                {
                    "flags": 2,
                    "name": {"en": "Regular"},
                    "value": 400.0,
                    "linkedValue": 700.0,
                },
                {
                    "flags": 0,
                    "name": {"en": "Bold"},
                    "value": 700.0,
                    "linkedValue": 400.0,
                },
            ],
            "name": {"en": "Wéíght", "fa-IR": "قطر"},
            "ordering": 2,
            "tag": "wght",
        },
        {
            "values": [
                {"flags": 3, "name": {"en": "Normal"}, "value": 100.0},
            ],
            "name": {"en": "Width", "fr": "Chasse"},
            "ordering": 1,
            "tag": "wdth",
        },
        {
            "values": [
                {"flags": 0, "name": {"en": "Italic"}, "value": 1.0},
            ],
            "name": {"en": "Italic"},
            "ordering": 3,
            "tag": "ital",
        },
    ]


def test_getStatLocations(datadir):
    doc = DesignSpaceDocument.fromfile(datadir / "test_v5.designspace")

    assert getStatLocations(
        doc, {"Italic": 0, "Width": Range(50, 150), "Weight": Range(200, 900)}
    ) == [
        {
            "flags": 0,
            "location": {"ital": 0.0, "wdth": 50.0, "wght": 300.0},
            "name": {"en": "Some Style", "fr": "Un Style"},
        },
    ]
    assert getStatLocations(
        doc, {"Italic": 1, "Width": Range(50, 150), "Weight": Range(200, 900)}
    ) == [
        {
            "flags": 0,
            "location": {"ital": 1.0, "wdth": 100.0, "wght": 700.0},
            "name": {"en": "Other"},
        },
    ]
