from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.designspaceLib.statNames import StatNames, getStatNames

from .fixtures import datadir


def test_instance_getStatNames(datadir):
    doc = DesignSpaceDocument.fromfile(datadir / "test_v5_sourceserif.designspace")

    assert getStatNames(doc, doc.instances[0].getFullUserLocation(doc)) == StatNames(
        familyNames={"en": "Source Serif 4"},
        styleNames={"en": "Caption ExtraLight"},
        postScriptFontName="SourceSerif4-CaptionExtraLight",
        styleMapFamilyNames={"en": "Source Serif 4 Caption ExtraLight"},
        styleMapStyleName="regular",
    )


def test_not_all_ordering_specified_and_translations(datadir):
    doc = DesignSpaceDocument.fromfile(datadir / "test_v5.designspace")

    assert getStatNames(doc, {"weight": 200, "width": 125, "Italic": 1}) == StatNames(
        familyNames={
            "en": "MasterFamilyName",
            "fr": "Montserrat",
            "ja": "モンセラート",
        },
        styleNames={
            "fr": "Wide Extra léger Italic",
            "de": "Wide Extraleicht Italic",
            "en": "Wide Extra Light Italic",
        },
        postScriptFontName="MasterFamilyName-WideExtraLightItalic",
        styleMapFamilyNames={
            "en": "MasterFamilyName Wide Extra Light",
            "fr": "Montserrat Wide Extra léger",
            "de": "MasterFamilyName Wide Extraleicht",
            "ja": "モンセラート Wide Extra Light",
        },
        styleMapStyleName="italic",
    )


def test_detect_ribbi_aktiv(datadir):
    doc = DesignSpaceDocument.fromfile(datadir / "test_v5_aktiv.designspace")

    assert getStatNames(doc, {"Weight": 600, "Width": 125, "Italic": 1}) == StatNames(
        familyNames={"en": "Aktiv Grotesk"},
        styleNames={"en": "Ex SemiBold Italic"},
        postScriptFontName="AktivGrotesk-ExSemiBoldItalic",
        styleMapFamilyNames={"en": "Aktiv Grotesk Ex SemiBold"},
        styleMapStyleName="italic",
    )

    assert getStatNames(doc, {"Weight": 700, "Width": 75, "Italic": 1}) == StatNames(
        familyNames={"en": "Aktiv Grotesk"},
        styleNames={"en": "Cd Bold Italic"},
        postScriptFontName="AktivGrotesk-CdBoldItalic",
        styleMapFamilyNames={"en": "Aktiv Grotesk Cd"},
        styleMapStyleName="bold italic",
    )
