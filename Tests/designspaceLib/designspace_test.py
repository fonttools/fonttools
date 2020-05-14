# coding=utf-8

import os
import sys
import pytest
import warnings

from fontTools.misc.py23 import open
from fontTools.misc import plistlib
from fontTools.designspaceLib import (
    DesignSpaceDocument, SourceDescriptor, AxisDescriptor, RuleDescriptor,
    InstanceDescriptor, evaluateRule, processRules, posix, DesignSpaceDocumentError)
from fontTools import ttLib

def _axesAsDict(axes):
    """
        Make the axis data we have available in
    """
    axesDict = {}
    for axisDescriptor in axes:
        d = {
            'name': axisDescriptor.name,
            'tag': axisDescriptor.tag,
            'minimum': axisDescriptor.minimum,
            'maximum': axisDescriptor.maximum,
            'default': axisDescriptor.default,
            'map': axisDescriptor.map,
        }
        axesDict[axisDescriptor.name] = d
    return axesDict


def assert_equals_test_file(path, test_filename):
    with open(path) as fp:
        actual = fp.read()

    test_path = os.path.join(os.path.dirname(__file__), test_filename)
    with open(test_path) as fp:
        expected = fp.read()

    assert actual == expected


def test_fill_document(tmpdir):
    tmpdir = str(tmpdir)
    testDocPath = os.path.join(tmpdir, "test.designspace")
    masterPath1 = os.path.join(tmpdir, "masters", "masterTest1.ufo")
    masterPath2 = os.path.join(tmpdir, "masters", "masterTest2.ufo")
    instancePath1 = os.path.join(tmpdir, "instances", "instanceTest1.ufo")
    instancePath2 = os.path.join(tmpdir, "instances", "instanceTest2.ufo")
    doc = DesignSpaceDocument()
    doc.rulesProcessingLast = True

    # write some axes
    a1 = AxisDescriptor()
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0
    a1.name = "weight"
    a1.tag = "wght"
    # note: just to test the element language, not an actual label name recommendations.
    a1.labelNames[u'fa-IR'] = u"قطر"
    a1.labelNames[u'en'] = u"Wéíght"
    doc.addAxis(a1)
    a2 = AxisDescriptor()
    a2.minimum = 0
    a2.maximum = 1000
    a2.default = 15
    a2.name = "width"
    a2.tag = "wdth"
    a2.map = [(0.0, 10.0), (15.0, 20.0), (401.0, 66.0), (1000.0, 990.0)]
    a2.hidden = True
    a2.labelNames[u'fr'] = u"Chasse"
    doc.addAxis(a2)

    # add master 1
    s1 = SourceDescriptor()
    s1.filename = os.path.relpath(masterPath1, os.path.dirname(testDocPath))
    assert s1.font is None
    s1.name = "master.ufo1"
    s1.copyLib = True
    s1.copyInfo = True
    s1.copyFeatures = True
    s1.location = dict(weight=0)
    s1.familyName = "MasterFamilyName"
    s1.styleName = "MasterStyleNameOne"
    s1.mutedGlyphNames.append("A")
    s1.mutedGlyphNames.append("Z")
    doc.addSource(s1)
    # add master 2
    s2 = SourceDescriptor()
    s2.filename = os.path.relpath(masterPath2, os.path.dirname(testDocPath))
    s2.name = "master.ufo2"
    s2.copyLib = False
    s2.copyInfo = False
    s2.copyFeatures = False
    s2.muteKerning = True
    s2.location = dict(weight=1000)
    s2.familyName = "MasterFamilyName"
    s2.styleName = "MasterStyleNameTwo"
    doc.addSource(s2)
    # add master 3 from a different layer
    s3 = SourceDescriptor()
    s3.filename = os.path.relpath(masterPath2, os.path.dirname(testDocPath))
    s3.name = "master.ufo2"
    s3.copyLib = False
    s3.copyInfo = False
    s3.copyFeatures = False
    s3.muteKerning = False
    s3.layerName = "supports"
    s3.location = dict(weight=1000)
    s3.familyName = "MasterFamilyName"
    s3.styleName = "Supports"
    doc.addSource(s3)
    # add instance 1
    i1 = InstanceDescriptor()
    i1.filename = os.path.relpath(instancePath1, os.path.dirname(testDocPath))
    i1.familyName = "InstanceFamilyName"
    i1.styleName = "InstanceStyleName"
    i1.name = "instance.ufo1"
    i1.location = dict(weight=500, spooky=666)  # this adds a dimension that is not defined.
    i1.postScriptFontName = "InstancePostscriptName"
    i1.styleMapFamilyName = "InstanceStyleMapFamilyName"
    i1.styleMapStyleName = "InstanceStyleMapStyleName"
    glyphData = dict(name="arrow", mute=True, unicodes=[0x123, 0x124, 0x125])
    i1.glyphs['arrow'] = glyphData
    i1.lib['com.coolDesignspaceApp.binaryData'] = plistlib.Data(b'<binary gunk>')
    i1.lib['com.coolDesignspaceApp.specimenText'] = "Hamburgerwhatever"
    doc.addInstance(i1)
    # add instance 2
    i2 = InstanceDescriptor()
    i2.filename = os.path.relpath(instancePath2, os.path.dirname(testDocPath))
    i2.familyName = "InstanceFamilyName"
    i2.styleName = "InstanceStyleName"
    i2.name = "instance.ufo2"
    # anisotropic location
    i2.location = dict(weight=500, width=(400,300))
    i2.postScriptFontName = "InstancePostscriptName"
    i2.styleMapFamilyName = "InstanceStyleMapFamilyName"
    i2.styleMapStyleName = "InstanceStyleMapStyleName"
    glyphMasters = [dict(font="master.ufo1", glyphName="BB", location=dict(width=20,weight=20)), dict(font="master.ufo2", glyphName="CC", location=dict(width=900,weight=900))]
    glyphData = dict(name="arrow", unicodes=[101, 201, 301])
    glyphData['masters'] = glyphMasters
    glyphData['note'] = "A note about this glyph"
    glyphData['instanceLocation'] = dict(width=100, weight=120)
    i2.glyphs['arrow'] = glyphData
    i2.glyphs['arrow2'] = dict(mute=False)
    doc.addInstance(i2)

    doc.filename = "suggestedFileName.designspace"
    doc.lib['com.coolDesignspaceApp.previewSize'] = 30

    # write some rules
    r1 = RuleDescriptor()
    r1.name = "named.rule.1"
    r1.conditionSets.append([
        dict(name='axisName_a', minimum=0, maximum=1),
        dict(name='axisName_b', minimum=2, maximum=3)
    ])
    r1.subs.append(("a", "a.alt"))
    doc.addRule(r1)
    # write the document
    doc.write(testDocPath)
    assert os.path.exists(testDocPath)
    assert_equals_test_file(testDocPath, 'data/test.designspace')
    # import it again
    new = DesignSpaceDocument()
    new.read(testDocPath)

    assert new.default.location == {'width': 20.0, 'weight': 0.0}
    assert new.filename == 'test.designspace'
    assert new.lib == doc.lib
    assert new.instances[0].lib == doc.instances[0].lib

    # test roundtrip for the axis attributes and data
    axes = {}
    for axis in doc.axes:
        if axis.tag not in axes:
            axes[axis.tag] = []
        axes[axis.tag].append(axis.serialize())
    for axis in new.axes:
        if axis.tag[0] == "_":
            continue
        if axis.tag not in axes:
            axes[axis.tag] = []
        axes[axis.tag].append(axis.serialize())
    for v in axes.values():
        a, b = v
        assert a == b


