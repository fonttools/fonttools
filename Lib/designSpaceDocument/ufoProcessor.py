from __future__ import print_function, division, absolute_import

from ufoLib import fontInfoAttributesVersion1, fontInfoAttributesVersion2, fontInfoAttributesVersion3
from pprint import pprint

"""
    
    A subclassed DesignSpaceDocument that can
        - process the document and generate finished UFOs with MutatorMath.
        - read and write documents
        - bypass and eventually replace the mutatormath ufo generator.

"""


from designSpaceDocument import DesignSpaceDocument, SourceDescriptor, InstanceDescriptor, AxisDescriptor, RuleDescriptor, processRules
from defcon.objects.font import Font
import defcon
from fontMath.mathGlyph import MathGlyph
from fontMath.mathInfo import MathInfo
from fontMath.mathKerning import MathKerning
from mutatorMath.objects.mutator import buildMutator
from mutatorMath.objects.location import biasFromLocations, Location
import os

"""

    Swap the contents of two glyphs.
        - contours
        - components
        - width
        - group membership
        - kerning

    + Remap components so that glyphs that reference either of the swapped glyphs maintain appearance
    + Keep the unicode value of the original glyph.
    
    Notes
    Parking the glyphs under a swapname is a bit lazy, but at least it guarantees the glyphs have the right parent.

"""
def swapGlyphNames(font, oldName, newName, swapNameExtension = "_______________swap"):
    if not oldName in font or not newName in font:
        return None
    swapName = oldName + swapNameExtension
    # park the old glyph 
    if not swapName in font:
        font.newGlyph(swapName)
    # swap the outlines
    font[swapName].clear()
    p = font[swapName].getPointPen()
    font[oldName].drawPoints(p)
    font[swapName].width = font[oldName].width
    
    font[oldName].clear()
    p = font[oldName].getPointPen()
    font[newName].drawPoints(p)
    font[oldName].width = font[newName].width
    
    font[newName].clear()
    p = font[newName].getPointPen()
    font[swapName].drawPoints(p)
    font[newName].width = font[swapName].width
    
    # remap the components
    for g in font:
        for c in g.components:
           if c.baseGlyph == oldName:
               c.baseGlyph = swapName
           continue
    for g in font:
        for c in g.components:
           if c.baseGlyph == newName:
               c.baseGlyph = oldName
           continue
    for g in font:
        for c in g.components:
           if c.baseGlyph == swapName:
               c.baseGlyph = newName
   
    # change the names in groups
    # the shapes will swap, that will invalidate the kerning
    # so the names need to swap in the kerning as well.
    newKerning = {}
    for first, second in font.kerning.keys():
        value = font.kerning[(first,second)]
        if first == oldName:
            first = newName
        elif first == newName:
            first = oldName
        if second == oldName:
            second = newName
        elif second == newName:
            second = oldName
        newKerning[(first, second)] = value
    font.kerning.clear()
    font.kerning.update(newKerning)
            
    for groupName, members in font.groups.items():
        newMembers = []
        for name in members:
            if name == oldName:
                newMembers.append(newName)
            elif name == newName:
                newMembers.append(oldName)
            else:
                newMembers.append(name)
        font.groups[groupName] = newMembers
    
    remove = []
    for g in font:
        if g.name.find(swapNameExtension)!=-1:
            remove.append(g.name)
    for r in remove:
        del font[r]


