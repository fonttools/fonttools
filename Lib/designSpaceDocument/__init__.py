# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import os
import xml.etree.ElementTree as ET

"""
    designSpaceDocument

    - read and write designspace files
    - axes must be defined.
    - warpmap is stored in its axis element
"""

__all__ = [ 'DesignSpaceDocumentError', 'BaseDocReader', 'DesignSpaceDocument', 'SourceDescriptor', 'InstanceDescriptor', 'AxisDescriptor', 'BaseDocReader', 'BaseDocWriter']

class DesignSpaceDocumentError(Exception):
    def __init__(self, msg, obj=None):
        self.msg = msg
        self.obj = obj

    def __str__(self):
        return repr(self.msg) + repr(self.obj)


def _indent(elem, whitespace="    ", level=0):
    # taken from http://effbot.org/zone/element-lib.htm#prettyprint
    i = "\n" + level * whitespace
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + whitespace
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent(elem, whitespace, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class SimpleDescriptor(object):
    """ Containers for a bunch of attributes"""
    def compare(self, other):
        # test if this object contains the same data as the other
        for attr in self._attrs:
            try:
                assert(getattr(self, attr) == getattr(other, attr))
            except AssertionError:
                print("failed attribute", attr, getattr(self, attr), "!=", getattr(other, attr))


class SourceDescriptor(SimpleDescriptor):
    """Simple container for data related to the source"""
    flavor = "source"
    _attrs = ['path', 'name',
              'location', 'copyLib',
              'copyGroups', 'copyFeatures',
              'muteKerning', 'muteInfo',
              'mutedGlyphNames',
              'familyName', 'styleName']

    def __init__(self):
        self.path = None
        self.name = None
        self.location = None
        self.copyLib = False
        self.copyInfo = False
        self.copyGroups = False
        self.copyFeatures = False
        self.muteKerning = False
        self.muteInfo = False
        self.mutedGlyphNames = []
        self.familyName = None
        self.styleName = None


class InstanceDescriptor(SimpleDescriptor):
    """Simple container for data related to the instance"""
    flavor = "instance"
    _attrs = ['path', 'name',
              'location', 'familyName',
              'styleName', 'postScriptFontName',
              'styleMapFamilyName',
              'styleMapStyleName',
              'kerning', 'info']

    def __init__(self):
        self.path = None
        self.name = None
        self.location = None
        self.familyName = None
        self.styleName = None
        self.postScriptFontName = None
        self.styleMapFamilyName = None
        self.styleMapStyleName = None
        self.glyphs = {}
        self.kerning = True
        self.info = True


class AxisDescriptor(SimpleDescriptor):
    """Simple container for the axis data"""
    flavor = "axis"
    _attrs = ['tag', 'name', 'maximum', 'minimum', 'default', 'map']

    def __init__(self):
        self.tag = None       # opentype tag for this axis
        self.name = None      # name of the axis used in locations
        self.labelNames = {}  # names for UI purposes, if this is not a standard axis,
        self.minimum = None
        self.maximum = None
        self.default = None
        self.map = []

    def serialize(self):
        # output to a dict, used in testing
        d = dict(tag = self.tag,
                name = self.name,
                labelNames = self.labelNames,
                maximum = self.maximum,
                minimum = self.minimum,
                default = self.default,
                map = self.map,
            )
        return d


class BaseDocWriter(object):
    _whiteSpace = "    "
    axisDescriptorClass = AxisDescriptor
    sourceDescriptorClass = SourceDescriptor
    instanceDescriptorClass = InstanceDescriptor

    def __init__(self, documentPath, documentObject):
        self.path = documentPath
        self.documentObject = documentObject
        self.toolVersion = 3
        self.root = ET.Element("designspace")
        self.root.attrib['format'] = "%d" % self.toolVersion
        self.root.append(ET.Element("axes"))
        self.root.append(ET.Element("sources"))
        self.root.append(ET.Element("instances"))
        self.axes = []

    def newDefaultLocation(self):
        loc = {}
        for axisDescriptor in self.axes:
            loc[axisDescriptor.name] = axisDescriptor.default
        return loc

    def write(self, pretty=True):
        for axisObject in self.documentObject.axes:
            self._addAxis(axisObject)
        for sourceObject in self.documentObject.sources:
            self._addSource(sourceObject)
        for instanceObject in self.documentObject.instances:
            self._addInstance(instanceObject)
        if pretty:
            _indent(self.root, whitespace=self._whiteSpace)
        tree = ET.ElementTree(self.root)
        tree.write(self.path, encoding="utf-8", method='xml', xml_declaration=True)

    def _makeLocationElement(self, locationObject, name=None):
        """ Convert Location dict to a locationElement."""
        locElement = ET.Element("location")
        if name is not None:
            locElement.attrib['name'] = name
        defaultLoc = self.newDefaultLocation()
        validatedLocation = {}
        for axisName, axisValue in defaultLoc.items():
            # update the location dict with missing default axis values
            validatedLocation[axisName] = locationObject.get(axisName, axisValue)
        for dimensionName, dimensionValue in validatedLocation.items():
            dimElement = ET.Element('dimension')
            dimElement.attrib['name'] = dimensionName
            if type(dimensionValue) == tuple:
                dimElement.attrib['xvalue'] = self.intOrFloat(dimensionValue[0])
                dimElement.attrib['yvalue'] = self.intOrFloat(dimensionValue[1])
            else:
                dimElement.attrib['xvalue'] = self.intOrFloat(dimensionValue)
            locElement.append(dimElement)
        return locElement, validatedLocation

    def intOrFloat(self, num):
        if int(num) == num:
            return "%d" % num
        return "%f" % num

    def _addAxis(self, axisObject):
        self.axes.append(axisObject)
        axisElement = ET.Element('axis')
        axisElement.attrib['tag'] = axisObject.tag
        axisElement.attrib['name'] = axisObject.name
        axisElement.attrib['minimum'] = str(axisObject.minimum)
        axisElement.attrib['maximum'] = str(axisObject.maximum)
        axisElement.attrib['default'] = str(axisObject.default)
        for languageCode, labelName in axisObject.labelNames.items():
            languageElement = ET.Element('labelname')
            languageElement.attrib[u'xml:lang'] = languageCode
            languageElement.text = labelName
            axisElement.append(languageElement)
        if axisObject.map:
            for inputValue, outputValue in axisObject.map:
                mapElement = ET.Element('map')
                mapElement.attrib['input'] = str(inputValue)
                mapElement.attrib['output'] = str(outputValue)
                axisElement.append(mapElement)
        self.root.findall('.axes')[0].append(axisElement)

    def _addInstance(self, instanceObject):
        instanceElement = ET.Element('instance')
        if instanceObject.name is not None:
            instanceElement.attrib['name'] = instanceObject.name
        if instanceObject.familyName is not None:
            instanceElement.attrib['familyname'] = instanceObject.familyName
        if instanceObject.styleName is not None:
            instanceElement.attrib['stylename'] = instanceObject.styleName
        if instanceObject.location is not None:
            locationElement, instanceObject.location = self._makeLocationElement(instanceObject.location)
            instanceElement.append(locationElement)
        if instanceObject.path is not None:
            pathRelativeToDocument = os.path.relpath(instanceObject.path, os.path.dirname(self.path))
            instanceElement.attrib['filename'] = pathRelativeToDocument
        if instanceObject.postScriptFontName is not None:
            instanceElement.attrib['postscriptfontname'] = instanceObject.postScriptFontName
        if instanceObject.styleMapFamilyName is not None:
            instanceElement.attrib['stylemapfamilyname'] = instanceObject.styleMapFamilyName
        if instanceObject.styleMapStyleName is not None:
            instanceElement.attrib['stylemapstylename'] = instanceObject.styleMapStyleName
        if instanceObject.glyphs:
            if instanceElement.findall('.glyphs') == []:
                glyphsElement = ET.Element('glyphs')
                instanceElement.append(glyphsElement)
            glyphsElement = instanceElement.findall('.glyphs')[0]
            for glyphName, data in instanceObject.glyphs.items():
                glyphElement = self._writeGlyphElement(instanceElement, instanceObject, glyphName, data)
                glyphsElement.append(glyphElement)
        if instanceObject.kerning:
            kerningElement = ET.Element('kerning')
            instanceElement.append(kerningElement)
        if instanceObject.info:
            infoElement = ET.Element('info')
            instanceElement.append(infoElement)
        self.root.findall('.instances')[0].append(instanceElement)

    def _addSource(self, sourceObject):
        sourceElement = ET.Element("source")
        pathRelativeToDocument = os.path.relpath(sourceObject.path, os.path.dirname(self.path))
        sourceElement.attrib['filename'] = pathRelativeToDocument
        if sourceObject.name is not None:
            sourceElement.attrib['name'] = sourceObject.name
        if sourceObject.familyName is not None:
            sourceElement.attrib['familyname'] = sourceObject.familyName
        if sourceObject.styleName is not None:
            sourceElement.attrib['stylename'] = sourceObject.styleName
        if sourceObject.copyLib:
            libElement = ET.Element('lib')
            libElement.attrib['copy'] = "1"
            sourceElement.append(libElement)
        if sourceObject.copyGroups:
            groupsElement = ET.Element('groups')
            groupsElement.attrib['copy'] = "1"
            sourceElement.append(groupsElement)
        if sourceObject.copyFeatures:
            featuresElement = ET.Element('features')
            featuresElement.attrib['copy'] = "1"
            sourceElement.append(featuresElement)
        if sourceObject.copyInfo or sourceObject.muteInfo:
            infoElement = ET.Element('info')
            if sourceObject.copyInfo:
                infoElement.attrib['copy'] = "1"
            if sourceObject.muteInfo:
                infoElement.attrib['mute'] = "1"
            sourceElement.append(infoElement)
        if sourceObject.muteKerning:
            kerningElement = ET.Element("kerning")
            kerningElement.attrib["mute"] = '1'
            sourceElement.append(kerningElement)
        if sourceObject.mutedGlyphNames:
            for name in sourceObject.mutedGlyphNames:
                glyphElement = ET.Element("glyph")
                glyphElement.attrib["name"] = name
                glyphElement.attrib["mute"] = '1'
                sourceElement.append(glyphElement)
        locationElement, sourceObject.location = self._makeLocationElement(sourceObject.location)
        sourceElement.append(locationElement)
        self.root.findall('.sources')[0].append(sourceElement)

    def _writeGlyphElement(self, instanceElement, instanceObject, glyphName, data):
        glyphElement = ET.Element('glyph')
        if data.get('mute'):
            glyphElement.attrib['mute'] = "1"
        if data.get('unicodeValue') is not None:
            glyphElement.attrib['unicode'] = hex(data.get('unicodeValue'))
        if data.get('instanceLocation') is not None:
            locationElement, data['instanceLocation'] = self._makeLocationElement(data.get('instanceLocation'))
            glyphElement.append(locationElement)
        if glyphName is not None:
            glyphElement.attrib['name'] = glyphName
        if data.get('note') is not None:
            noteElement = ET.Element('note')
            noteElement.text = data.get('note')
            glyphElement.append(noteElement)
        if data.get('masters') is not None:
            mastersElement = ET.Element("masters")
            for m in data.get('masters'):
                masterElement = ET.Element("master")
                if m.get('glyphName') is not None:
                    masterElement.attrib['glyphname'] = m.get('glyphName')
                if m.get('font') is not None:
                    masterElement.attrib['source'] = m.get('font')
                if m.get('location') is not None:
                    locationElement, m['location'] = self._makeLocationElement(m.get('location'))
                    masterElement.append(locationElement)
                mastersElement.append(masterElement)
            glyphElement.append(mastersElement)
        return glyphElement


class BaseDocReader(object):
    axisDescriptorClass = AxisDescriptor
    sourceDescriptorClass = SourceDescriptor
    instanceDescriptorClass = InstanceDescriptor

    def __init__(self, documentPath, documentObject):
        self.path = documentPath
        self.documentObject = documentObject
        self.documentObject.formatVersion = 0
        tree = ET.parse(self.path)
        self.root = tree.getroot()
        self.documentObject.formatVersion = int(self.root.attrib.get("format", 0))
        self.axes = []
        self.sources = []
        self.instances = []
        self.axisDefaults = {}

    def read(self):
        self.readAxes()
        self.readSources()
        self.readInstances()

    def getSourcePaths(self, makeGlyphs=True, makeKerning=True, makeInfo=True):
        paths = []
        for name in self.documentObject.sources.keys():
            paths.append(self.documentObject.sources[name][0].path)
        return paths

    def newDefaultLocation(self):
        loc = {}
        for axisDescriptor in self.axes:
            loc[axisDescriptor.name] = axisDescriptor.default
        return loc

    def readAxes(self):
        # read the axes elements, including the warp map.
        axes = []
        for axisElement in self.root.findall(".axes/axis"):
            axisObject = self.axisDescriptorClass()
            axisObject.name = axisElement.attrib.get("name")
            axisObject.minimum = float(axisElement.attrib.get("minimum"))
            axisObject.maximum = float(axisElement.attrib.get("maximum"))
            # we need to check if there is an attribute named "initial"
            if axisElement.attrib.get("default") is None:
                if axisElement.attrib.get("initial") is not None:
                    axisObject.default = float(axisElement.attrib.get("initial"))
                else:
                    axisObject.default = axisObject.minimum
            else:
                axisObject.default = float(axisElement.attrib.get("default"))
            axisObject.tag = axisElement.attrib.get("tag")
            for mapElement in axisElement.findall('map'):
                a = float(mapElement.attrib['input'])
                b = float(mapElement.attrib['output'])
                axisObject.map.append((a,b))
            for labelNameElement in axisElement.findall('labelname'):
                # Note: elementtree reads the xml:lang attribute name as
                # '{http://www.w3.org/XML/1998/namespace}lang'
                for key, lang in labelNameElement.items():
                    labelName = labelNameElement.text
                    axisObject.labelNames[lang] = labelName
            self.documentObject.axes.append(axisObject)
            self.axisDefaults[axisObject.name] = axisObject.default

    def readSources(self):
        for sourceElement in self.root.findall(".sources/source"):
            filename = sourceElement.attrib.get('filename')
            sourcePath = os.path.abspath(os.path.join(os.path.dirname(self.path), filename))
            sourceName = sourceElement.attrib.get('name')
            sourceObject = self.sourceDescriptorClass()
            sourceObject.path = sourcePath
            sourceObject.name = sourceName
            familyName = sourceElement.attrib.get("familyname")
            if familyName is not None:
                sourceObject.familyName = familyName
            styleName = sourceElement.attrib.get("stylename")
            if styleName is not None:
                sourceObject.styleName = styleName
            sourceObject.location = self.locationFromElement(sourceElement)
            for libElement in sourceElement.findall('.lib'):
                if libElement.attrib.get('copy') == '1':
                    sourceObject.copyLib = True
            for groupsElement in sourceElement.findall('.groups'):
                if groupsElement.attrib.get('copy') == '1':
                    sourceObject.copyGroups = True
            for infoElement in sourceElement.findall(".info"):
                if infoElement.attrib.get('copy') == '1':
                    sourceObject.copyInfo = True
                if infoElement.attrib.get('mute') == '1':
                    sourceObject.muteInfo = True
            for featuresElement in sourceElement.findall(".features"):
                if featuresElement.attrib.get('copy') == '1':
                    sourceObject.copyFeatures = True
            for glyphElement in sourceElement.findall(".glyph"):
                glyphName = glyphElement.attrib.get('name')
                if glyphName is None:
                    continue
                if glyphElement.attrib.get('mute') == '1':
                    sourceObject.mutedGlyphNames.append(glyphName)
            for kerningElement in sourceElement.findall(".kerning"):
                if kerningElement.attrib.get('mute') == '1':
                    sourceObject.muteKerning = True
            self.documentObject.sources.append(sourceObject)

    def locationFromElement(self, element):
        elementLocation = None
        for locationElement in element.findall('.location'):
            elementLocation = self.readLocationElement(locationElement)
            break
        return elementLocation

    def readLocationElement(self, locationElement):
        """ Format 0 location reader """
        loc = {}
        for dimensionElement in locationElement.findall(".dimension"):
            dimName = dimensionElement.attrib.get("name")
            if dimName not in self.axisDefaults:
                continue
            xValue = yValue = None
            try:
                xValue = dimensionElement.attrib.get('xvalue')
                xValue = float(xValue)
            except ValueError:
                self.logger.info("KeyError in readLocation xValue %3.3f", xValue)
            try:
                yValue = dimensionElement.attrib.get('yvalue')
                if yValue is not None:
                    yValue = float(yValue)
            except ValueError:
                pass
            if yValue is not None:
                loc[dimName] = (xValue, yValue)
            else:
                loc[dimName] = xValue
        return loc

    def readInstances(self, makeGlyphs=True, makeKerning=True, makeInfo=True):
        instanceElements = self.root.findall('.instances/instance')
        for instanceElement in self.root.findall('.instances/instance'):
            self._readSingleInstanceElement(instanceElement, makeGlyphs=makeGlyphs, makeKerning=makeKerning, makeInfo=makeInfo)

    def _readSingleInstanceElement(self, instanceElement, makeGlyphs=True, makeKerning=True, makeInfo=True):
        filename = instanceElement.attrib.get('filename')
        if filename is not None:
            instancePath = os.path.join(os.path.dirname(self.documentObject.path), filename)
            filenameTokenForResults = os.path.basename(filename)
        else:
            instancePath = None
        instanceObject = self.instanceDescriptorClass()
        instanceObject.path = instancePath
        name = instanceElement.attrib.get("name")
        if name is not None:
            instanceObject.name = name
        familyname = instanceElement.attrib.get('familyname')
        if familyname is not None:
            instanceObject.familyName = familyname
        stylename = instanceElement.attrib.get('stylename')
        if stylename is not None:
            instanceObject.styleName = stylename
        postScriptFontName = instanceElement.attrib.get('postscriptfontname')
        if postScriptFontName is not None:
            instanceObject.postScriptFontName = postScriptFontName
        styleMapFamilyName = instanceElement.attrib.get('stylemapfamilyname')
        if styleMapFamilyName is not None:
            instanceObject.styleMapFamilyName = styleMapFamilyName
        styleMapStyleName = instanceElement.attrib.get('stylemapstylename')
        if styleMapStyleName is not None:
            instanceObject.styleMapStyleName = styleMapStyleName
        instanceLocation = self.locationFromElement(instanceElement)
        if instanceLocation is not None:
            instanceObject.location = instanceLocation
        for glyphElement in instanceElement.findall('.glyphs/glyph'):
            self.readGlyphElement(glyphElement, instanceObject)
        for infoElement in instanceElement.findall("info"):
            self.readInfoElement(infoElement, instanceObject)
        self.documentObject.instances.append(instanceObject)

    def readInfoElement(self, infoElement, instanceObject):
        """ Read the info element.

            ::

                <info/>

                Let's drop support for a different location for the info. Never needed it.

            """
        infoLocation = self.locationFromElement(infoElement)
        instanceObject.info = True

    def readKerningElement(self, kerningElement, instanceObject):
        """ Read the kerning element.

        ::

                Make kerning at the location and with the masters specified at the instance level.
                <kerning/>

        """
        kerningLocation = self.locationFromElement(kerningElement)
        instanceObject.addKerning(kerningLocation)

    def readGlyphElement(self, glyphElement, instanceObject):
        """
        Read the glyph element.

        ::

            <glyph name="b" unicode="0x62"/>

            <glyph name="b"/>

            <glyph name="b">
                <master location="location-token-bbb" source="master-token-aaa2"/>
                <master glyphname="b.alt1" location="location-token-ccc" source="master-token-aaa3"/>

                <note>
                    This is an instance from an anisotropic interpolation.
                </note>
            </glyph>

        """
        glyphData = {}
        glyphName = glyphElement.attrib.get('name')
        if glyphName is None:
            raise DesignSpaceDocumentError("Glyph object without name attribute.")
        mute = glyphElement.attrib.get("mute")
        if mute == "1":
            glyphData['mute'] = True
        unicodeValue = glyphElement.attrib.get('unicode')
        if unicodeValue is not None:
            unicodeValue = int(unicodeValue, 16)
            glyphData['unicodeValue'] = unicodeValue
        note = None
        for noteElement in glyphElement.findall('.note'):
            glyphData['note'] = noteElement.text
            break
        instanceLocation = self.locationFromElement(glyphElement)
        if instanceLocation is not None:
            glyphData['instanceLocation'] = instanceLocation
        glyphSources = None
        for masterElement in glyphElement.findall('.masters/master'):
            fontSourceName = masterElement.attrib.get('source')
            sourceLocation = self.locationFromElement(masterElement)
            masterGlyphName = masterElement.attrib.get('glyphname')
            if masterGlyphName is None:
                # if we don't read a glyphname, use the one we have
                masterGlyphName = glyphName
            d = dict(font=fontSourceName,
                     location=sourceLocation,
                     glyphName=masterGlyphName)
            if glyphSources is None:
                glyphSources = []
            glyphSources.append(d)
        if glyphSources is not None:
            glyphData['masters'] = glyphSources
        instanceObject.glyphs[glyphName] = glyphData


class DesignSpaceDocument(object):
    """ Read, write data from the designspace file"""
    def __init__(self, readerClass=None, writerClass=None, fontClass=None):
        self.path = None
        self.formatVersion = None
        self.sources = []
        self.instances = []
        self.axes = []
        #
        if readerClass is not None:
            self.readerClass = readerClass
        else:
            self.readerClass = BaseDocReader
        if writerClass is not None:
            self.writerClass = writerClass
        else:
            self.writerClass = BaseDocWriter
        if fontClass is not None:
            self.fontClass = fontClass
        else:
            from defcon.objects.font import Font
            self.fontClass = Font

    def read(self, path):
        self.path = path
        reader = self.readerClass(path, self)
        reader.read()

    def write(self, path):
        writer = self.writerClass(path, self)
        writer.write()

    def addSource(self, sourceDescriptor):
        self.sources.append(sourceDescriptor)

    def addInstance(self, instanceDescriptor):
        self.instances.append(instanceDescriptor)

    def addAxis(self, axisDescriptor):
        self.axes.append(axisDescriptor)

    def newDefaultLocation(self):
        loc = {}
        for axisDescriptor in self.axes:
            loc[axisDescriptor.name] = axisDescriptor.default
        return loc

    def getFonts(self):
        # convenience method that delivers the masters and their locations
        # so someone can build a thing for a thing.
        fonts = []
        for sourceDescriptor in self.sources:
            if sourceDescriptor.path is not None:
                if os.path.exists(sourceDescriptor.path):
                    f = self.fontClass(sourceDescriptor.path)
                    fonts.append((f, sourceDescriptor.location))
        return fonts

    def getAxisOrder(self):
        names = []
        for axisDescriptor in self.axes:
            names.append(axisDescriptor.name)
        return names


if __name__ == "__main__":

    def test():
        """
        >>> import os
        >>> testDocPath = os.path.join(os.getcwd(), "test.designspace")
        >>> masterPath1 = os.path.join(os.getcwd(), "masters", "masterTest1.ufo")
        >>> masterPath2 = os.path.join(os.getcwd(), "masters", "masterTest2.ufo")
        >>> instancePath1 = os.path.join(os.getcwd(), "instances", "instanceTest1.ufo")
        >>> instancePath2 = os.path.join(os.getcwd(), "instances", "instanceTest2.ufo")
        >>> doc = DesignSpaceDocument()
        >>> # add master 1
        >>> s1 = SourceDescriptor()
        >>> s1.path = masterPath1
        >>> s1.name = "master.ufo1"
        >>> s1.copyLib = True
        >>> s1.copyInfo = True
        >>> s1.copyFeatures = True
        >>> s1.location = dict(weight=0)
        >>> s1.familyName = "MasterFamilyName"
        >>> s1.styleName = "MasterStyleNameOne"
        >>> s1.mutedGlyphNames.append("A")
        >>> s1.mutedGlyphNames.append("Z")
        >>> doc.addSource(s1)
        >>> # add master 2
        >>> s2 = SourceDescriptor()
        >>> s2.path = masterPath2
        >>> s2.name = "master.ufo2"
        >>> s2.copyLib = False
        >>> s2.copyInfo = False
        >>> s2.copyFeatures = False
        >>> s2.muteKerning = True
        >>> s2.location = dict(weight=1000)
        >>> s2.familyName = "MasterFamilyName"
        >>> s2.styleName = "MasterStyleNameTwo"
        >>> doc.addSource(s2)
        >>> # add instance 1
        >>> i1 = InstanceDescriptor()
        >>> i1.path = instancePath1
        >>> i1.familyName = "InstanceFamilyName"
        >>> i1.styleName = "InstanceStyleName"
        >>> i1.name = "instance.ufo1"
        >>> i1.location = dict(weight=500, spooky=666)  # this adds a dimension that is not defined.
        >>> i1.postScriptFontName = "InstancePostscriptName"
        >>> i1.styleMapFamilyName = "InstanceStyleMapFamilyName"
        >>> i1.styleMapStyleName = "InstanceStyleMapStyleName"
        >>> glyphData = dict(name="arrow", mute=True, unicode="0x123")
        >>> i1.glyphs['arrow'] = glyphData
        >>> doc.addInstance(i1)
        >>> # add instance 2
        >>> i2 = InstanceDescriptor()
        >>> i2.path = instancePath2
        >>> i2.familyName = "InstanceFamilyName"
        >>> i2.styleName = "InstanceStyleName"
        >>> i2.name = "instance.ufo2"
        >>> # anisotropic location
        >>> i2.location = dict(weight=500, width=(400,300))
        >>> i2.postScriptFontName = "InstancePostscriptName"
        >>> i2.styleMapFamilyName = "InstanceStyleMapFamilyName"
        >>> i2.styleMapStyleName = "InstanceStyleMapStyleName"
        >>> glyphMasters = [dict(font="master.ufo1", glyphName="BB", location=dict(width=20,weight=20)), dict(font="master.ufo2", glyphName="CC", location=dict(width=900,weight=900))]
        >>> glyphData = dict(name="arrow", unicodeValue=1234)
        >>> glyphData['masters'] = glyphMasters
        >>> glyphData['note'] = "A note about this glyph"
        >>> glyphData['instanceLocation'] = dict(width=100, weight=120)
        >>> i2.glyphs['arrow'] = glyphData
        >>> i2.glyphs['arrow2'] = dict(mute=False)
        >>> doc.addInstance(i2)
        >>> # write some axes
        >>> a1 = AxisDescriptor()
        >>> a1.minimum = 0
        >>> a1.maximum = 1000
        >>> a1.default = 0
        >>> a1.name = "weight"
        >>> a1.tag = "wght"
        >>> # note: just to test the element language, not an actual label name recommendations.
        >>> a1.labelNames[u'fa-IR'] = u"قطر"
        >>> a1.labelNames[u'en'] = u"Wéíght"
        >>> doc.addAxis(a1)
        >>> a2 = AxisDescriptor()
        >>> a2.minimum = 0
        >>> a2.maximum = 1000
        >>> a2.default = 0
        >>> a2.name = "width"
        >>> a2.tag = "wdth"
        >>> a2.map = [(0.0, 10.0), (401.0, 66.0), (1000.0, 990.0)]
        >>> a2.labelNames[u'fr'] = u"Poids"
        >>> doc.addAxis(a2)
        >>> # add an axis that is not part of any location to see if that works
        >>> a3 = AxisDescriptor()
        >>> a3.minimum = 333
        >>> a3.maximum = 666
        >>> a3.default = 444
        >>> a3.name = "spooky"
        >>> a3.tag = "spok"
        >>> a3.map = [(0.0, 10.0), (401.0, 66.0), (1000.0, 990.0)]
        >>> #doc.addAxis(a3)    # uncomment this line to test the effects of default axes values
        >>> # write the document
        >>> doc.write(testDocPath)
        >>> assert os.path.exists(testDocPath)
        >>> # import it again
        >>> new = DesignSpaceDocument()
        >>> new.read(testDocPath)
        >>> for a, b in zip(doc.instances, new.instances):
        ...     a.compare(b)
        >>> for a, b in zip(doc.sources, new.sources):
        ...     a.compare(b)
        >>> for a, b in zip(doc.axes, new.axes):
        ...     a.compare(b)
        >>> [n.mutedGlyphNames for n in new.sources]
        [['A', 'Z'], []]
        >>> doc.getFonts()
        []
        
        >>> # test roundtrip for the axis attributes and data
        >>> axes = {}
        >>> for axis in doc.axes:
        ...     if not axis.tag in axes:
        ...         axes[axis.tag] = []
        ...     axes[axis.tag].append(axis.serialize())
        >>> for axis in new.axes:
        ...     if not axis.tag in axes:
        ...         axes[axis.tag] = []
        ...     axes[axis.tag].append(axis.serialize())
        >>> for v in axes.values():
        ...     a, b = v
        ...     assert a == b        
        """

    def _test():
        import doctest
        doctest.testmod()
    _test()