def test_unicodes(tmpdir):
    tmpdir = str(tmpdir)
    testDocPath = os.path.join(tmpdir, "testUnicodes.designspace")
    testDocPath2 = os.path.join(tmpdir, "testUnicodes_roundtrip.designspace")
    masterPath1 = os.path.join(tmpdir, "masters", "masterTest1.ufo")
    masterPath2 = os.path.join(tmpdir, "masters", "masterTest2.ufo")
    instancePath1 = os.path.join(tmpdir, "instances", "instanceTest1.ufo")
    instancePath2 = os.path.join(tmpdir, "instances", "instanceTest2.ufo")
    doc = DesignSpaceDocument()
    # add master 1
    s1 = SourceDescriptor()
    s1.filename = os.path.relpath(masterPath1, os.path.dirname(testDocPath))
    s1.name = "master.ufo1"
    s1.copyInfo = True
    s1.location = dict(weight=0)
    doc.addSource(s1)
    # add master 2
    s2 = SourceDescriptor()
    s2.filename = os.path.relpath(masterPath2, os.path.dirname(testDocPath))
    s2.name = "master.ufo2"
    s2.location = dict(weight=1000)
    doc.addSource(s2)
    # add instance 1
    i1 = InstanceDescriptor()
    i1.filename = os.path.relpath(instancePath1, os.path.dirname(testDocPath))
    i1.name = "instance.ufo1"
    i1.location = dict(weight=500)
    glyphData = dict(name="arrow", mute=True, unicodes=[100, 200, 300])
    i1.glyphs['arrow'] = glyphData
    doc.addInstance(i1)
    # now we have sources and instances, but no axes yet.
    doc.axes = []   # clear the axes
    # write some axes
    a1 = AxisDescriptor()
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0
    a1.name = "weight"
    a1.tag = "wght"
    doc.addAxis(a1)
    # write the document
    doc.write(testDocPath)
    assert os.path.exists(testDocPath)
    # import it again
    new = DesignSpaceDocument()
    new.read(testDocPath)
    new.write(testDocPath2)
    # compare the file contents
    with open(testDocPath, 'r', encoding='utf-8') as f1:
        t1 = f1.read()
    with open(testDocPath2, 'r', encoding='utf-8') as f2:
        t2 = f2.read()
    assert t1 == t2
    # check the unicode values read from the document
    assert new.instances[0].glyphs['arrow']['unicodes'] == [100,200,300]


