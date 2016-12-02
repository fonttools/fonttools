# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import

import logging
import os
import xml.etree.ElementTree as ET
from mutatorMath.objects.location import biasFromLocations, Location

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


def tagForAxisName(name):
    # try to find or make a tag name for this axis name
    names = {
        'weight':   ('wght', dict(en = 'Weight')),
        'width':    ('wdth', dict(en = 'Width')),
        'optical':  ('opsz', dict(en = 'Optical Size')),
        'slant':    ('slnt', dict(en = 'Slant')),
        'italic':   ('ital', dict(en = 'Italic')),
    }
    if name.lower() in names:
        return names[name.lower()]
    if len(name) < 4:
        tag = name + "*"*(4-len(name))
    else:
        tag = name[:4]
    return tag, dict(en = name)

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

    @classmethod
    def getAxisDecriptor(cls):
        return cls.axisDescriptorClass()

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
        self._strictAxisNames = True

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
        if not axes:
            self._strictAxisNames = False

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
            if self._strictAxisNames and dimName not in self.axisDefaults:
                # In case the document contains axis definitions,
                # then we should only read the axes we know about. 
                # However, if the document does not contain axes,
                # then we need to create them after reading.
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
        self.logger = logging.getLogger("DesignSpaceDocumentLog")
        self.path = None
        self.formatVersion = None
        self.sources = []
        self.instances = []
        self.axes = []
        self.default = None         # name of the default master
        self.defaultLoc = None
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

    def newAxisDescriptor(self):
        # Ask the writer class to make us a new axisDescriptor
        return self.writerClass.getAxisDecriptor()

    def getAxisOrder(self):
        names = []
        for axisDescriptor in self.axes:
            names.append(axisDescriptor.name)
        return names

    def check(self):
        """
            After reading we need to make sure we have a valid designspace. 
            This means making repairs if things are missing
                - check if we have axes and deduce them from the masters if they're missing
                - that can include axes referenced in masters, instances, glyphs. 
                - if no default is assigned, use mutatormath to find out. 
                - record the default in the designspace
                - report all the changes in a log
                - save a "repaired" version of the doc
        """
        self.checkAxes()
        self.checkDefault()

    def checkDefault(self):
        """ Check the sources for a copyInfo flag."""
        flaggedDefaultCandidate = None
        for sourceDescriptor in self.sources:
            names = set()
            if sourceDescriptor.copyInfo:
                # we choose you!
                flaggedDefaultCandidate = sourceDescriptor
        masterLocations = [src.location for src in self.sources]
        mutatorBias = biasFromLocations(masterLocations, preferOrigin=False)
        c = [src for src in self.sources if src.location==mutatorBias]
        if c:
            mutatorDefaultCandidate = c[0]
        else:
            mutatorDefaultCandidate = None
        # what are we going to do?
        if flaggedDefaultCandidate is not None:
            if mutatorDefaultCandidate is not None:
                if mutatorDefaultCandidate.name != flaggedDefaultCandidate.name:
                    # warn if we have a conflict
                    self.logger.info("Note: conflicting default masters:\n\tUsing %s as default\n\tMutator found %s"%(flaggedDefaultCandidate.name, mutatorDefaultCandidate.name))
            self.default = flaggedDefaultCandidate
            self.defaultLoc = self.default.location
        else:
            # we have no flagged default candidate
            # let's use the one from mutator
            if flaggedDefaultCandidate is None and mutatorDefaultCandidate is not None:
                # we didn't have a flag, use the one selected by mutator
                self.default = mutatorDefaultCandidate
                self.defaultLoc = self.default.location
        self.default.copyInfo = True


    def checkAxes(self):
        """
            If we don't have axes in the document, make some, report
            Should we include the instance locations when determining the axis extrema?
        """
        axisValues = {}
        # find all the axes
        locations = []
        for sourceDescriptor in self.sources:
            locations.append(sourceDescriptor.location)
        for instanceDescriptor in self.instances:
            locations.append(instanceDescriptor.location)
            for name, glyphData in instanceDescriptor.glyphs.items():
                loc = glyphData.get("instanceLocation")
                if loc is not None:
                    locations.append(loc)
                for m in glyphData.get('masters', []):
                    locations.append(m['location'])
        for loc in locations:
            for name, value in loc.items():
                if not name in axisValues:
                    axisValues[name] = []
                if type(value)==tuple:
                    for v in value:
                        axisValues[name].append(v)
                else:
                    axisValues[name].append(value)
        have = self.getAxisOrder()
        for name, values in axisValues.items():
            if name not in have:
                # we need to make this axis
                a = self.newAxisDescriptor()
                a.name = name
                a.minimum = min(values)
                a.maximum = max(values)
                a.default = a.minimum
                a.tag, a.labelNames = tagForAxisName(a.name)
                self.addAxis(a)
                self.logger.info("CheckAxes: added a missing axis %s, %3.3f %3.3f", a.name, a.minimum, a.maximum)
                #print("CheckAxes: added a missing axis %s, %3.3f %3.3f"%(a.name, a.minimum, a.maximum))


    def normalizeLocation(self, location):
        # scale this location based on the axes
        # accept only values for the axes that we have definitions for
        # only normalise if we're valid?
        # normalise anisotropic cooordinates to isotropic.
        # copied from fontTools.varlib.models.normalizeLocation
        new = {}
        for axis in self.axes:
            if not axis.name in location:
                # skipping this dimension it seems
                continue
            v = location.get(axis.name, axis.default)
            if type(v)==tuple:
                v = v[0]
            if v == axis.default:
                v = 0.0
            elif v < axis.default:
                if axis.default == axis.minimum:
                    v = 0.0
                else:
                    v = (max(v, axis.minimum) - axis.default) / (axis.default - axis.minimum)
            else:
                if axis.default == axis.maximum:
                    v = 0.0
                else:
                    v = (min(v, axis.maximum) - axis.default) / (axis.maximum - axis.default)
            new[axis.name] = v
        return new

    def normalize(self):
        # scale all the locations of all masters and instances to the -1 - 0 - 1 value.
        # we need the axis data to do the scaling, so we do those last.
        # masters
        for item in self.sources:
            item.location = self.normalizeLocation(item.location)
        # instances
        for item in self.instances:
            # glyph masters for this instance
            for name, glyphData in item.glyphs.items():
                glyphData['instanceLocation'] = self.normalizeLocation(glyphData['instanceLocation'])
                for glyphMaster in glyphData['masters']:
                    glyphMaster['location'] = self.normalizeLocation(glyphMaster['location'])
            item.location = self.normalizeLocation(item.location)
        # now the axes
        for axis in self.axes:
            # scale the map first
            newMap = []
            for inputValue, outputValue in axis.map:
                newOutputValue = self.normalizeLocation({axis.name: outputValue}).get(axis.name)
                newMap.append((inputValue, newOutputValue))
            if newMap:
                axis.map = newMap
            # finally the axis values
            minimum = self.normalizeLocation({axis.name:axis.minimum}).get(axis.name)
            maximum = self.normalizeLocation({axis.name:axis.maximum}).get(axis.name)
            default = self.normalizeLocation({axis.name:axis.default}).get(axis.name)
            # and set them in the axis.minimum
            axis.minimum = minimum
            axis.maximum = maximum
            axis.default = default



