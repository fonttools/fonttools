# coding=utf-8

from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import os
import pytest

from fontTools.misc.py23 import open
from fontTools.designspaceLib import (
    DesignSpaceDocument, SourceDescriptor, AxisDescriptor, RuleDescriptor,
    InstanceDescriptor, evaluateRule, processRules, posix)


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

    # now we have sources and instances, but no axes yet.
    doc.check()

    # Here, since the axes are not defined in the document, but instead are
    # infered from the locations of the instances, we cannot guarantee the
    # order in which they will be created by the `check()` method.
    assert set(doc.getAxisOrder()) == set(['spooky', 'weight', 'width'])
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
    a2.default = 20
    a2.name = "width"
    a2.tag = "wdth"
    a2.map = [(0.0, 10.0), (401.0, 66.0), (1000.0, 990.0)]
    a2.hidden = True
    a2.labelNames[u'fr'] = u"Chasse"
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
    r1.conditions.append(dict(name='aaaa', minimum=0, maximum=1))
    r1.conditions.append(dict(name='bbbb', minimum=2, maximum=3))
    r1.subs.append(("a", "a.alt"))
    doc.addRule(r1)
    # write the document
    doc.write(testDocPath)
    assert os.path.exists(testDocPath)
    assert_equals_test_file(testDocPath, 'data/test.designspace')
    # import it again
    new = DesignSpaceDocument()
    new.read(testDocPath)

    new.check()
    assert new.default.location == {'width': 20.0, 'weight': 0.0}
    assert new.filename == 'test.designspace'
    assert new.lib == doc.lib
    assert new.instances[0].lib == doc.instances[0].lib

    # >>> for a, b in zip(doc.instances, new.instances):
    # ...     a.compare(b)
    # >>> for a, b in zip(doc.sources, new.sources):
    # ...     a.compare(b)
    # >>> for a, b in zip(doc.axes, new.axes):
    # ...     a.compare(b)
    # >>> [n.mutedGlyphNames for n in new.sources]
    # [['A', 'Z'], []]
    # >>> doc.getFonts()
    # []

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


def test_adjustAxisDefaultToNeutral(tmpdir):
    tmpdir = str(tmpdir)
    testDocPath = os.path.join(tmpdir, "testAdjustAxisDefaultToNeutral.designspace")
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
    s1.copyFeatures = True
    s1.location = dict(weight=55, width=1000)
    doc.addSource(s1)
    # write some axes
    a1 = AxisDescriptor()
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0      # the wrong value
    a1.name = "weight"
    a1.tag = "wght"
    doc.addAxis(a1)
    a2 = AxisDescriptor()
    a2.minimum = -10
    a2.maximum = 10
    a2.default = 0      # the wrong value
    a2.name = "width"
    a2.tag = "wdth"
    doc.addAxis(a2)
    # write the document
    doc.write(testDocPath)
    assert os.path.exists(testDocPath)
    # import it again
    new = DesignSpaceDocument()
    new.read(testDocPath)
    new.check()
    loc = new.default.location
    for axisObj in new.axes:
        n = axisObj.name
        assert axisObj.default == loc.get(n)


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
    f1 = open(testDocPath, 'r', encoding='utf-8')
    t1 = f1.read()
    f1.close()
    f2 = open(testDocPath2, 'r', encoding='utf-8')
    t2 = f2.read()
    f2.close()
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
    r1.conditions.append(dict(name='aaaa', minimum=0, maximum=1))
    r1.conditions.append(dict(name='bbbb', minimum=2, maximum=3))
    r1.subs.append(("a", "a.alt"))
    doc.addRule(r1)
    # write the document
    doc.write(testDocPath)
    assert os.path.exists(testDocPath)
    # import it again
    new = DesignSpaceDocument()
    new.read(testDocPath)
    new.write(testDocPath2)
    f1 = open(testDocPath, 'r', encoding='utf-8')
    t1 = f1.read()
    f1.close()
    f2 = open(testDocPath2, 'r', encoding='utf-8')
    t2 = f2.read()
    f2.close()
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
        a.name = "axisName%s"%(name)
        a.tag = "ax_%d"%(value)
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
    __removeAxesFromDesignSpace(testDocPath)
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

    # Case 1: filename and path are both empty. Nothing to calculate, nothing to put in the file.
    doc = DesignSpaceDocument()
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