def test_localisedNames(tmpdir):
    tmpdir = str(tmpdir)
    testDocPath = os.path.join(tmpdir, "testLocalisedNames.designspace")
    testDocPath2 = os.path.join(tmpdir, "testLocalisedNames_roundtrip.designspace")
    masterPath1 = os.path.join(tmpdir, "masters", "masterTest1.ufo")
    masterPath2 = os.path.join(tmpdir, "masters", "masterTest2.ufo")
    instancePath1 = os.path.join(tmpdir, "instances", "instanceTest1.ufo")
    instancePath2 = os.path.join(tmpdir, "instances", "instanceTest2.ufo")
    doc = DesignSpaceDocument()
    # add master 1
    s1 = SourceDescriptor()
    s1.filename = os.path.relpath(masterPath1, os.path.dirname(testDocPath))
    s1.name = "master.ufo1"
    s1.copyInfo = True
    s1.location = dict(weight=0)
    doc.addSource(s1)
    # add master 2
    s2 = SourceDescriptor()
    s2.filename = os.path.relpath(masterPath2, os.path.dirname(testDocPath))
    s2.name = "master.ufo2"
    s2.location = dict(weight=1000)
    doc.addSource(s2)
    # add instance 1
    i1 = InstanceDescriptor()
    i1.filename = os.path.relpath(instancePath1, os.path.dirname(testDocPath))
    i1.familyName = "Montserrat"
    i1.styleName = "SemiBold"
    i1.styleMapFamilyName = "Montserrat SemiBold"
    i1.styleMapStyleName = "Regular"
    i1.setFamilyName("Montserrat", "fr")
    i1.setFamilyName(u"モンセラート", "ja")
    i1.setStyleName("Demigras", "fr")
    i1.setStyleName(u"半ば", "ja")
    i1.setStyleMapStyleName(u"Standard", "de")
    i1.setStyleMapFamilyName("Montserrat Halbfett", "de")
    i1.setStyleMapFamilyName(u"モンセラート SemiBold", "ja")
    i1.name = "instance.ufo1"
    i1.location = dict(weight=500, spooky=666)  # this adds a dimension that is not defined.
    i1.postScriptFontName = "InstancePostscriptName"
    glyphData = dict(name="arrow", mute=True, unicodes=[0x123])
    i1.glyphs['arrow'] = glyphData
    doc.addInstance(i1)
    # now we have sources and instances, but no axes yet.
    doc.axes = []   # clear the axes
    # write some axes
    a1 = AxisDescriptor()
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0
    a1.name = "weight"
    a1.tag = "wght"
    # note: just to test the element language, not an actual label name recommendations.
    a1.labelNames[u'fa-IR'] = u"قطر"
    a1.labelNames[u'en'] = u"Wéíght"
    doc.addAxis(a1)
    a2 = AxisDescriptor()
    a2.minimum = 0
    a2.maximum = 1000
    a2.default = 0
    a2.name = "width"
    a2.tag = "wdth"
    a2.map = [(0.0, 10.0), (401.0, 66.0), (1000.0, 990.0)]
    a2.labelNames[u'fr'] = u"Poids"
    doc.addAxis(a2)
    # add an axis that is not part of any location to see if that works
    a3 = AxisDescriptor()
    a3.minimum = 333
    a3.maximum = 666
    a3.default = 444
    a3.name = "spooky"
    a3.tag = "spok"
    a3.map = [(0.0, 10.0), (401.0, 66.0), (1000.0, 990.0)]
    #doc.addAxis(a3)    # uncomment this line to test the effects of default axes values
    # write some rules
    r1 = RuleDescriptor()
    r1.name = "named.rule.1"
    r1.conditionSets.append([
        dict(name='weight', minimum=200, maximum=500),
        dict(name='width', minimum=0, maximum=150)
    ])
    r1.subs.append(("a", "a.alt"))
    doc.addRule(r1)
    # write the document
    doc.write(testDocPath)
    assert os.path.exists(testDocPath)
    # import it again
    new = DesignSpaceDocument()
    new.read(testDocPath)
    new.write(testDocPath2)
    with open(testDocPath, 'r', encoding='utf-8') as f1:
        t1 = f1.read()
    with open(testDocPath2, 'r', encoding='utf-8') as f2:
        t2 = f2.read()
    assert t1 == t2