class DesignSpaceProcessor(DesignSpaceDocument):
    """
        builder of glyphs from designspaces
        validate the data
        if it works, make a generating thing
    """

    fontClass = defcon.Font
    glyphClass = defcon.Glyph
    libClass = defcon.Lib
    glyphContourClass = defcon.Contour
    glyphPointClass = defcon.Point
    glyphComponentClass = defcon.Component
    glyphAnchorClass = defcon.Anchor
    kerningClass = defcon.Kerning
    groupsClass = defcon.Groups
    infoClass = defcon.Info
    featuresClass = defcon.Features

    mathInfoClass = MathInfo
    mathGlyphClass = MathGlyph
    mathKerningClass = MathKerning

    def __init__(self, readerClass=None, writerClass=None, fontClass=None, ufoVersion=2):
        super(DesignSpaceProcessor, self).__init__(readerClass=readerClass, writerClass=writerClass, fontClass=fontClass)
        self.ufoVersion = ufoVersion         # target UFO version
        self.roundGeometry = False
        self._glyphMutators = {}
        self._infoMutator = None
        self._kerningMutator = None
        self._preppedAxes = None
        self.fonts = {}
        self.glyphNames = []     # list of all glyphnames
        self.processRules = True
        self.problems = []  # receptacle for problem notifications. Not big enough to break, but also not small enough to ignore.

    def generateUFO(self, processRules=True):
        # makes the instances
        # option to execute the rules
        #self.checkAxes()
        self.loadFonts()
        self.checkDefault()
        for instanceDescriptor in self.instances:
            if instanceDescriptor.path is None:
                continue
            font = self.makeInstance(instanceDescriptor, processRules)
            if not os.path.exists(os.path.dirname(instanceDescriptor.path)):
                os.makedirs(os.path.dirname(instanceDescriptor.path))
            font.save(instanceDescriptor.path, self.ufoVersion)

    def getInfoMutator(self):
        """ Returns a info mutator """
        if self._infoMutator:
            return self._infoMutator
        infoItems = []
        for sourceDescriptor in self.sources:
            loc = Location(sourceDescriptor.location)
            sourceFont = self.fonts[sourceDescriptor.name]
            infoItems.append((loc, self.mathInfoClass(sourceFont.info)))
        bias, self._infoMutator = buildMutator(infoItems, axes=self._preppedAxes, bias=self.defaultLoc)
        return self._infoMutator

    def getKerningMutator(self):
        """ Return a kerning mutator """
        if self._kerningMutator:
            return self._kerningMutator
        kerningItems = []
        for sourceDescriptor in self.sources:
            loc = Location(sourceDescriptor.location)
            sourceFont = self.fonts[sourceDescriptor.name]
            kerningItems.append((loc, self.mathKerningClass(sourceFont.kerning, sourceFont.groups)))
        bias, self._kerningMutator = buildMutator(kerningItems, axes=self._preppedAxes, bias=self.defaultLoc)
        return self._kerningMutator

    def getGlyphMutator(self, glyphName):
        """ Return a glyph mutator """
        if glyphName in self._glyphMutators:
            return self._glyphMutators[glyphName]
        items = []
        for sourceDescriptor in self.sources:
            loc = Location(sourceDescriptor.location)
            f = self.fonts[sourceDescriptor.name]
            if glyphName in sourceDescriptor.mutedGlyphNames:
                continue
            if not glyphName in f:
                # log this>
                continue
            items.append((loc, self.mathGlyphClass(f[glyphName])))
        bias, self._glyphMutators[glyphName] = buildMutator(items, axes=self._preppedAxes, bias=self.defaultLoc)
        return self._glyphMutators[glyphName]

    def loadFonts(self):
        # Load the fonts and find the default candidate based on the info flag
        names = set()
        for sourceDescriptor in self.sources:
            if not sourceDescriptor.name in self.fonts:
                self.fonts[sourceDescriptor.name] = self._instantiateFont(sourceDescriptor.path)
            names = names | set(self.fonts[sourceDescriptor.name].keys())
        self.glyphNames = list(names)

    def makeInstance(self, instanceDescriptor, doRules=False, glyphNames=None):
        """ Generate a font object for this instance """
        font = self._instantiateFont(None)
        self._preppedAxes = self._prepAxesForBender()
        # make fonty things here
        loc = Location(instanceDescriptor.location)
        # make the kerning
        if instanceDescriptor.kerning:
            try:
                self.getKerningMutator().makeInstance(loc).extractKerning(font)
            except:
                self.problems.append("Could not make kerning for %s"%loc)
        # make the info
        if instanceDescriptor.info:
            try:
                self.getInfoMutator().makeInstance(loc).extractInfo(font.info)
                info = self._infoMutator.makeInstance(loc)
                info.extractInfo(font.info)
                font.info.familyName = instanceDescriptor.familyName
                font.info.styleName = instanceDescriptor.styleName
                font.info.postScriptFontName = instanceDescriptor.postScriptFontName
                font.info.styleMapFamilyName = instanceDescriptor.styleMapFamilyName
                font.info.styleMapStyleName = instanceDescriptor.styleMapStyleName
                # localised names need to go to the right openTypeNameRecords
                #print("xxx", font.info.openTypeNameRecords)
                # records = []
                # nameID = 1
                # platformID = 
                # for languageCode, name in instanceDescriptor.localisedStyleMapFamilyName.items():
                #    # Name ID 1 (font family name) is found at the generic styleMapFamily attribute.
                #    records.append((nameID, ))

            except:
                self.problems.append("Could not make fontinfo for %s"%loc)
        # copied info
        for sourceDescriptor in self.sources:
            if sourceDescriptor.copyInfo:
                # this is the source
                self._copyFontInfo(self.fonts[sourceDescriptor.name].info, font.info)
            if sourceDescriptor.copyLib:
                font.lib.update(self.fonts[sourceDescriptor.name].lib)
            if sourceDescriptor.copyFeatures:
                featuresText = self.fonts[sourceDescriptor.name].features.text
                if isinstance(featuresText, str):
                    font.features.text = u""+featuresText
                elif isinstance(featuresText, unicode):
                    font.features.text = featuresText
        # glyphs
        if glyphNames:
            selectedGlyphNames = glyphNames
        else:
            selectedGlyphNames = self.glyphNames
        for glyphName in selectedGlyphNames:
            try:
                glyphMutator = self.getGlyphMutator(glyphName)
            except:
                self.problems.append("Could not make mutator for glyph %s"%glyphName)
                continue
            if glyphName in instanceDescriptor.glyphs.keys():
                # reminder: this is what the glyphData can look like
                # {'instanceLocation': {'custom': 0.0, 'weight': 824.0},
                #  'masters': [{'font': 'master.Adobe VF Prototype.Master_0.0',
                #               'glyphName': 'dollar.nostroke',
                #               'location': {'custom': 0.0, 'weight': 0.0}},
                #              {'font': 'master.Adobe VF Prototype.Master_1.1',
                #               'glyphName': 'dollar.nostroke',
                #               'location': {'custom': 0.0, 'weight': 368.0}},
                #              {'font': 'master.Adobe VF Prototype.Master_2.2',
                #               'glyphName': 'dollar.nostroke',
                #               'location': {'custom': 0.0, 'weight': 1000.0}},
                #              {'font': 'master.Adobe VF Prototype.Master_3.3',
                #               'glyphName': 'dollar.nostroke',
                #               'location': {'custom': 100.0, 'weight': 1000.0}},
                #              {'font': 'master.Adobe VF Prototype.Master_0.4',
                #               'glyphName': 'dollar.nostroke',
                #               'location': {'custom': 100.0, 'weight': 0.0}},
                #              {'font': 'master.Adobe VF Prototype.Master_4.5',
                #               'glyphName': 'dollar.nostroke',
                #               'location': {'custom': 100.0, 'weight': 368.0}}],
                #  'unicodeValue': 36}
                glyphData = instanceDescriptor.glyphs[glyphName]
            else:
                glyphData = {}
            font.newGlyph(glyphName)
            font[glyphName].clear()
            if glyphData.get('mute', False):
                # mute this glyph, skip
                continue
            glyphInstanceLocation = Location(glyphData.get("instanceLocation", instanceDescriptor.location))
            try:
                uniValue = glyphMutator[()][0].unicodes[0]
            except IndexError:
                uniValue = None
            glyphInstanceUnicode = glyphData.get("unicodeValue", uniValue)
            note = glyphData.get("note")
            if note:
                font[glyphName] = note
            masters = glyphData.get("masters", None)
            if masters:
                items = []
                for glyphMaster in masters:
                    sourceGlyphFont = glyphMaster.get("font")
                    sourceGlyphName = glyphMaster.get("glyphName", glyphName)
                    m = self.fonts.get(sourceGlyphFont)
                    if not sourceGlyphName in m:
                        continue
                    sourceGlyph = MathGlyph(m[sourceGlyphName])
                    sourceGlyphLocation = Location(glyphMaster.get("location"))
                    items.append((sourceGlyphLocation, sourceGlyph))
                bias, glyphMutator = buildMutator(items, axes=self._preppedAxes, bias=self.defaultLoc)
            try:
                glyphInstanceObject = glyphMutator.makeInstance(glyphInstanceLocation)
            except IndexError:
                # alignment problem with the data?
                print("Error making instance %s"%glyphName)
                continue
            font.newGlyph(glyphName)
            font[glyphName].clear()
            if self.roundGeometry:
                try:
                    glyphInstanceObject = glyphInstanceObject.round()
                except AttributeError:
                    pass
            try:
                glyphInstanceObject.extractGlyph(font[glyphName], onlyGeometry=True)
            except TypeError:
                # this causes ruled glyphs to end up in the wrong glyphname
                # but defcon2 objects don't support it
                pPen = font[glyphName].getPointPen()
                font[glyphName].clear()
                glyphInstanceObject.drawPoints(pPen)
            font[glyphName].width = glyphInstanceObject.width
            font[glyphName].unicode = glyphInstanceUnicode
        if doRules:
            resultNames = processRules(self.rules, loc, self.glyphNames)
            for oldName, newName in zip(self.glyphNames, resultNames):
                if oldName != newName:
                    swapGlyphNames(font, oldName, newName)
        # store designspace location in the font.lib
        font.lib['designspace'] = instanceDescriptor.location.items()
        return font

    def _instantiateFont(self, path):
        """ Return a instance of a font object with all the given subclasses"""
        return self.fontClass(path,
            libClass=self.libClass,
            kerningClass=self.kerningClass,
            groupsClass=self.groupsClass,
            infoClass=self.infoClass,
            featuresClass=self.featuresClass,
            glyphClass=self.glyphClass,
            glyphContourClass=self.glyphContourClass,
            glyphPointClass=self.glyphPointClass,
            glyphComponentClass=self.glyphComponentClass,
            glyphAnchorClass=self.glyphAnchorClass)

    def _copyFontInfo(self, sourceInfo, targetInfo):
        """ Copy the non-calculating fields from the source info."""
        infoAttributes = [
            "versionMajor",
            "versionMinor",
            "copyright",
            "trademark",
            "note",
            "openTypeGaspRangeRecords",
            "openTypeHeadCreated",
            "openTypeHeadFlags",
            "openTypeNameDesigner",
            "openTypeNameDesignerURL",
            "openTypeNameManufacturer",
            "openTypeNameManufacturerURL",
            "openTypeNameLicense",
            "openTypeNameLicenseURL",
            "openTypeNameVersion",
            "openTypeNameUniqueID",
            "openTypeNameDescription",
            "#openTypeNamePreferredFamilyName",
            "#openTypeNamePreferredSubfamilyName",
            "#openTypeNameCompatibleFullName",
            "openTypeNameSampleText",
            "openTypeNameWWSFamilyName",
            "openTypeNameWWSSubfamilyName",
            "openTypeNameRecords",
            "openTypeOS2Selection",
            "openTypeOS2VendorID",
            "openTypeOS2Panose",
            "openTypeOS2FamilyClass",
            "openTypeOS2UnicodeRanges",
            "openTypeOS2CodePageRanges",
            "openTypeOS2Type",
            "postscriptIsFixedPitch",
            "postscriptForceBold",
            "postscriptDefaultCharacter",
            "postscriptWindowsCharacterSet"
        ]
        for infoAttribute in infoAttributes:
            copy = False
            if self.ufoVersion == 1 and infoAttribute in fontInfoAttributesVersion1:
                copy = True
            elif self.ufoVersion == 2 and infoAttribute in fontInfoAttributesVersion2:
                copy = True
            elif self.ufoVersion == 3 and infoAttribute in fontInfoAttributesVersion3:
                copy = True
            if copy:
                value = getattr(sourceInfo, infoAttribute)
                setattr(targetInfo, infoAttribute, value)