def test_normalise():
    doc = DesignSpaceDocument()
    # write some axes
    a1 = AxisDescriptor()
    a1.minimum = -1000
    a1.maximum = 1000
    a1.default = 0
    a1.name = "aaa"
    a1.tag = "aaaa"
    doc.addAxis(a1)

    assert doc.normalizeLocation(dict(aaa=0)) == {'aaa': 0.0}
    assert doc.normalizeLocation(dict(aaa=1000)) == {'aaa': 1.0}

    # clipping beyond max values:
    assert doc.normalizeLocation(dict(aaa=1001)) == {'aaa': 1.0}
    assert doc.normalizeLocation(dict(aaa=500)) == {'aaa': 0.5}
    assert doc.normalizeLocation(dict(aaa=-1000)) == {'aaa': -1.0}
    assert doc.normalizeLocation(dict(aaa=-1001)) == {'aaa': -1.0}
    # anisotropic coordinates normalise to isotropic
    assert doc.normalizeLocation(dict(aaa=(1000, -1000))) == {'aaa': 1.0}
    doc.normalize()
    r = []
    for axis in doc.axes:
        r.append((axis.name, axis.minimum, axis.default, axis.maximum))
    r.sort()
    assert r == [('aaa', -1.0, 0.0, 1.0)]

    doc = DesignSpaceDocument()
    # write some axes
    a2 = AxisDescriptor()
    a2.minimum = 100
    a2.maximum = 1000
    a2.default = 100
    a2.name = "bbb"
    doc.addAxis(a2)
    assert doc.normalizeLocation(dict(bbb=0)) == {'bbb': 0.0}
    assert doc.normalizeLocation(dict(bbb=1000)) == {'bbb': 1.0}
    # clipping beyond max values:
    assert doc.normalizeLocation(dict(bbb=1001)) == {'bbb': 1.0}
    assert doc.normalizeLocation(dict(bbb=500)) == {'bbb': 0.4444444444444444}
    assert doc.normalizeLocation(dict(bbb=-1000)) == {'bbb': 0.0}
    assert doc.normalizeLocation(dict(bbb=-1001)) == {'bbb': 0.0}
    # anisotropic coordinates normalise to isotropic
    assert doc.normalizeLocation(dict(bbb=(1000,-1000))) == {'bbb': 1.0}
    assert doc.normalizeLocation(dict(bbb=1001)) == {'bbb': 1.0}
    doc.normalize()
    r = []
    for axis in doc.axes:
        r.append((axis.name, axis.minimum, axis.default, axis.maximum))
    r.sort()
    assert r == [('bbb', 0.0, 0.0, 1.0)]

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


    doc = DesignSpaceDocument()
    # write some axes
    a3 = AxisDescriptor()
    a3.minimum = 2000
    a3.maximum = 3000
    a3.default = 2000
    a3.name = "ccc"
    doc.addAxis(a3)
    assert doc.normalizeLocation(dict(ccc=0)) == {'ccc': 0.0}
    assert doc.normalizeLocation(dict(ccc=1)) == {'ccc': 0.0}
    assert doc.normalizeLocation(dict(ccc=-1000)) == {'ccc': 0.0}
    assert doc.normalizeLocation(dict(ccc=-1001)) == {'ccc': 0.0}

    doc.normalize()
    r = []
    for axis in doc.axes:
        r.append((axis.name, axis.minimum, axis.default, axis.maximum))
    r.sort()
    assert r == [('ccc', 0.0, 0.0, 1.0)]


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
    assert r == [('ddd', [(0, 0.1), (300, 0.5), (600, 0.5), (1000, 0.9)])]


