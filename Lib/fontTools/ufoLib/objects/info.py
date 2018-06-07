import attr
from typing import Optional, Union


@attr.s(slots=True)
class Info(object):
    familyName = attr.ib(default=None, type=Optional[str])
    styleName = attr.ib(default=None, type=Optional[str])
    styleMapFamilyName = attr.ib(default=None, type=Optional[str])
    styleMapStyleName = attr.ib(default=None, type=Optional[str])
    versionMajor = attr.ib(default=None, type=int)
    # type is positive integer
    versionMinor = attr.ib(default=None, type=int)

    copyright = attr.ib(default=None, type=Optional[str])
    trademark = attr.ib(default=None, type=Optional[str])

    # type is positive Number
    unitsPerEm = attr.ib(default=None, type=Union[int, float])
    descender = attr.ib(default=None, type=Union[int, float])
    xHeight = attr.ib(default=None, type=Union[int, float])
    capHeight = attr.ib(default=None, type=Union[int, float])
    ascender = attr.ib(default=None, type=Union[int, float])
    italicAngle = attr.ib(default=None, type=Union[int, float])

    note = attr.ib(default=None, type=Optional[str])

    # note: all list entries have detailed speccing
    openTypeGaspRangeRecords = attr.ib(default=None, type=list)
    openTypeHeadCreated = attr.ib(default=None, type=Optional[str])
    # type is positive integer
    openTypeHeadLowestRecPPEM = attr.ib(default=None, type=int)
    openTypeHeadFlags = attr.ib(default=None, type=list)

    openTypeHheaAscender = attr.ib(default=None, type=int)
    openTypeHheaDescender = attr.ib(default=None, type=int)
    openTypeHheaLineGap = attr.ib(default=None, type=int)
    openTypeHheaCaretSlopeRise = attr.ib(default=None, type=int)
    openTypeHheaCaretSlopeRun = attr.ib(default=None, type=int)
    openTypeHheaCaretOffset = attr.ib(default=None, type=int)

    openTypeNameDesigner = attr.ib(default=None, type=Optional[str])
    openTypeNameDesignerURL = attr.ib(default=None, type=Optional[str])
    openTypeNameManufacturer = attr.ib(default=None, type=Optional[str])
    openTypeNameManufacturerURL = attr.ib(default=None, type=Optional[str])
    openTypeNameLicense = attr.ib(default=None, type=Optional[str])
    openTypeNameLicenseURL = attr.ib(default=None, type=Optional[str])
    openTypeNameVersion = attr.ib(default=None, type=Optional[str])
    openTypeNameUniqueID = attr.ib(default=None, type=Optional[str])
    openTypeNameDescription = attr.ib(default=None, type=Optional[str])
    openTypeNamePreferredFamilyName = attr.ib(default=None, type=Optional[str])
    openTypeNamePreferredSubfamilyName = attr.ib(
        default=None, type=Optional[str]
    )
    openTypeNameCompatibleFullName = attr.ib(default=None, type=Optional[str])
    openTypeNameSampleText = attr.ib(default=None, type=Optional[str])
    openTypeNameWWSFamilyName = attr.ib(default=None, type=Optional[str])
    openTypeNameWWSSubfamilyName = attr.ib(default=None, type=Optional[str])
    openTypeNameRecords = attr.ib(default=None, type=list)

    openTypeOS2WidthClass = attr.ib(default=None, type=int)
    openTypeOS2WeightClass = attr.ib(default=None, type=int)
    openTypeOS2Selection = attr.ib(default=None, type=list)
    openTypeOS2VendorID = attr.ib(default=None, type=Optional[str])
    openTypeOS2Panose = attr.ib(default=None, type=list)
    openTypeOS2FamilyClass = attr.ib(default=None, type=list)
    openTypeOS2UnicodeRanges = attr.ib(default=None, type=list)
    openTypeOS2CodePageRanges = attr.ib(default=None, type=list)
    openTypeOS2TypoAscender = attr.ib(default=None, type=int)
    openTypeOS2TypoDescender = attr.ib(default=None, type=int)
    openTypeOS2TypoLineGap = attr.ib(default=None, type=int)
    # positive int
    openTypeOS2WinAscent = attr.ib(default=None, type=int)
    # positive int
    openTypeOS2WinDescent = attr.ib(default=None, type=int)
    openTypeOS2Type = attr.ib(default=None, type=list)
    openTypeOS2SubscriptXSize = attr.ib(default=None, type=int)
    openTypeOS2SubscriptYSize = attr.ib(default=None, type=int)
    openTypeOS2SubscriptXOffset = attr.ib(default=None, type=int)
    openTypeOS2SubscriptYOffset = attr.ib(default=None, type=int)
    openTypeOS2SuperscriptXSize = attr.ib(default=None, type=int)
    openTypeOS2SuperscriptYSize = attr.ib(default=None, type=int)
    openTypeOS2SuperscriptXOffset = attr.ib(default=None, type=int)
    openTypeOS2SuperscriptYOffset = attr.ib(default=None, type=int)
    openTypeOS2StrikeoutSize = attr.ib(default=None, type=int)
    openTypeOS2StrikeoutPosition = attr.ib(default=None, type=int)

    openTypeVheaVertTypoAscender = attr.ib(default=None, type=int)
    openTypeVheaVertTypoDescender = attr.ib(default=None, type=int)
    openTypeVheaVertTypoLineGap = attr.ib(default=None, type=int)
    openTypeVheaCaretSlopeRise = attr.ib(default=None, type=int)
    openTypeVheaCaretSlopeRun = attr.ib(default=None, type=int)
    openTypeVheaCaretOffset = attr.ib(default=None, type=int)

    postscriptFontName = attr.ib(default=None, type=Optional[str])
    postscriptFullName = attr.ib(default=None, type=Optional[str])
    postscriptSlantAngle = attr.ib(default=None, type=Union[int, float])
    postscriptUniqueID = attr.ib(default=None, type=int)
    postscriptUnderlineThickness = attr.ib(
        default=None, type=Union[int, float]
    )
    postscriptUnderlinePosition = attr.ib(default=None, type=Union[int, float])
    postscriptIsFixedPitch = attr.ib(default=None, type=bool)
    postscriptBlueValues = attr.ib(default=attr.Factory(list), type=list)
    postscriptOtherBlues = attr.ib(default=attr.Factory(list), type=list)
    postscriptFamilyBlues = attr.ib(default=attr.Factory(list), type=list)
    postscriptFamilyOtherBlues = attr.ib(default=attr.Factory(list), type=list)
    postscriptStemSnapH = attr.ib(default=attr.Factory(list), type=list)
    postscriptStemSnapV = attr.ib(default=attr.Factory(list), type=list)
    postscriptBlueFuzz = attr.ib(default=None, type=Union[int, float])
    postscriptBlueShift = attr.ib(default=None, type=Union[int, float])
    postscriptBlueScale = attr.ib(default=None, type=float)
    postscriptForceBold = attr.ib(default=None, type=bool)
    postscriptDefaultWidthX = attr.ib(default=None, type=Union[int, float])
    postscriptNominalWidthX = attr.ib(default=None, type=Union[int, float])
    postscriptWeightName = attr.ib(default=None, type=Optional[str])
    postscriptDefaultCharacter = attr.ib(default=None, type=Optional[str])
    postscriptWindowsCharacterSet = attr.ib(default=None, type=Optional[str])

    # old stuff
    macintoshFONDName = attr.ib(default=None, type=Optional[str])
    macintoshFONDFamilyID = attr.ib(default=None, type=Optional[int])
    year = attr.ib(default=None, type=Optional[int])