def test_handleNoAxes(tmpdir):
    tmpdir = str(tmpdir)
    # test what happens if the designspacedocument has no axes element.
    testDocPath = os.path.join(tmpdir, "testNoAxes_source.designspace")
    testDocPath2 = os.path.join(tmpdir, "testNoAxes_recontructed.designspace")
    masterPath1 = os.path.join(tmpdir, "masters", "masterTest1.ufo")
    masterPath2 = os.path.join(tmpdir, "masters", "masterTest2.ufo")
    instancePath1 = os.path.join(tmpdir, "instances", "instanceTest1.ufo")
    instancePath2 = os.path.join(tmpdir, "instances", "instanceTest2.ufo")

    # Case 1: No axes element in the document, but there are sources and instances
    doc = DesignSpaceDocument()

    for name, value in [('One', 1),('Two', 2),('Three', 3)]:
        a = AxisDescriptor()
        a.minimum = 0
        a.maximum = 1000
        a.default = 0
        a.name = "axisName%s" % (name)
        a.tag = "ax_%d" % (value)
        doc.addAxis(a)

    # add master 1
    s1 = SourceDescriptor()
    s1.filename = os.path.relpath(masterPath1, os.path.dirname(testDocPath))
    s1.name = "master.ufo1"
    s1.copyLib = True
    s1.copyInfo = True
    s1.copyFeatures = True
    s1.location = dict(axisNameOne=-1000, axisNameTwo=0, axisNameThree=1000)
    s1.familyName = "MasterFamilyName"
    s1.styleName = "MasterStyleNameOne"
    doc.addSource(s1)

    # add master 2
    s2 = SourceDescriptor()
    s2.filename = os.path.relpath(masterPath2, os.path.dirname(testDocPath))
    s2.name = "master.ufo1"
    s2.copyLib = False
    s2.copyInfo = False
    s2.copyFeatures = False
    s2.location = dict(axisNameOne=1000, axisNameTwo=1000, axisNameThree=0)
    s2.familyName = "MasterFamilyName"
    s2.styleName = "MasterStyleNameTwo"
    doc.addSource(s2)

    # add instance 1
    i1 = InstanceDescriptor()
    i1.filename = os.path.relpath(instancePath1, os.path.dirname(testDocPath))
    i1.familyName = "InstanceFamilyName"
    i1.styleName = "InstanceStyleName"
    i1.name = "instance.ufo1"
    i1.location = dict(axisNameOne=(-1000,500), axisNameTwo=100)
    i1.postScriptFontName = "InstancePostscriptName"
    i1.styleMapFamilyName = "InstanceStyleMapFamilyName"
    i1.styleMapStyleName = "InstanceStyleMapStyleName"
    doc.addInstance(i1)

    doc.write(testDocPath)
    verify = DesignSpaceDocument()
    verify.read(testDocPath)
    verify.write(testDocPath2)

def test_pathNameResolve(tmpdir):
    tmpdir = str(tmpdir)
    # test how descriptor.path and descriptor.filename are resolved
    testDocPath1 = os.path.join(tmpdir, "testPathName_case1.designspace")
    testDocPath2 = os.path.join(tmpdir, "testPathName_case2.designspace")
    testDocPath3 = os.path.join(tmpdir, "testPathName_case3.designspace")
    testDocPath4 = os.path.join(tmpdir, "testPathName_case4.designspace")
    testDocPath5 = os.path.join(tmpdir, "testPathName_case5.designspace")
    testDocPath6 = os.path.join(tmpdir, "testPathName_case6.designspace")
    masterPath1 = os.path.join(tmpdir, "masters", "masterTest1.ufo")
    masterPath2 = os.path.join(tmpdir, "masters", "masterTest2.ufo")
    instancePath1 = os.path.join(tmpdir, "instances", "instanceTest1.ufo")
    instancePath2 = os.path.join(tmpdir, "instances", "instanceTest2.ufo")

    a1 = AxisDescriptor()
    a1.tag = "TAGA"
    a1.name = "axisName_a"
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0

    # Case 1: filename and path are both empty. Nothing to calculate, nothing to put in the file.
    doc = DesignSpaceDocument()
    doc.addAxis(a1)
    s = SourceDescriptor()
    s.filename = None
    s.path = None
    s.copyInfo = True
    s.location = dict(weight=0)
    s.familyName = "MasterFamilyName"
    s.styleName = "MasterStyleNameOne"
    doc.addSource(s)
    doc.write(testDocPath1)
    verify = DesignSpaceDocument()
    verify.read(testDocPath1)
    assert verify.sources[0].filename == None
    assert verify.sources[0].path == None

    # Case 2: filename is empty, path points somewhere: calculate a new filename.
    doc = DesignSpaceDocument()
    doc.addAxis(a1)
    s = SourceDescriptor()
    s.filename = None
    s.path = masterPath1
    s.copyInfo = True
    s.location = dict(weight=0)
    s.familyName = "MasterFamilyName"
    s.styleName = "MasterStyleNameOne"
    doc.addSource(s)
    doc.write(testDocPath2)
    verify = DesignSpaceDocument()
    verify.read(testDocPath2)
    assert verify.sources[0].filename == "masters/masterTest1.ufo"
    assert verify.sources[0].path == posix(masterPath1)

    # Case 3: the filename is set, the path is None.
    doc = DesignSpaceDocument()
    doc.addAxis(a1)
    s = SourceDescriptor()
    s.filename = "../somewhere/over/the/rainbow.ufo"
    s.path = None
    s.copyInfo = True
    s.location = dict(weight=0)
    s.familyName = "MasterFamilyName"
    s.styleName = "MasterStyleNameOne"
    doc.addSource(s)
    doc.write(testDocPath3)
    verify = DesignSpaceDocument()
    verify.read(testDocPath3)
    assert verify.sources[0].filename == "../somewhere/over/the/rainbow.ufo"
    # make the absolute path for filename so we can see if it matches the path
    p = os.path.abspath(os.path.join(os.path.dirname(testDocPath3), verify.sources[0].filename))
    assert verify.sources[0].path == posix(p)

    # Case 4: the filename points to one file, the path points to another. The path takes precedence.
    doc = DesignSpaceDocument()
    doc.addAxis(a1)
    s = SourceDescriptor()
    s.filename = "../somewhere/over/the/rainbow.ufo"
    s.path = masterPath1
    s.copyInfo = True
    s.location = dict(weight=0)
    s.familyName = "MasterFamilyName"
    s.styleName = "MasterStyleNameOne"
    doc.addSource(s)
    doc.write(testDocPath4)
    verify = DesignSpaceDocument()
    verify.read(testDocPath4)
    assert verify.sources[0].filename == "masters/masterTest1.ufo"

    # Case 5: the filename is None, path has a value, update the filename
    doc = DesignSpaceDocument()
    doc.addAxis(a1)
    s = SourceDescriptor()
    s.filename = None
    s.path = masterPath1
    s.copyInfo = True
    s.location = dict(weight=0)
    s.familyName = "MasterFamilyName"
    s.styleName = "MasterStyleNameOne"
    doc.addSource(s)
    doc.write(testDocPath5) # so that the document has a path
    doc.updateFilenameFromPath()
    assert doc.sources[0].filename == "masters/masterTest1.ufo"

    # Case 6: the filename has a value, path has a value, update the filenames with force
    doc = DesignSpaceDocument()
    doc.addAxis(a1)
    s = SourceDescriptor()
    s.filename = "../somewhere/over/the/rainbow.ufo"
    s.path = masterPath1
    s.copyInfo = True
    s.location = dict(weight=0)
    s.familyName = "MasterFamilyName"
    s.styleName = "MasterStyleNameOne"
    doc.write(testDocPath5) # so that the document has a path
    doc.addSource(s)
    assert doc.sources[0].filename == "../somewhere/over/the/rainbow.ufo"
    doc.updateFilenameFromPath(force=True)
    assert doc.sources[0].filename == "masters/masterTest1.ufo"


