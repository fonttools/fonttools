from __future__ import absolute_import, unicode_literals
import attr
from fontTools.misc.filenames import userNameToFileName
from fontTools.misc.py23 import tounicode
import os
import errno
from lxml import etree
from ufoLib2 import plistlib
from ufoLib2.constants import CONTENTS_FILENAME, LAYERINFO_FILENAME

# Note: we can implement reporting with logging, and lxml Elements
# have a sourceline attr


@attr.s(slots=True)
class GlyphSet(object):
    _path = attr.ib(type=str)
    _contents = attr.ib(init=False, type=dict)
    _filenames = attr.ib(init=False, type=set)

    def __attrs_post_init__(self):
        self.rebuildContents()

    @property
    def path(self):
        return self._path

    # r

    def rebuildContents(self):
        path = os.path.join(self._path, CONTENTS_FILENAME)
        try:
            with open(path, "rb") as file:
                contents = plistlib.load(file)
        except (IOError, OSError) as e:
            if e.errno != errno.ENOENT:
                raise
            contents = {}
        self._contents = contents
        self._filenames = {fn.lower() for fn in self._contents.values()}

    def readGlyph(self, name, classes):
        fileName = self._contents[name]
        path = os.path.join(self._path, fileName)
        try:
            with open(path, "rb") as file:
                tree = etree.parse(file)
        except (IOError, OSError) as e:
            if e.errno == errno.ENOENT:
                raise KeyError(name)
            raise
        return glyphFromTree(tree.getroot(), classes)

    def readLayerInfo(self, layer):
        path = os.path.join(self._path, LAYERINFO_FILENAME)
        try:
            with open(path, "rb") as file:
                layerDict = plistlib.load(file)
        except (IOError, OSError) as e:
            if e.errno != errno.ENOENT:
                raise
            return
        for key, value in layerDict.items():
            setattr(layer, key, value)

    # w

    def deleteGlyph(self, name):
        fileName = self._contents[name]
        path = os.path.join(self._path, fileName)
        os.remove(path)
        del self._contents[name]
        del self._contents[fileName.lower()]

    def writeContents(self):
        path = os.path.join(self._path, CONTENTS_FILENAME)
        with open(path, "wb") as file:
            plistlib.dump(self._contents, file)

    def writeGlyph(self, glyph):
        if not glyph.name:
            raise KeyError("name %r is not a string" % glyph.name)
        fileName = self._contents.get(glyph.name)
        if fileName is None:
            fileName = userNameToFileName(
                tounicode(glyph.name, "utf-8"),
                existing=self._filenames,
                suffix=".glif",
            )
            self._contents[glyph.name] = fileName
            self._filenames.add(fileName.lower())
        root = treeFromGlyph(glyph)
        tree = etree.ElementTree(root)
        path = os.path.join(self._path, fileName)
        with open(path, "wb") as file:
            tree.write(
                file, encoding="utf-8", pretty_print=True, xml_declaration=True
            )

    def writeLayerInfo(self, layer):
        layerDict = {}
        if layer.color is not None:
            layerDict["color"] = layer.color
        if layer.lib:
            layerDict["lib"] = layer.lib
        path = os.path.join(self._path, LAYERINFO_FILENAME)
        with open(path, "wb") as file:
            plistlib.dump(layerDict, file)

    # dict

    def __contains__(self, name):
        return name in self._contents

    def __len__(self):
        return len(self._contents)

    def items(self):
        return self._contents.items()

    def keys(self):
        return self._contents.keys()

    def values(self):
        return self._contents.values()


def _number(s):
    # converts string to float or int
    if "." in s:
        # fast path for decimal notation
        return float(s)
    try:
        return int(s)
    except ValueError:
        # maybe a float in scientific notation?
        return float(s)


def _getNumber(element, attr, default):
    # gets an element's optional attributes and converts it to a number
    s = element.get(attr)
    if not s:
        return default
    # inline to avoid extra call?
    return _number(s)


def _setTransformationAttributes(transformation, d):
    for attrib, value, default in zip(
        ("xScale", "xyScale", "yxScale", "yScale", "xOffset", "yOffset"),
        transformation,
        (1, 0, 0, 1, 0, 0),
    ):
        if value != default:
            d[attrib] = repr(value)