if __name__ == "__main__":

    def __removeAxesFromDesignSpace(path):
        # only for testing, so we can make an invalid designspace file
        # without making the designSpaceDocument also support it.
        f = open(path, 'r')
        d = f.read()
        f.close()
        start = d.find("<axes>")
        end = d.find("</axes>")+len("</axes>")
        n = d[0:start] + d[end:]
        f = open(path, 'w')
        f.write(n)
        f.close()

    # print(tagForAxisName('weight'))
    # print(tagForAxisName('width'))
    # print(tagForAxisName('Optical'))
    # print(tagForAxisName('Poids'))
    # print(tagForAxisName('wt'))

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
        >>> # now we have sounrces and instances, but no axes yet. 
        >>> doc.check()
        >>> doc.getAxisOrder()
        ['spooky', 'weight', 'width']
        >>> doc.axes = []   # clear the axes
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

    def testNormalise():
        """
        >>> doc = DesignSpaceDocument()
        >>> # write some axes
        >>> a1 = AxisDescriptor()
        >>> a1.minimum = -1000
        >>> a1.maximum = 1000
        >>> a1.default = 0
        >>> a1.name = "aaa"
        >>> doc.addAxis(a1)

        >>> doc.normalizeLocation(dict(aaa=0))
        {'aaa': 0.0}
        >>> doc.normalizeLocation(dict(aaa=1000))
        {'aaa': 1.0}
        >>> # clipping beyond max values:
        >>> doc.normalizeLocation(dict(aaa=1001))
        {'aaa': 1.0}
        >>> doc.normalizeLocation(dict(aaa=500))
        {'aaa': 0.5}
        >>> doc.normalizeLocation(dict(aaa=-1000))
        {'aaa': -1.0}
        >>> doc.normalizeLocation(dict(aaa=-1001))
        {'aaa': -1.0}
        >>> # anisotropic coordinates normalise to isotropic
        >>> doc.normalizeLocation(dict(aaa=(1000,-1000)))
        {'aaa': 1.0}
        >>> doc.normalize()
        >>> r = []
        >>> for axis in doc.axes:
        ...     r.append((axis.name, axis.minimum, axis.default, axis.maximum))
        >>> r.sort()
        >>> r
        [('aaa', -1.0, 0.0, 1.0)]

        >>> doc = DesignSpaceDocument()
        >>> # write some axes
        >>> a2 = AxisDescriptor()
        >>> a2.minimum = 100
        >>> a2.maximum = 1000
        >>> a2.default = 100
        >>> a2.name = "bbb"
        >>> doc.addAxis(a2)
        >>> doc.normalizeLocation(dict(bbb=0))
        {'bbb': 0.0}
        >>> doc.normalizeLocation(dict(bbb=1000))
        {'bbb': 1.0}
        >>> # clipping beyond max values:
        >>> doc.normalizeLocation(dict(bbb=1001))
        {'bbb': 1.0}
        >>> doc.normalizeLocation(dict(bbb=500))
        {'bbb': 0.4444444444444444}
        >>> doc.normalizeLocation(dict(bbb=-1000))
        {'bbb': 0.0}
        >>> doc.normalizeLocation(dict(bbb=-1001))
        {'bbb': 0.0}
        >>> # anisotropic coordinates normalise to isotropic
        >>> doc.normalizeLocation(dict(bbb=(1000,-1000)))
        {'bbb': 1.0}
        >>> doc.normalizeLocation(dict(bbb=1001))
        {'bbb': 1.0}
        >>> doc.normalize()
        >>> r = []
        >>> for axis in doc.axes:
        ...     r.append((axis.name, axis.minimum, axis.default, axis.maximum))
        >>> r.sort()
        >>> r
        [('bbb', 0.0, 0.0, 1.0)]

        >>> doc = DesignSpaceDocument()
        >>> # write some axes
        >>> a3 = AxisDescriptor()
        >>> a3.minimum = -1000
        >>> a3.maximum = 0
        >>> a3.default = 0
        >>> a3.name = "ccc"
        >>> doc.addAxis(a3)
        >>> doc.normalizeLocation(dict(ccc=0))
        {'ccc': 0.0}
        >>> doc.normalizeLocation(dict(ccc=1))
        {'ccc': 0.0}
        >>> doc.normalizeLocation(dict(ccc=-1000))
        {'ccc': -1.0}
        >>> doc.normalizeLocation(dict(ccc=-1001))
        {'ccc': -1.0}

        >>> doc.normalize()
        >>> r = []
        >>> for axis in doc.axes:
        ...     r.append((axis.name, axis.minimum, axis.default, axis.maximum))
        >>> r.sort()
        >>> r
        [('ccc', -1.0, 0.0, 0.0)]

        >>> doc = DesignSpaceDocument()
        >>> # write some axes
        >>> a4 = AxisDescriptor()
        >>> a4.minimum = 0
        >>> a4.maximum = 1000
        >>> a4.default = 0
        >>> a4.name = "ddd"
        >>> a4.map = [(0,100), (300, 500), (600, 500), (1000,900)]
        >>> doc.addAxis(a4)
        >>> doc.normalize()
        >>> r = []
        >>> for axis in doc.axes:
        ...     r.append((axis.name, axis.map))
        >>> r.sort()
        >>> r
        [('ddd', [(0, 0.1), (300, 0.5), (600, 0.5), (1000, 0.9)])]


        """

    def testCheck():
        """
        >>> # check if the checks are checking
        >>> testDocPath = os.path.join(os.getcwd(), "testCheck.designspace")
        >>> masterPath1 = os.path.join(os.getcwd(), "masters", "masterTest1.ufo")
        >>> masterPath2 = os.path.join(os.getcwd(), "masters", "masterTest2.ufo")
        >>> instancePath1 = os.path.join(os.getcwd(), "instances", "instanceTest1.ufo")
        >>> instancePath2 = os.path.join(os.getcwd(), "instances", "instanceTest2.ufo")
        
        >>> # no default selected
        >>> doc = DesignSpaceDocument()
        >>> # add master 1
        >>> s1 = SourceDescriptor()
        >>> s1.path = masterPath1
        >>> s1.name = "master.ufo1"
        >>> s1.location = dict(snap=0, pop=10)
        >>> s1.familyName = "MasterFamilyName"
        >>> s1.styleName = "MasterStyleNameOne"
        >>> doc.addSource(s1)
        >>> # add master 2
        >>> s2 = SourceDescriptor()
        >>> s2.path = masterPath2
        >>> s2.name = "master.ufo2"
        >>> s2.location = dict(snap=1000, pop=20)
        >>> s2.familyName = "MasterFamilyName"
        >>> s2.styleName = "MasterStyleNameTwo"
        >>> doc.addSource(s2)
        >>> doc.checkAxes()
        >>> doc.getAxisOrder()
        ['snap', 'pop']
        >>> assert doc.default == None
        >>> doc.checkDefault()
        >>> doc.default.name
        'master.ufo1'

        >>> # default selected
        >>> doc = DesignSpaceDocument()
        >>> # add master 1
        >>> s1 = SourceDescriptor()
        >>> s1.path = masterPath1
        >>> s1.name = "master.ufo1"
        >>> s1.location = dict(snap=0, pop=10)
        >>> s1.familyName = "MasterFamilyName"
        >>> s1.styleName = "MasterStyleNameOne"
        >>> doc.addSource(s1)
        >>> # add master 2
        >>> s2 = SourceDescriptor()
        >>> s2.path = masterPath2
        >>> s2.name = "master.ufo2"
        >>> s2.copyInfo = True
        >>> s2.location = dict(snap=1000, pop=20)
        >>> s2.familyName = "MasterFamilyName"
        >>> s2.styleName = "MasterStyleNameTwo"
        >>> doc.addSource(s2)
        >>> doc.checkAxes()
        >>> doc.getAxisOrder()
        ['snap', 'pop']
        >>> assert doc.default == None
        >>> doc.checkDefault()
        >>> doc.default.name
        'master.ufo2'

        >>> # generate a doc without axes, save and read again
        >>> doc = DesignSpaceDocument()
        >>> # add master 1
        >>> s1 = SourceDescriptor()
        >>> s1.path = masterPath1
        >>> s1.name = "master.ufo1"
        >>> s1.location = dict(snap=0, pop=10)
        >>> s1.familyName = "MasterFamilyName"
        >>> s1.styleName = "MasterStyleNameOne"
        >>> doc.addSource(s1)
        >>> # add master 2
        >>> s2 = SourceDescriptor()
        >>> s2.path = masterPath2
        >>> s2.name = "master.ufo2"
        >>> s2.location = dict(snap=1000, pop=20)
        >>> s2.familyName = "MasterFamilyName"
        >>> s2.styleName = "MasterStyleNameTwo"
        >>> doc.addSource(s2)
        >>> doc.checkAxes()
        >>> doc.write(testDocPath)
        >>> __removeAxesFromDesignSpace(testDocPath)

        >>> new = DesignSpaceDocument()
        >>> new.read(testDocPath)
        >>> new.axes
        []
        >>> new.checkAxes()
        >>> len(new.axes)
        2
        >>> new.write(testDocPath)

        """

    p = "testCheck.designspace"
    __removeAxesFromDesignSpace(p)
    def _test():
        import doctest
        doctest.testmod()
    _test()