def test_normalise1():
    # normalisation of anisotropic locations, clipping
    doc = DesignSpaceDocument()
    # write some axes
    a1 = AxisDescriptor()
    a1.minimum = -1000
    a1.maximum = 1000
    a1.default = 0
    a1.name = "axisName_a"
    a1.tag = "TAGA"
    doc.addAxis(a1)
    assert doc.normalizeLocation(dict(axisName_a=0)) == {'axisName_a': 0.0}
    assert doc.normalizeLocation(dict(axisName_a=1000)) == {'axisName_a': 1.0}
    # clipping beyond max values:
    assert doc.normalizeLocation(dict(axisName_a=1001)) == {'axisName_a': 1.0}
    assert doc.normalizeLocation(dict(axisName_a=500)) == {'axisName_a': 0.5}
    assert doc.normalizeLocation(dict(axisName_a=-1000)) == {'axisName_a': -1.0}
    assert doc.normalizeLocation(dict(axisName_a=-1001)) == {'axisName_a': -1.0}
    # anisotropic coordinates normalise to isotropic
    assert doc.normalizeLocation(dict(axisName_a=(1000, -1000))) == {'axisName_a': 1.0}
    doc.normalize()
    r = []
    for axis in doc.axes:
        r.append((axis.name, axis.minimum, axis.default, axis.maximum))
    r.sort()
    assert r == [('axisName_a', -1.0, 0.0, 1.0)]

def test_normalise2():
    # normalisation with minimum > 0
    doc = DesignSpaceDocument()
    # write some axes
    a2 = AxisDescriptor()
    a2.minimum = 100
    a2.maximum = 1000
    a2.default = 100
    a2.name = "axisName_b"
    doc.addAxis(a2)
    assert doc.normalizeLocation(dict(axisName_b=0)) == {'axisName_b': 0.0}
    assert doc.normalizeLocation(dict(axisName_b=1000)) == {'axisName_b': 1.0}
    # clipping beyond max values:
    assert doc.normalizeLocation(dict(axisName_b=1001)) == {'axisName_b': 1.0}
    assert doc.normalizeLocation(dict(axisName_b=500)) == {'axisName_b': 0.4444444444444444}
    assert doc.normalizeLocation(dict(axisName_b=-1000)) == {'axisName_b': 0.0}
    assert doc.normalizeLocation(dict(axisName_b=-1001)) == {'axisName_b': 0.0}
    # anisotropic coordinates normalise to isotropic
    assert doc.normalizeLocation(dict(axisName_b=(1000,-1000))) == {'axisName_b': 1.0}
    assert doc.normalizeLocation(dict(axisName_b=1001)) == {'axisName_b': 1.0}
    doc.normalize()
    r = []
    for axis in doc.axes:
        r.append((axis.name, axis.minimum, axis.default, axis.maximum))
    r.sort()
    assert r == [('axisName_b', 0.0, 0.0, 1.0)]

def test_normalise3():
    # normalisation of negative values, with default == maximum
    doc = DesignSpaceDocument()
    # write some axes
    a3 = AxisDescriptor()
    a3.minimum = -1000
    a3.maximum = 0
    a3.default = 0
    a3.name = "ccc"
    doc.addAxis(a3)
    assert doc.normalizeLocation(dict(ccc=0)) == {'ccc': 0.0}
    assert doc.normalizeLocation(dict(ccc=1)) == {'ccc': 0.0}
    assert doc.normalizeLocation(dict(ccc=-1000)) == {'ccc': -1.0}
    assert doc.normalizeLocation(dict(ccc=-1001)) == {'ccc': -1.0}
    doc.normalize()
    r = []
    for axis in doc.axes:
        r.append((axis.name, axis.minimum, axis.default, axis.maximum))
    r.sort()
    assert r == [('ccc', -1.0, 0.0, 0.0)]