def glyphFromTree(root, classes):
    glyph = classes.Glyph(root.attrib["name"])
    unicodes = []
    for element in root:
        if element.tag == "advance":
            for key in ("width", "height"):
                if key in element.attrib:
                    setattr(glyph, key, _number(element.attrib[key]))
        elif element.tag == "unicode":
            unicodes.append(int(element.attrib["hex"], 16))
        elif element.tag == "note":
            # TODO: strip whitesp?
            glyph.note = element.text
        elif element.tag == "image":
            image = classes.Image(
                fileName=element.attrib["fileName"],
                transformation=classes.Transformation(
                    _getNumber(element, "xScale", 1),
                    _getNumber(element, "xyScale", 0),
                    _getNumber(element, "yxScale", 0),
                    _getNumber(element, "yScale", 1),
                    _getNumber(element, "xOffset", 0),
                    _getNumber(element, "yOffset", 0),
                ),
                color=element.get("color"),
            )
            glyph.image = image
        elif element.tag == "guideline":
            guideline = classes.Guideline(
                x=_getNumber(element, "x", None),
                y=_getNumber(element, "y", None),
                angle=_getNumber(element, "angle", None),
                name=element.get("name"),
                color=element.get("color"),
                identifier=element.get("identifier"),
            )
            glyph.guidelines.append(guideline)
        elif element.tag == "anchor":
            anchor = classes.Anchor(
                x=_number(element.attrib["x"]),
                y=_number(element.attrib["y"]),
                name=element.get("name"),
                color=element.get("color"),
                identifier=element.get("identifier"),
            )
            glyph.anchors.append(anchor)
        elif element.tag == "outline":
            outlineFromTree(element, glyph, classes)
        elif element.tag == "lib":
            glyph.lib = plistlib.fromtree(element)
    glyph.unicodes = unicodes
    return glyph


def outlineFromTree(outline, glyph, classes):
    for element in outline:
        if element.tag == "contour":
            contour = classes.Contour(identifier=element.get("identifier"))
            for element_ in element:
                pointType = element_.get("type")
                if pointType == "offcurve":
                    pointType = None
                point = classes.Point(
                    x=_number(element_.attrib["x"]),
                    y=_number(element_.attrib["y"]),
                    type=pointType,
                    smooth=element_.get("smooth", False),
                    name=element_.get("name"),
                    identifier=element_.get("identifier"),
                )
                contour.append(point)
            glyph.contours.append(contour)
        elif element.tag == "component":
            component = classes.Component(
                baseGlyph=element.attrib["base"],
                transformation=classes.Transformation(
                    _getNumber(element, "xScale", 1),
                    _getNumber(element, "xyScale", 0),
                    _getNumber(element, "yxScale", 0),
                    _getNumber(element, "yScale", 1),
                    _getNumber(element, "xOffset", 0),
                    _getNumber(element, "yOffset", 0),
                ),
                identifier=element.get("identifier"),
            )
            glyph.components.append(component)


def treeFromGlyph(glyph):
    root = etree.Element("glyph", {"name": glyph.name, "format": repr(2)})
    # advance
    if glyph.width or glyph.height:
        advance = etree.SubElement(root, "advance")
        if glyph.width:
            advance.attrib["width"] = repr(glyph.width)
        if glyph.height:
            advance.attrib["height"] = repr(glyph.height)
    # unicodes
    if glyph.unicodes:
        for value in glyph.unicodes:
            etree.SubElement(root, "unicode", {"hex": "%04X" % value})
    # note
    if glyph.note:
        # TODO: indent etc.?
        etree.SubElement(root, "note").text = glyph.note
    # image
    if glyph.image.fileName is not None:
        attrs = {"fileName": glyph.image.fileName}
        if glyph.image.transformation is not None:
            _setTransformationAttributes(glyph.image.transformation, attrs)
        if glyph.image.color is not None:
            attrs["color"] = glyph.image.color
        etree.SubElement(root, "image", attrs)
    # guidelines
    for guideline in glyph.guidelines:
        attrs = {}
        for a in ("x", "y", "angle"):
            v = getattr(guideline, a)
            if v is not None:
                attrs[a] = repr(v)
        if guideline.name is not None:
            attrs["name"] = guideline.name
        if guideline.color is not None:
            attrs["color"] = guideline.color
        if guideline.identifier is not None:
            attrs["identifier"] = guideline.identifier
        etree.SubElement(root, "guideline", attrs)
    # anchors
    for anchor in glyph.anchors:
        attrs = {"x": repr(anchor.x), "y": repr(anchor.y)}
        if anchor.name is not None:
            attrs["name"] = anchor.name
        if anchor.color is not None:
            attrs["color"] = anchor.color
        if anchor.identifier is not None:
            attrs["identifier"] = anchor.identifier
        etree.SubElement(root, "anchor", attrs)
    # outline
    treeFromOutline(glyph, etree.SubElement(root, "outline"))
    # lib
    if glyph.lib:
        lib = etree.SubElement(root, "lib")
        lib.append(plistlib.totree(glyph.lib))
    return root


def treeFromOutline(glyph, outline):
    for contour in glyph.contours:
        element = etree.SubElement(outline, "contour")
        if contour.identifier is not None:
            element.attrib["identifier"] = contour.identifier
        for point in contour:
            attrs = {"x": repr(point.x), "y": repr(point.y)}
            if point.type is not None:
                attrs["type"] = point.type
            if point.smooth:
                attrs["smooth"] = "yes"
            if point.name is not None:
                attrs["name"] = point.name
            if point.identifier is not None:
                attrs["identifier"] = point.identifier
            etree.SubElement(element, "point", attrs)
    for component in glyph.components:
        attrs = {"base": component.baseGlyph}
        _setTransformationAttributes(component.transformation, attrs)
        if component.identifier is not None:
            attrs["identifier"] = component.identifier
        etree.SubElement(outline, "component", attrs)