def test_rules(tmpdir):
    tmpdir = str(tmpdir)
    testDocPath = os.path.join(tmpdir, "testRules.designspace")
    testDocPath2 = os.path.join(tmpdir, "testRules_roundtrip.designspace")
    doc = DesignSpaceDocument()
    # write some axes
    a1 = AxisDescriptor()
    a1.tag = "taga"
    a1.name = "aaaa"
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0
    doc.addAxis(a1)
    a2 = AxisDescriptor()
    a2.tag = "tagb"
    a2.name = "bbbb"
    a2.minimum = 0
    a2.maximum = 3000
    a2.default = 0
    doc.addAxis(a2)

    r1 = RuleDescriptor()
    r1.name = "named.rule.1"
    r1.conditions.append(dict(name='aaaa', minimum=0, maximum=1000))
    r1.conditions.append(dict(name='bbbb', minimum=0, maximum=3000))
    r1.subs.append(("a", "a.alt"))

    # rule with minium and maximum
    doc.addRule(r1)
    assert len(doc.rules) == 1
    assert len(doc.rules[0].conditions) == 2
    assert evaluateRule(r1, dict(aaaa = 500, bbbb = 0)) == True
    assert evaluateRule(r1, dict(aaaa = 0, bbbb = 0)) == True
    assert evaluateRule(r1, dict(aaaa = 1000, bbbb = 0)) == True
    assert evaluateRule(r1, dict(aaaa = 1000, bbbb = -100)) == False
    assert evaluateRule(r1, dict(aaaa = 1000.0001, bbbb = 0)) == False
    assert evaluateRule(r1, dict(aaaa = -0.0001, bbbb = 0)) == False
    assert evaluateRule(r1, dict(aaaa = -100, bbbb = 0)) == False
    assert processRules([r1], dict(aaaa = 500), ["a", "b", "c"]) == ['a.alt', 'b', 'c']
    assert processRules([r1], dict(aaaa = 500), ["a.alt", "b", "c"]) == ['a.alt', 'b', 'c']
    assert processRules([r1], dict(aaaa = 2000), ["a", "b", "c"]) == ['a', 'b', 'c']

    # rule with only a maximum
    r2 = RuleDescriptor()
    r2.name = "named.rule.2"
    r2.conditions.append(dict(name='aaaa', maximum=500))
    r2.subs.append(("b", "b.alt"))

    assert evaluateRule(r2, dict(aaaa = 0)) == True
    assert evaluateRule(r2, dict(aaaa = -500)) == True
    assert evaluateRule(r2, dict(aaaa = 1000)) == False

    # rule with only a minimum
    r3 = RuleDescriptor()
    r3.name = "named.rule.3"
    r3.conditions.append(dict(name='aaaa', minimum=500))
    r3.subs.append(("c", "c.alt"))

    assert evaluateRule(r3, dict(aaaa = 0)) == False
    assert evaluateRule(r3, dict(aaaa = 1000)) == True
    assert evaluateRule(r3, dict(bbbb = 1000)) == True

    # rule with only a minimum, maximum in separate conditions
    r4 = RuleDescriptor()
    r4.name = "named.rule.4"
    r4.conditions.append(dict(name='aaaa', minimum=500))
    r4.conditions.append(dict(name='bbbb', maximum=500))
    r4.subs.append(("c", "c.alt"))

    assert evaluateRule(r4, dict()) == True  # is this what we expect though?
    assert evaluateRule(r4, dict(aaaa = 1000, bbbb = 0)) == True
    assert evaluateRule(r4, dict(aaaa = 0, bbbb = 0)) == False
    assert evaluateRule(r4, dict(aaaa = 1000, bbbb = 1000)) == False

    a1 = AxisDescriptor()
    a1.minimum = 0
    a1.maximum = 1000
    a1.default = 0
    a1.name = "aaaa"
    a1.tag = "aaaa"
    b1 = AxisDescriptor()
    b1.minimum = 2000
    b1.maximum = 3000
    b1.default = 2000
    b1.name = "bbbb"
    b1.tag = "bbbb"
    doc.addAxis(a1)
    doc.addAxis(b1)
    assert doc._prepAxesForBender() == {'aaaa': {'map': [], 'name': 'aaaa', 'default': 0, 'minimum': 0, 'maximum': 1000, 'tag': 'aaaa'}, 'bbbb': {'map': [], 'name': 'bbbb', 'default': 2000, 'minimum': 2000, 'maximum': 3000, 'tag': 'bbbb'}}

    assert doc.rules[0].conditions == [{'minimum': 0, 'maximum': 1000, 'name': 'aaaa'}, {'minimum': 0, 'maximum': 3000, 'name': 'bbbb'}]

    assert doc.rules[0].subs == [('a', 'a.alt')]

    doc.normalize()
    assert doc.rules[0].name == 'named.rule.1'
    assert doc.rules[0].conditions == [{'minimum': 0.0, 'maximum': 1.0, 'name': 'aaaa'}, {'minimum': 0.0, 'maximum': 1.0, 'name': 'bbbb'}]

    doc.write(testDocPath)
    new = DesignSpaceDocument()

    new.read(testDocPath)
    assert len(new.axes) == 4
    assert len(new.rules) == 1
    new.write(testDocPath2)