def test_normalise4():
    # normalisation with a map
    doc = DesignSpaceDocument()
    # write some axes
    a4 = AxisDescriptor()
    a4.minimum = 0
    a4.maximum = 1000
    a4.default = 0
    a4.name = "ddd"
    a4.map = [(0,100), (300, 500), (600, 500), (1000,900)]
    doc.addAxis(a4)
    doc.normalize()
    r = []
    for axis in doc.axes:
        r.append((axis.name, axis.map))
    r.sort()
    assert r == [('ddd', [(0, 0.0), (300, 0.5), (600, 0.5), (1000, 1.0)])]

def test_axisMapping():
    # note: because designspance lib does not do any actual
    # processing of the mapping data, we can only check if there data is there.
    doc = DesignSpaceDocument()
    # write some axes
    a4 = AxisDescriptor()
    a4.minimum = 0
    a4.maximum = 1000
    a4.default = 0
    a4.name = "ddd"
    a4.map = [(0,100), (300, 500), (600, 500), (1000,900)]
    doc.addAxis(a4)
    doc.normalize()
    r = []
    for axis in doc.axes:
        r.append((axis.name, axis.map))
    r.sort()
    assert r == [('ddd', [(0, 0.0), (300, 0.5), (600, 0.5), (1000, 1.0)])]

def test_rulesConditions(tmpdir):
    # tests of rules, conditionsets and conditions
    r1 = RuleDescriptor()
    r1.name = "named.rule.1"
    r1.conditionSets.append([
        dict(name='axisName_a', minimum=0, maximum=1000),
        dict(name='axisName_b', minimum=0, maximum=3000)
    ])
    r1.subs.append(("a", "a.alt"))

    assert evaluateRule(r1, dict(axisName_a = 500, axisName_b = 0)) == True
    assert evaluateRule(r1, dict(axisName_a = 0, axisName_b = 0)) == True
    assert evaluateRule(r1, dict(axisName_a = 1000, axisName_b = 0)) == True
    assert evaluateRule(r1, dict(axisName_a = 1000, axisName_b = -100)) == False
    assert evaluateRule(r1, dict(axisName_a = 1000.0001, axisName_b = 0)) == False
    assert evaluateRule(r1, dict(axisName_a = -0.0001, axisName_b = 0)) == False
    assert evaluateRule(r1, dict(axisName_a = -100, axisName_b = 0)) == False
    assert processRules([r1], dict(axisName_a = 500, axisName_b = 0), ["a", "b", "c"]) == ['a.alt', 'b', 'c']
    assert processRules([r1], dict(axisName_a = 500, axisName_b = 0), ["a.alt", "b", "c"]) == ['a.alt', 'b', 'c']
    assert processRules([r1], dict(axisName_a = 2000, axisName_b = 0), ["a", "b", "c"]) == ['a', 'b', 'c']

    # rule with only a maximum
    r2 = RuleDescriptor()
    r2.name = "named.rule.2"
    r2.conditionSets.append([dict(name='axisName_a', maximum=500)])
    r2.subs.append(("b", "b.alt"))

    assert evaluateRule(r2, dict(axisName_a = 0)) == True
    assert evaluateRule(r2, dict(axisName_a = -500)) == True
    assert evaluateRule(r2, dict(axisName_a = 1000)) == False

    # rule with only a minimum
    r3 = RuleDescriptor()
    r3.name = "named.rule.3"
    r3.conditionSets.append([dict(name='axisName_a', minimum=500)])
    r3.subs.append(("c", "c.alt"))

    assert evaluateRule(r3, dict(axisName_a = 0)) == False
    assert evaluateRule(r3, dict(axisName_a = 1000)) == True
    assert evaluateRule(r3, dict(axisName_a = 1000)) == True

    # rule with only a minimum, maximum in separate conditions
    r4 = RuleDescriptor()
    r4.name = "named.rule.4"
    r4.conditionSets.append([
        dict(name='axisName_a', minimum=500),
        dict(name='axisName_b', maximum=500)
    ])
    r4.subs.append(("c", "c.alt"))

    assert evaluateRule(r4, dict(axisName_a = 1000, axisName_b = 0)) == True
    assert evaluateRule(r4, dict(axisName_a = 0, axisName_b = 0)) == False
    assert evaluateRule(r4, dict(axisName_a = 1000, axisName_b = 1000)) == False