if __name__ == "__main__":
    # standalone test
    import shutil
    import os
    from defcon.objects.font import Font
    import logging

    def addGlyphs(font, s):
        # we need to add the glyphs
        step = 0
        for n in ['glyphOne', 'glyphTwo', 'glyphThree', 'glyphFour']:
            font.newGlyph(n)
            g = font[n]
            p = g.getPen()
            p.moveTo((0,0))
            p.lineTo((s,0))
            p.lineTo((s,s))
            p.lineTo((0,s))
            p.closePath()
            g.move((0,s+step))
            g.width = s
            g.unicode = 200 + step
            step += 50
        for n, w in [('wide', 800), ('narrow', 100)]:
            font.newGlyph(n)
            g = font[n]
            p = g.getPen()
            p.moveTo((0,0))
            p.lineTo((w,0))
            p.lineTo((w,font.info.ascender))
            p.lineTo((0,font.info.ascender))
            p.closePath()
            g.width = w
        font.newGlyph("wide.component")
        g = font["wide.component"]
        comp = g.instantiateComponent()
        comp.baseGlyph = "wide"
        comp.offset = (0,0)
        g.appendComponent(comp)
        g.width = font['wide'].width
        font.newGlyph("narrow.component")
        g = font["narrow.component"]
        comp = g.instantiateComponent()
        comp.baseGlyph = "narrow"
        comp.offset = (0,0)
        g.appendComponent(comp)
        g.width = font['narrow'].width
        uniValue = 200
        for g in font:
            g.unicode = uniValue
            uniValue += 1


    def fillInfo(font):
        font.info.unitsPerEm = 1000
        font.info.ascender = 800
        font.info.descender = -200

    def makeTestFonts(rootPath):
        """ Make some test fonts that have the kerning problem."""
        path1 = os.path.join(rootPath, "geometryMaster1.ufo")
        path2 = os.path.join(rootPath, "geometryMaster2.ufo")
        path3 = os.path.join(rootPath, "my_test_instance_dir_one", "geometryInstance%3.3f.ufo")
        path4 = os.path.join(rootPath, "my_test_instance_dir_two", "geometryInstanceAnisotropic1.ufo")
        path5 = os.path.join(rootPath, "my_test_instance_dir_two", "geometryInstanceAnisotropic2.ufo")
        f1 = Font()
        fillInfo(f1)
        addGlyphs(f1, 100)
        f1.features.text = u"# features text from master 1"
        f2 = Font()
        fillInfo(f2)
        addGlyphs(f2, 500)
        f2.features.text = u"# features text from master 2"
        f1.info.ascender = 400
        f1.info.descender = -200
        f2.info.ascender = 600
        f2.info.descender = -100
        f1.info.copyright = u"This is the copyright notice from master 1"
        f2.info.copyright = u"This is the copyright notice from master 2"
        f1.save(path1, 2)
        f2.save(path2, 2)
        return path1, path2, path3, path4, path5

    def makeSwapFonts(rootPath):
        """ Make some test fonts that have the kerning problem."""
        path1 = os.path.join(rootPath, "Swap.ufo")
        path2 = os.path.join(rootPath, "Swapped.ufo")
        f1 = Font()
        fillInfo(f1)
        addGlyphs(f1, 100)
        f1.features.text = u"# features text from master 1"
        f1.info.ascender = 800
        f1.info.descender = -200
        f1.kerning[('glyphOne', 'glyphOne')] = -10
        f1.kerning[('glyphTwo', 'glyphTwo')] = 10
        f1.save(path1, 2)
        return path1, path2

    def test0(docPath):
        # make the test fonts and a test document
        testFontPath = os.path.join(os.getcwd(), "automatic_testfonts")
        m1, m2, i1, i2, i3 = makeTestFonts(testFontPath)
        d = DesignSpaceProcessor()
        a = AxisDescriptor()
        a.name = "pop"
        a.minimum = 50
        a.maximum = 1000
        a.default = 0
        a.tag = "pop*"
        d.addAxis(a)
        s1 = SourceDescriptor()
        s1.path = m1
        s1.location = dict(pop=a.minimum)
        s1.name = "test.master.1"
        s1.copyInfo = True
        s1.copyFeatures = True
        d.addSource(s1)
        s2 = SourceDescriptor()
        s2.path = m2
        s2.location = dict(pop=1000)
        s2.name = "test.master.2"
        #s2.copyInfo = True
        d.addSource(s2)

        for counter in range(3):
            factor = counter / 2        
            i = InstanceDescriptor()
            v = a.minimum+factor*(a.maximum-a.minimum)
            i.path = i1%v
            i.familyName = "TestFamily"
            i.styleName = "TestStyle_pop%3.3f"%(v)
            i.name = "%s-%s"%(i.familyName, i.styleName)
            i.location = dict(pop=v)
            i.info = True
            i.kerning = True
            if counter == 2:
                i.glyphs['glyphTwo'] = dict(name="glyphTwo", mute=True)
            d.addInstance(i)
        d.write(docPath)

    def test1(docPath):
        # execute the test document
        d = DesignSpaceProcessor()
        d.read(docPath)
        d.generateUFO()

    def testSwap(docPath):
        srcPath, dstPath = makeSwapFonts(os.path.dirname(docPath))
        
        f = Font(srcPath)
        swapGlyphNames(f, "narrow", "wide")
        f.info.styleName = "Swapped"
        f.save(dstPath)
        
        # test the results in newly opened fonts
        old = Font(srcPath)
        new = Font(dstPath)
        assert new.kerning.get(("narrow", "narrow")) == old.kerning.get(("wide","wide"))
        assert new.kerning.get(("wide", "wide")) == old.kerning.get(("narrow","narrow"))
        # after the swap these widths should be the same
        assert old['narrow'].width == new['wide'].width
        assert old['wide'].width == new['narrow'].width
        # The following test may be a bit counterintuitive:
        # the rule swaps the glyphs, but we do not want glyphs that are not
        # specifically affected by the rule to *appear* any different.
        # So, components have to be remapped. 
        assert new['wide.component'].components[0].baseGlyph == "narrow"
        assert new['narrow.component'].components[0].baseGlyph == "wide"

    selfTest = True
    if selfTest:
        testRoot = os.path.join(os.getcwd(), "automatic_testfonts")
        if os.path.exists(testRoot):
            shutil.rmtree(testRoot)
        docPath = os.path.join(testRoot, "automatic_test.designspace")
        test0(docPath)
        test1(docPath)
        testSwap(docPath)