def __removeAxesFromDesignSpace(path):
    # only for testing, so we can make an invalid designspace file
    # without making the designSpaceDocument also support it.
    f = open(path, 'r', encoding='utf-8')
    d = f.read()
    f.close()
    start = d.find("<axes>")
    end = d.find("</axes>")+len("</axes>")
    n = d[0:start] + d[end:]
    f = open(path, 'w', encoding='utf-8')
    f.write(n)
    f.close()


@pytest.fixture
def invalid_designspace():
    p = "testCheck.designspace"
    __removeAxesFromDesignSpace(p)
    yield p


@pytest.mark.xfail(reason="The check method requires MutatorMath")
def test_check(invalid_designspace, tmpdir):
    tmpdir = str(tmpdir)
    # check if the checks are checking
    testDocPath = os.path.join(tmpdir, invalid_designspace)
    masterPath1 = os.path.join(tmpdir, "masters", "masterTest1.ufo")
    masterPath2 = os.path.join(tmpdir, "masters", "masterTest2.ufo")
    instancePath1 = os.path.join(tmpdir, "instances", "instanceTest1.ufo")
    instancePath2 = os.path.join(tmpdir, "instances", "instanceTest2.ufo")

    # no default selected
    doc = DesignSpaceDocument()
    # add master 1
    s1 = SourceDescriptor()
    s1.path = masterPath1
    s1.name = "master.ufo1"
    s1.location = dict(snap=0, pop=10)
    s1.familyName = "MasterFamilyName"
    s1.styleName = "MasterStyleNameOne"
    doc.addSource(s1)
    # add master 2
    s2 = SourceDescriptor()
    s2.path = masterPath2
    s2.name = "master.ufo2"
    s2.location = dict(snap=1000, pop=20)
    s2.familyName = "MasterFamilyName"
    s2.styleName = "MasterStyleNameTwo"
    doc.addSource(s2)
    doc.checkAxes()
    doc.getAxisOrder() == ['snap', 'pop']
    assert doc.default == None
    doc.checkDefault()
    assert doc.default.name == 'master.ufo1'

    # default selected
    doc = DesignSpaceDocument()
    # add master 1
    s1 = SourceDescriptor()
    s1.path = masterPath1
    s1.name = "master.ufo1"
    s1.location = dict(snap=0, pop=10)
    s1.familyName = "MasterFamilyName"
    s1.styleName = "MasterStyleNameOne"
    doc.addSource(s1)
    # add master 2
    s2 = SourceDescriptor()
    s2.path = masterPath2
    s2.name = "master.ufo2"
    s2.copyInfo = True
    s2.location = dict(snap=1000, pop=20)
    s2.familyName = "MasterFamilyName"
    s2.styleName = "MasterStyleNameTwo"
    doc.addSource(s2)
    doc.checkAxes()
    assert doc.getAxisOrder() == ['snap', 'pop']
    assert doc.default == None
    doc.checkDefault()
    assert doc.default.name == 'master.ufo2'

    # generate a doc without axes, save and read again
    doc = DesignSpaceDocument()
    # add master 1
    s1 = SourceDescriptor()
    s1.path = masterPath1
    s1.name = "master.ufo1"
    s1.location = dict(snap=0, pop=10)
    s1.familyName = "MasterFamilyName"
    s1.styleName = "MasterStyleNameOne"
    doc.addSource(s1)
    # add master 2
    s2 = SourceDescriptor()
    s2.path = masterPath2
    s2.name = "master.ufo2"
    s2.location = dict(snap=1000, pop=20)
    s2.familyName = "MasterFamilyName"
    s2.styleName = "MasterStyleNameTwo"
    doc.addSource(s2)
    doc.checkAxes()
    doc.write(testDocPath)
    __removeAxesFromDesignSpace(testDocPath)

    new = DesignSpaceDocument()
    new.read(testDocPath)
    assert len(new.axes) == 2
    new.checkAxes()
    assert len(new.axes) == 2
    assert print([a.name for a in new.axes]) == ['snap', 'pop']
    new.write(testDocPath)