def test_rulesDocument(tmpdir):
    # tests of rules in a document, roundtripping.
    tmpdir = str(tmpdir)
    testDocPath = os.path.join(tmpdir, "testRules.designspace")
    testDocPath2 = os.path.join(tmpdir, "testRules_roundtrip.designspace")
    doc = DesignSpaceDocument()
    doc.rulesProcessingLast = True
    a1 = AxisDescriptor()
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0
    a1.name = "axisName_a"
    a1.tag = "TAGA"
    b1 = AxisDescriptor()
    b1.minimum = 2000
    b1.maximum = 3000
    b1.default = 2000
    b1.name = "axisName_b"
    b1.tag = "TAGB"
    doc.addAxis(a1)
    doc.addAxis(b1)
    r1 = RuleDescriptor()
    r1.name = "named.rule.1"
    r1.conditionSets.append([
        dict(name='axisName_a', minimum=0, maximum=1000),
        dict(name='axisName_b', minimum=0, maximum=3000)
    ])
    r1.subs.append(("a", "a.alt"))
    # rule with minium and maximum
    doc.addRule(r1)
    assert len(doc.rules) == 1
    assert len(doc.rules[0].conditionSets) == 1
    assert len(doc.rules[0].conditionSets[0]) == 2
    assert _axesAsDict(doc.axes) == {'axisName_a': {'map': [], 'name': 'axisName_a', 'default': 0, 'minimum': 0, 'maximum': 1000, 'tag': 'TAGA'}, 'axisName_b': {'map': [], 'name': 'axisName_b', 'default': 2000, 'minimum': 2000, 'maximum': 3000, 'tag': 'TAGB'}}
    assert doc.rules[0].conditionSets == [[
        {'minimum': 0, 'maximum': 1000, 'name': 'axisName_a'},
        {'minimum': 0, 'maximum': 3000, 'name': 'axisName_b'}]]
    assert doc.rules[0].subs == [('a', 'a.alt')]
    doc.normalize()
    assert doc.rules[0].name == 'named.rule.1'
    assert doc.rules[0].conditionSets == [[
        {'minimum': 0.0, 'maximum': 1.0, 'name': 'axisName_a'},
        {'minimum': 0.0, 'maximum': 1.0, 'name': 'axisName_b'}]]
    # still one conditionset
    assert len(doc.rules[0].conditionSets) == 1
    doc.write(testDocPath)
    # add a stray conditionset
    _addUnwrappedCondition(testDocPath)
    doc2 = DesignSpaceDocument()
    doc2.read(testDocPath)
    assert doc2.rulesProcessingLast
    assert len(doc2.axes) == 2
    assert len(doc2.rules) == 1
    assert len(doc2.rules[0].conditionSets) == 2
    doc2.write(testDocPath2)
    # verify these results
    # make sure the stray condition is now neatly wrapped in a conditionset.
    doc3 = DesignSpaceDocument()
    doc3.read(testDocPath2)
    assert len(doc3.rules) == 1
    assert len(doc3.rules[0].conditionSets) == 2

def _addUnwrappedCondition(path):
    # only for testing, so we can make an invalid designspace file
    # older designspace files may have conditions that are not wrapped in a conditionset
    # These can be read into a new conditionset.
    with open(path, 'r', encoding='utf-8') as f:
        d = f.read()
    print(d)
    d = d.replace('<rule name="named.rule.1">', '<rule name="named.rule.1">\n\t<condition maximum="22" minimum="33" name="axisName_a" />')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(d)

def test_documentLib(tmpdir):
    # roundtrip test of the document lib with some nested data
    tmpdir = str(tmpdir)
    testDocPath1 = os.path.join(tmpdir, "testDocumentLibTest.designspace")
    doc = DesignSpaceDocument()
    a1 = AxisDescriptor()
    a1.tag = "TAGA"
    a1.name = "axisName_a"
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0
    doc.addAxis(a1)
    dummyData = dict(a=123, b=u"äbc", c=[1,2,3], d={'a':123})
    dummyKey = "org.fontTools.designspaceLib"
    doc.lib = {dummyKey: dummyData}
    doc.write(testDocPath1)
    new = DesignSpaceDocument()
    new.read(testDocPath1)
    assert dummyKey in new.lib
    assert new.lib[dummyKey] == dummyData


def test_updatePaths(tmpdir):
    doc = DesignSpaceDocument()
    doc.path = str(tmpdir / "foo" / "bar" / "MyDesignspace.designspace")

    s1 = SourceDescriptor()
    doc.addSource(s1)

    doc.updatePaths()

    # expect no changes
    assert s1.path is None
    assert s1.filename is None

    name1 = "../masters/Source1.ufo"
    path1 = posix(str(tmpdir / "foo" / "masters" / "Source1.ufo"))

    s1.path = path1
    s1.filename = None

    doc.updatePaths()

    assert s1.path == path1
    assert s1.filename == name1  # empty filename updated

    name2 = "../masters/Source2.ufo"
    s1.filename = name2

    doc.updatePaths()

    # conflicting filename discarded, path always gets precedence
    assert s1.path == path1
    assert s1.filename == "../masters/Source1.ufo"

    s1.path = None
    s1.filename = name2

    doc.updatePaths()

    # expect no changes
    assert s1.path is None
    assert s1.filename == name2


@pytest.mark.skipif(sys.version_info[:2] < (3, 6), reason="pathlib is only tested on 3.6 and up")
def test_read_with_path_object():
    import pathlib
    source = (pathlib.Path(__file__) / "../data/test.designspace").resolve()
    assert source.exists()
    doc = DesignSpaceDocument()
    doc.read(source)


@pytest.mark.skipif(sys.version_info[:2] < (3, 6), reason="pathlib is only tested on 3.6 and up")
def test_with_with_path_object(tmpdir):
    import pathlib
    tmpdir = str(tmpdir)
    dest = pathlib.Path(tmpdir) / "test.designspace"
    doc = DesignSpaceDocument()
    doc.write(dest)
    assert dest.exists()


def test_findDefault_axis_mapping():
    designspace_string = """\
<?xml version='1.0' encoding='UTF-8'?>
<designspace format="4.0">
  <axes>
    <axis tag="wght" name="Weight" minimum="100" maximum="800" default="400">
      <map input="100" output="20"/>
      <map input="300" output="40"/>
      <map input="400" output="80"/>
      <map input="700" output="126"/>
      <map input="800" output="170"/>
    </axis>
    <axis tag="ital" name="Italic" minimum="0" maximum="1" default="1"/>
  </axes>
  <sources>
    <source filename="Font-Light.ufo">
      <location>
        <dimension name="Weight" xvalue="20"/>
        <dimension name="Italic" xvalue="0"/>
      </location>
    </source>
    <source filename="Font-Regular.ufo">
      <location>
        <dimension name="Weight" xvalue="80"/>
        <dimension name="Italic" xvalue="0"/>
      </location>
    </source>
    <source filename="Font-Bold.ufo">
      <location>
        <dimension name="Weight" xvalue="170"/>
        <dimension name="Italic" xvalue="0"/>
      </location>
    </source>
    <source filename="Font-LightItalic.ufo">
      <location>
        <dimension name="Weight" xvalue="20"/>
        <dimension name="Italic" xvalue="1"/>
      </location>
    </source>
    <source filename="Font-Italic.ufo">
      <location>
        <dimension name="Weight" xvalue="80"/>
        <dimension name="Italic" xvalue="1"/>
      </location>
    </source>
    <source filename="Font-BoldItalic.ufo">
      <location>
        <dimension name="Weight" xvalue="170"/>
        <dimension name="Italic" xvalue="1"/>
      </location>
    </source>
  </sources>
</designspace>
    """
    designspace = DesignSpaceDocument.fromstring(designspace_string)
    assert designspace.findDefault().filename == "Font-Italic.ufo"

    designspace.axes[1].default = 0

    assert designspace.findDefault().filename == "Font-Regular.ufo"


def test_loadSourceFonts():

    def opener(path):
        font = ttLib.TTFont()
        font.importXML(path)
        return font

    # this designspace file contains .TTX source paths
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "varLib",
        "data",
        "SparseMasters.designspace"
    )
    designspace = DesignSpaceDocument.fromfile(path)

    # force two source descriptors to have the same path
    designspace.sources[1].path = designspace.sources[0].path

    fonts = designspace.loadSourceFonts(opener)

    assert len(fonts) == 3
    assert all(isinstance(font, ttLib.TTFont) for font in fonts)
    assert fonts[0] is fonts[1]  # same path, identical font object

    fonts2 = designspace.loadSourceFonts(opener)

    for font1, font2 in zip(fonts, fonts2):
        assert font1 is font2


def test_loadSourceFonts_no_required_path():
    designspace = DesignSpaceDocument()
    designspace.sources.append(SourceDescriptor())

    with pytest.raises(DesignSpaceDocumentError, match="no 'path' attribute"):
        designspace.loadSourceFonts(lambda p: p)


def test_addAxisDescriptor():
    ds = DesignSpaceDocument()

    axis = ds.addAxisDescriptor(
      name="Weight", tag="wght", minimum=100, default=400, maximum=900
    )

    assert ds.axes[0] is axis
    assert isinstance(axis, AxisDescriptor)
    assert axis.name == "Weight"
    assert axis.tag == "wght"
    assert axis.minimum == 100
    assert axis.default == 400
    assert axis.maximum == 900


def test_addSourceDescriptor():
    ds = DesignSpaceDocument()

    source = ds.addSourceDescriptor(name="TestSource", location={"Weight": 400})

    assert ds.sources[0] is source
    assert isinstance(source, SourceDescriptor)
    assert source.name == "TestSource"
    assert source.location == {"Weight": 400}


def test_addInstanceDescriptor():
    ds = DesignSpaceDocument()

    instance = ds.addInstanceDescriptor(
      name="TestInstance",
      location={"Weight": 400},
      styleName="Regular",
      styleMapStyleName="regular",
    )

    assert ds.instances[0] is instance
    assert isinstance(instance, InstanceDescriptor)
    assert instance.name == "TestInstance"
    assert instance.location == {"Weight": 400}
    assert instance.styleName == "Regular"
    assert instance.styleMapStyleName == "regular"


def test_addRuleDescriptor(tmp_path):
    ds = DesignSpaceDocument()

    rule = ds.addRuleDescriptor(
        name="TestRule",
        conditionSets=[
            [
                dict(name="Weight", minimum=100, maximum=200),
                dict(name="Weight", minimum=700, maximum=900),
            ]
        ],
        subs=[("a", "a.alt")],
    )

    assert ds.rules[0] is rule
    assert isinstance(rule, RuleDescriptor)
    assert rule.name == "TestRule"
    assert rule.conditionSets == [
        [
            dict(name="Weight", minimum=100, maximum=200),
            dict(name="Weight", minimum=700, maximum=900),
        ]
    ]
    assert rule.subs == [("a", "a.alt")]

    # Test it doesn't crash.
    ds.write(tmp_path / "test.designspace")
