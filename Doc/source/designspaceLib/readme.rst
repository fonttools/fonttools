#################################
DesignSpaceDocument Specification
#################################

An object to read, write and edit interpolation systems for typefaces.

-  the format was originally written for MutatorMath.
-  the format is now also used in fontTools.varlib.
-  Define sources, axes and instances.
-  Not all values might be required by all applications.

A couple of differences between things that use designspaces:

-  Varlib does not support anisotropic interpolations.
-  MutatorMath and Superpolator will extrapolate over the boundaries of
   the axes. Varlib can not (at the moment).
-  Varlib requires much less data to define an instance than
   MutatorMath.
-  The goals of Varlib and MutatorMath are different, so not all
   attributes are always needed.
-  Need to expand the description of FDK use of designspace files.

The DesignSpaceDocument object can read and write ``.designspace`` data.
It imports the axes, sources and instances to very basic **descriptor**
objects that store the data in attributes. Data is added to the document
by creating such descriptor objects, filling them with data and then
adding them to the document. This makes it easy to integrate this object
in different contexts.

The **DesignSpaceDocument** object can be subclassed to work with
different objects, as long as they have the same attributes.

.. code:: python

    from designSpaceDocument import DesignSpaceDocument
    doc = DesignSpaceDocument()
    doc.read("some/path/to/my.designspace")
    doc.axes
    doc.sources
    doc.instances

**********
Validation
**********

Some validation is done when reading.

Axes
====

-  If the ``axes`` element is available in the document then all
   locations will check their dimensions against the defined axes. If a
   location uses an axis that is not defined it will be ignored.
-  If there are no ``axes`` in the document, locations will accept all
   axis names, so that we can..
-  Use ``doc.checkAxes()`` to reconstruct axes definitions based on the
   ``source.location`` values. If you save the document the axes will be
   there.

Default font
============

-  The source with the ``copyInfo`` flag indicates this is the default
   font.
-  In mutatorMath the default font is selected automatically. A warning
   is printed if the mutatorMath default selection differs from the one
   set by ``copyInfo``. But the ``copyInfo`` source will be used.
-  If no source has a ``copyInfo`` flag, mutatorMath will be used to
   select one. This source gets its ``copyInfo`` flag set. If you save
   the document this flag will be set.
-  Use ``doc.checkDefault()`` to set the default font.

************
Localisation
************

Some of the descriptors support localised names. The names are stored in
dictionaries using the language code as key. That means that there are
now two places to store names: the old attribute and the new localised
dictionary, ``obj.stylename`` and ``obj.localisedStyleName['en']``.

*****
Rules
*****

Rules describe designspace areas in which one glyph should be replaced by another.
A rule has a name and a number of conditionsets. The rule also contains a list of
glyphname pairs: the glyphs that need to be substituted. For a rule to be triggered
**only one** of the conditionsets needs to be true, ``OR``. Within a conditionset 
**all** conditions need to be true, ``AND``.

The ``sub`` element contains a pair of glyphnames. The ``name`` attribute is the glyph that should be visible when the rule evaluates to **False**. The ``with`` attribute is the glyph that should be visible when the rule evaluates to **True**.

UFO instances
=============

-  When making instances as UFOs however, we need to swap the glyphs so
   that the original shape is still available. For instance, if a rule
   swaps ``a`` for ``a.alt``, but a glyph that references ``a`` in a
   component would then show the new ``a.alt``.
-  But that can lead to unexpected results. So, if there are no rules
   for ``adieresis`` (assuming it references ``a``) then that glyph
   **should not change appearance**. That means that when the rule swaps
   ``a`` and ``a.alt`` it also swaps all components that reference these
   glyphs so they keep their appearance.
-  The swap function also needs to take care of swapping the names in
   kerning data.

**********
Python API
**********

SourceDescriptor object
=======================

Attributes
----------

-  ``filename``: string. A relative path to the source file, **as it is
   in the document**. MutatorMath + Varlib.
-  ``path``: string. Absolute path to the source file, calculated from
   the document path and the string in the filename attr. MutatorMath +
   Varlib.
-  ``layerName``: string. The name of the layer in the source to look for
   outline data. Default ``None`` which means ``foreground``.
-  ``font``: Any Python object. Optional. Points to a representation of
   this source font that is loaded in memory, as a Python object
   (e.g. a ``defcon.Font`` or a ``fontTools.ttFont.TTFont``). The default
   document reader will not fill-in this attribute, and the default
   writer will not use this attribute. It is up to the user of
   ``designspaceLib`` to either load the resource identified by ``filename``
   and store it in this field, or write the contents of this field to the
   disk and make ``filename`` point to that.
-  ``name``: string. Optional. Unique identifier name for this source,
   if there is one or more ``instance.glyph`` elements in the document.
   MutatorMath.
-  ``location``: dict. Axis values for this source. MutatorMath + Varlib
-  ``copyLib``: bool. Indicates if the contents of the font.lib need to
   be copied to the instances. MutatorMath.
-  ``copyInfo`` bool. Indicates if the non-interpolating font.info needs
   to be copied to the instances. Also indicates this source is expected
   to be the default font. MutatorMath + Varlib
-  ``copyGroups`` bool. Indicates if the groups need to be copied to the
   instances. MutatorMath.
-  ``copyFeatures`` bool. Indicates if the feature text needs to be
   copied to the instances. MutatorMath.
-  ``muteKerning``: bool. Indicates if the kerning data from this source
   needs to be muted (i.e. not be part of the calculations).
   MutatorMath.
-  ``muteInfo``: bool. Indicated if the interpolating font.info data for
   this source needs to be muted. MutatorMath.
-  ``mutedGlyphNames``: list. Glyphnames that need to be muted in the
   instances. MutatorMath.
-  ``familyName``: string. Family name of this source. Though this data
   can be extracted from the font, it can be efficient to have it right
   here. Varlib.
-  ``styleName``: string. Style name of this source. Though this data
   can be extracted from the font, it can be efficient to have it right
   here. Varlib.

.. code:: python

    doc = DesignSpaceDocument()
    s1 = SourceDescriptor()
    s1.path = masterPath1
    s1.name = "master.ufo1"
    s1.font = defcon.Font("master.ufo1")
    s1.copyLib = True
    s1.copyInfo = True
    s1.copyFeatures = True
    s1.location = dict(weight=0)
    s1.familyName = "MasterFamilyName"
    s1.styleName = "MasterStyleNameOne"
    s1.mutedGlyphNames.append("A")
    s1.mutedGlyphNames.append("Z")
    doc.addSource(s1)

.. _instance-descriptor-object:

InstanceDescriptor object
=========================

.. attributes-1:

Attributes
----------

-  ``filename``: string. Relative path to the instance file, **as it is
   in the document**. The file may or may not exist. MutatorMath.
-  ``path``: string. Absolute path to the source file, calculated from
   the document path and the string in the filename attr. The file may
   or may not exist. MutatorMath.
-  ``name``: string. Unique identifier name of the instance, used to
   identify it if it needs to be referenced from elsewhere in the
   document.
-  ``location``: dict. Axis values for this source. MutatorMath +
   Varlib.
-  ``familyName``: string. Family name of this instance. MutatorMath +
   Varlib.
-  ``localisedFamilyName``: dict. A dictionary of localised family name
   strings, keyed by language code.
-  ``styleName``: string. Style name of this source. MutatorMath +
   Varlib.
-  ``localisedStyleName``: dict. A dictionary of localised stylename
   strings, keyed by language code.
-  ``postScriptFontName``: string. Postscript fontname for this
   instance. MutatorMath.
-  ``styleMapFamilyName``: string. StyleMap familyname for this
   instance. MutatorMath.
-  ``localisedStyleMapFamilyName``: A dictionary of localised style map
   familyname strings, keyed by language code.
-  ``localisedStyleMapStyleName``: A dictionary of localised style map
   stylename strings, keyed by language code.
-  ``styleMapStyleName``: string. StyleMap stylename for this instance.
   MutatorMath.
-  ``glyphs``: dict for special master definitions for glyphs. If glyphs
   need special masters (to record the results of executed rules for
   example). MutatorMath.
-  ``kerning``: bool. Indicates if this instance needs its kerning
   calculated. MutatorMath.
-  ``info``: bool. Indicated if this instance needs the interpolating
   font.info calculated.
-  ``lib``: dict. Custom data associated with this instance.

Methods
-------

These methods give easier access to the localised names.

-  ``setStyleName(styleName, languageCode="en")``
-  ``getStyleName(languageCode="en")``
-  ``setFamilyName(familyName, languageCode="en")``
-  ``getFamilyName(self, languageCode="en")``
-  ``setStyleMapStyleName(styleMapStyleName, languageCode="en")``
-  ``getStyleMapStyleName(languageCode="en")``
-  ``setStyleMapFamilyName(styleMapFamilyName, languageCode="en")``
-  ``getStyleMapFamilyName(languageCode="en")``

Example
-------

.. code:: python

    i2 = InstanceDescriptor()
    i2.path = instancePath2
    i2.familyName = "InstanceFamilyName"
    i2.styleName = "InstanceStyleName"
    i2.name = "instance.ufo2"
    # anisotropic location
    i2.location = dict(weight=500, width=(400,300))
    i2.postScriptFontName = "InstancePostscriptName"
    i2.styleMapFamilyName = "InstanceStyleMapFamilyName"
    i2.styleMapStyleName = "InstanceStyleMapStyleName"
    glyphMasters = [dict(font="master.ufo1", glyphName="BB", location=dict(width=20,weight=20)), dict(font="master.ufo2", glyphName="CC", location=dict(width=900,weight=900))]
    glyphData = dict(name="arrow", unicodeValue=1234)
    glyphData['masters'] = glyphMasters
    glyphData['note'] = "A note about this glyph"
    glyphData['instanceLocation'] = dict(width=100, weight=120)
    i2.glyphs['arrow'] = glyphData
    i2.glyphs['arrow2'] = dict(mute=False)
    i2.lib['com.coolDesignspaceApp.specimenText'] = 'Hamburgerwhatever'
    doc.addInstance(i2)

.. _axis-descriptor-object:

AxisDescriptor object
=====================

-  ``tag``: string. Four letter tag for this axis. Some might be
   registered at the `OpenType
   specification <https://www.microsoft.com/typography/otspec/fvar.htm#VAT>`__.
   Privately-defined axis tags must begin with an uppercase letter and
   use only uppercase letters or digits.
-  ``name``: string. Name of the axis as it is used in the location
   dicts. MutatorMath + Varlib.
-  ``labelNames``: dict. When defining a non-registered axis, it will be
   necessary to define user-facing readable names for the axis. Keyed by
   xml:lang code. Values are required to be ``unicode`` strings, even if
   they only contain ASCII characters.
-  ``minimum``: number. The minimum value for this axis in user space.
   MutatorMath + Varlib.
-  ``maximum``: number. The maximum value for this axis in user space.
   MutatorMath + Varlib.
-  ``default``: number. The default value for this axis, i.e. when a new
   location is created, this is the value this axis will get in user
   space. MutatorMath + Varlib.
-  ``map``: list of input / output values that can describe a warp of user space
   to design space coordinates. If no map values are present, it is assumed user
   space is the same as design space, as in [(minimum, minimum), (maximum, maximum)].
   Varlib.

.. code:: python

    a1 = AxisDescriptor()
    a1.minimum = 1
    a1.maximum = 1000
    a1.default = 400
    a1.name = "weight"
    a1.tag = "wght"
    a1.labelNames[u'fa-IR'] = u"قطر"
    a1.labelNames[u'en'] = u"Wéíght"
    a1.map = [(1.0, 10.0), (400.0, 66.0), (1000.0, 990.0)]

RuleDescriptor object
=====================

-  ``name``: string. Unique name for this rule. Can be used to
   reference this rule data.
-  ``conditionSets``: a list of conditionsets
-  Each conditionset is a list of conditions.
-  Each condition is a dict with ``name``, ``minimum`` and ``maximum`` keys.
-  ``subs``: list of substitutions
-  Each substitution is stored as tuples of glyphnames, e.g. ("a", "a.alt").

.. code:: python

    r1 = RuleDescriptor()
    r1.name = "unique.rule.name"
    r1.conditionsSets.append([dict(name="weight", minimum=-10, maximum=10), dict(...)])
    r1.conditionsSets.append([dict(...), dict(...)])
    r1.subs.append(("a", "a.alt"))

.. _subclassing-descriptors:

Subclassing descriptors
=======================

The DesignSpaceDocument can take subclassed Reader and Writer objects.
This allows you to work with your own descriptors. You could subclass
the descriptors. But as long as they have the basic attributes the
descriptor does not need to be a subclass.

.. code:: python

    class MyDocReader(BaseDocReader):
        ruleDescriptorClass = MyRuleDescriptor
        axisDescriptorClass = MyAxisDescriptor
        sourceDescriptorClass = MySourceDescriptor
        instanceDescriptorClass = MyInstanceDescriptor

    class MyDocWriter(BaseDocWriter):
        ruleDescriptorClass = MyRuleDescriptor
        axisDescriptorClass = MyAxisDescriptor
        sourceDescriptorClass = MySourceDescriptor
        instanceDescriptorClass = MyInstanceDescriptor

    myDoc = DesignSpaceDocument(KeyedDocReader, KeyedDocWriter)

**********************
Document xml structure
**********************

-  The ``axes`` element contains one or more ``axis`` elements.
-  The ``sources`` element contains one or more ``source`` elements.
-  The ``instances`` element contains one or more ``instance`` elements.
-  The ``rules`` element contains one or more ``rule`` elements.
-  The ``lib`` element contains arbitrary data.

.. code:: xml

    <?xml version='1.0' encoding='utf-8'?>
    <designspace format="3">
        <axes>
            <!-- define axes here -->
            <axis../>
        </axes>
        <sources>
            <!-- define masters here -->
            <source../>
        </sources>
        <instances>
            <!-- define instances here -->
            <instance../>
        </instances>
        <rules>
            <!-- define rules here -->
            <rule../>
        </rules>
        <lib>
            <dict>
                <!-- store custom data here -->
            </dict>
        </lib>
    </designspace>

.. 1-axis-element:

1. axis element
===============

-  Define a single axis
-  Child element of ``axes``

.. attributes-2:

Attributes
----------

-  ``name``: required, string. Name of the axis that is used in the
   location elements.
-  ``tag``: required, string, 4 letters. Some axis tags are registered
   in the OpenType Specification.
-  ``minimum``: required, number. The minimum value for this axis.
-  ``maximum``: required, number. The maximum value for this axis.
-  ``default``: required, number. The default value for this axis.
-  ``hidden``: optional, 0 or 1. Records whether this axis needs to be
   hidden in interfaces.

.. code:: xml

    <axis name="weight" tag="wght" minimum="1" maximum="1000" default="400">

.. 11-labelname-element:

1.1 labelname element
=====================

-  Defines a human readable name for UI use.
-  Optional for non-registered axis names.
-  Can be localised with ``xml:lang``
-  Child element of ``axis``

.. attributes-3:

Attributes
----------

-  ``xml:lang``: required, string. `XML language
   definition <https://www.w3.org/International/questions/qa-when-xmllang.en>`__

Value
-----

-  The natural language name of this axis.

.. example-1:

Example
-------

.. code:: xml

    <labelname xml:lang="fa-IR">قطر</labelname>
    <labelname xml:lang="en">Wéíght</labelname>

.. 12-map-element:

1.2 map element
===============

-  Defines a single node in a series of input value / output value
   pairs.
-  Together these values transform the designspace.
-  Child of ``axis`` element.

.. example-2:

Example
-------

.. code:: xml

    <map input="1.0" output="10.0" />
    <map input="400.0" output="66.0" />
    <map input="1000.0" output="990.0" />

Example of all axis elements together:
--------------------------------------

.. code:: xml

        <axes>
            <axis default="1" maximum="1000" minimum="0" name="weight" tag="wght">
                <labelname xml:lang="fa-IR">قطر</labelname>
                <labelname xml:lang="en">Wéíght</labelname>
            </axis>
            <axis default="100" maximum="200" minimum="50" name="width" tag="wdth">
                <map input="50.0" output="10.0" />
                <map input="100.0" output="66.0" />
                <map input="200.0" output="990.0" />
            </axis>
        </axes>

.. 2-location-element:

2. location element
===================

-  Defines a coordinate in the design space.
-  Dictionary of axisname: axisvalue
-  Used in ``source``, ``instance`` and ``glyph`` elements.

.. 21-dimension-element:

2.1 dimension element
=====================

-  Child element of ``location``

.. attributes-4:

Attributes
----------

-  ``name``: required, string. Name of the axis.
-  ``xvalue``: required, number. The value on this axis.
-  ``yvalue``: optional, number. Separate value for anisotropic
   interpolations.

.. example-3:

Example
-------

.. code:: xml

    <location>
        <dimension name="width" xvalue="0.000000" />
        <dimension name="weight" xvalue="0.000000" yvalue="0.003" />
    </location>

.. 3-source-element:

3. source element
=================

-  Defines a single font that contributes to the designspace.
-  Child element of ``sources``

.. attributes-5:

Attributes
----------

-  ``familyname``: optional, string. The family name of the source font.
   While this could be extracted from the font data itself, it can be
   more efficient to add it here.
-  ``stylename``: optional, string. The style name of the source font.
-  ``name``: required, string. A unique name that can be used to
   identify this font if it needs to be referenced elsewhere.
-  ``filename``: required, string. A path to the source file, relative
   to the root path of this document. The path can be at the same level
   as the document or lower.
-  ``layer``: optional, string. The name of the layer in the source file.
   If no layer attribute is given assume the foreground layer should be used.

.. 31-lib-element:

3.1 lib element
===============

There are two meanings for the ``lib`` element:

1. Source lib
    -  Example: ``<lib copy="1" />``
    -  Child element of ``source``
    -  Defines if the instances can inherit the data in the lib of this
       source.
    -  MutatorMath only

2. Document and instance lib
    - Example:

      .. code:: xml

        <lib>
            <dict>
                <key>...</key>
                <string>The contents use the PLIST format.</string>
            </dict>
        </lib>

    - Child element of ``designspace`` and ``instance``
    - Contains arbitrary data about the whole document or about a specific
      instance.
    - Items in the dict need to use **reverse domain name notation** <https://en.wikipedia.org/wiki/Reverse_domain_name_notation>__

.. 32-info-element:

3.2 info element
================

-  ``<info copy="1" />``
-  Child element of ``source``
-  Defines if the instances can inherit the non-interpolating font info
   from this source.
-  MutatorMath + Varlib
-  NOTE: **This presence of this element indicates this source is to be
   the default font.**

.. 33-features-element:

3.3 features element
====================

-  ``<features copy="1" />``
-  Defines if the instances can inherit opentype feature text from this
   source.
-  Child element of ``source``
-  MutatorMath only

.. 34-glyph-element:

3.4 glyph element
=================

-  Can appear in ``source`` as well as in ``instance`` elements.
-  In a ``source`` element this states if a glyph is to be excluded from
   the calculation.
-  MutatorMath only

.. attributes-6:

Attributes
----------

-  ``mute``: optional attribute, number 1 or 0. Indicate if this glyph
   should be ignored as a master.
-  ``<glyph mute="1" name="A"/>``
-  MutatorMath only

.. 35-kerning-element:

3.5 kerning element
===================

-  ``<kerning mute="1" />``
-  Can appear in ``source`` as well as in ``instance`` elements.

.. attributes-7:

Attributes
----------

-  ``mute``: required attribute, number 1 or 0. Indicate if the kerning
   data from this source is to be excluded from the calculation.
-  If the kerning element is not present, assume ``mute=0``, yes,
   include the kerning of this source in the calculation.
-  MutatorMath only

.. example-4:

Example
-------

.. code:: xml

    <source familyname="MasterFamilyName" filename="masters/masterTest1.ufo" name="master.ufo1" stylename="MasterStyleNameOne">
        <lib copy="1" />
        <features copy="1" />
        <info copy="1" />
        <glyph mute="1" name="A" />
        <glyph mute="1" name="Z" />
        <location>
            <dimension name="width" xvalue="0.000000" />
            <dimension name="weight" xvalue="0.000000" />
        </location>
    </source>

.. 4-instance-element:

4. instance element
===================

-  Defines a single font that can be calculated with the designspace.
-  Child element of ``instances``
-  For use in Varlib the instance element really only needs the names
   and the location. The ``glyphs`` element is not required.
-  MutatorMath uses the ``glyphs`` element to describe how certain
   glyphs need different masters, mainly to describe the effects of
   conditional rules in Superpolator.

.. attributes-8:

Attributes
----------

-  ``familyname``: required, string. The family name of the instance
   font. Corresponds with ``font.info.familyName``
-  ``stylename``: required, string. The style name of the instance font.
   Corresponds with ``font.info.styleName``
-  ``name``: required, string. A unique name that can be used to
   identify this font if it needs to be referenced elsewhere.
-  ``filename``: string. Required for MutatorMath. A path to the
   instance file, relative to the root path of this document. The path
   can be at the same level as the document or lower.
-  ``postscriptfontname``: string. Optional for MutatorMath. Corresponds
   with ``font.info.postscriptFontName``
-  ``stylemapfamilyname``: string. Optional for MutatorMath. Corresponds
   with ``styleMapFamilyName``
-  ``stylemapstylename``: string. Optional for MutatorMath. Corresponds
   with ``styleMapStyleName``

Example for varlib
------------------

.. code:: xml

    <instance familyname="InstanceFamilyName" filename="instances/instanceTest2.ufo" name="instance.ufo2" postscriptfontname="InstancePostscriptName" stylemapfamilyname="InstanceStyleMapFamilyName" stylemapstylename="InstanceStyleMapStyleName" stylename="InstanceStyleName">
    <location>
        <dimension name="width" xvalue="400" yvalue="300" />
        <dimension name="weight" xvalue="66" />
    </location>
    <kerning />
    <info />
    <lib>
        <dict>
            <key>com.coolDesignspaceApp.specimenText</key>
            <string>Hamburgerwhatever</string>
        </dict>
    </lib>
    </instance>

.. 41-glyphs-element:

4.1 glyphs element
==================

-  Container for ``glyph`` elements.
-  Optional
-  MutatorMath only.

.. 42-glyph-element:

4.2 glyph element
=================

-  Child element of ``glyphs``
-  May contain a ``location`` element.

.. attributes-9:

Attributes
----------

-  ``name``: string. The name of the glyph.
-  ``unicode``: string. Unicode values for this glyph, in hexadecimal.
   Multiple values should be separated with a space.
-  ``mute``: optional attribute, number 1 or 0. Indicate if this glyph
   should be supressed in the output.

.. 421-note-element:

4.2.1 note element
==================

-  String. The value corresponds to glyph.note in UFO.

.. 422-masters-element:

4.2.2 masters element
=====================

-  Container for ``master`` elements
-  These ``master`` elements define an alternative set of glyph masters
   for this glyph.

.. 4221-master-element:

4.2.2.1 master element
======================

-  Defines a single alternative master for this glyph.

4.3 Localised names for instances
=================================

Localised names for instances can be included with these simple elements
with an ``xml:lang`` attribute:
`XML language definition <https://www.w3.org/International/questions/qa-when-xmllang.en>`__

-  stylename
-  familyname
-  stylemapstylename
-  stylemapfamilyname

.. example-5:

Example
-------

.. code:: xml

    <stylename xml:lang="fr">Demigras</stylename>
    <stylename xml:lang="ja">半ば</stylename>
    <familyname xml:lang="fr">Montserrat</familyname>
    <familyname xml:lang="ja">モンセラート</familyname>
    <stylemapstylename xml:lang="de">Standard</stylemapstylename>
    <stylemapfamilyname xml:lang="de">Montserrat Halbfett</stylemapfamilyname>
    <stylemapfamilyname xml:lang="ja">モンセラート SemiBold</stylemapfamilyname>

.. attributes-10:

Attributes
----------

-  ``glyphname``: the name of the alternate master glyph.
-  ``source``: the identifier name of the source this master glyph needs
   to be loaded from

.. example-6:

Example
-------

.. code:: xml

    <instance familyname="InstanceFamilyName" filename="instances/instanceTest2.ufo" name="instance.ufo2" postscriptfontname="InstancePostscriptName" stylemapfamilyname="InstanceStyleMapFamilyName" stylemapstylename="InstanceStyleMapStyleName" stylename="InstanceStyleName">
    <location>
        <dimension name="width" xvalue="400" yvalue="300" />
        <dimension name="weight" xvalue="66" />
    </location>
    <glyphs>
        <glyph name="arrow2" />
        <glyph name="arrow" unicode="0x4d2 0x4d3">
        <location>
            <dimension name="width" xvalue="100" />
            <dimension name="weight" xvalue="120" />
        </location>
        <note>A note about this glyph</note>
        <masters>
            <master glyphname="BB" source="master.ufo1">
            <location>
                <dimension name="width" xvalue="20" />
                <dimension name="weight" xvalue="20" />
            </location>
            </master>
        </masters>
        </glyph>
    </glyphs>
    <kerning />
    <info />
    <lib>
        <dict>
            <key>com.coolDesignspaceApp.specimenText</key>
            <string>Hamburgerwhatever</string>
        </dict>
    </lib>
    </instance>

.. 50-rules-element:

5.0 rules element
=================

-  Container for ``rule`` elements
-  The rules are evaluated in this order.

.. 51-rule-element:

5.1 rule element
================

-  Defines a named rule.
-  Each ``rule`` element contains one or more ``conditionset`` elements.
-  Only one ``conditionset`` needs to be true to trigger the rule.
-  All conditions in a ``conditionset`` must be true to make the ``conditionset`` true.
-  For backwards compatibility a ``rule`` can contain ``condition`` elements outside of a conditionset. These are then understood to be part of a single, implied, ``conditionset``. Note: these conditions should be written wrapped in a conditionset.
-  A rule element needs to contain one or more ``sub`` elements in order to be compiled to a variable font.
-  Rules without sub elements should be ignored when compiling a font.
-  For authoring tools it might be necessary to save designspace files without ``sub`` elements just because the work is incomplete.

.. attributes-11:

Attributes
----------

-  ``name``: optional, string. A unique name that can be used to
   identify this rule if it needs to be referenced elsewhere. The name
   is not important for compiling variable fonts.

5.1.1 conditionset element
=======================

-  Child element of ``rule``
-  Contains one or more ``condition`` elements.

.. 512-condition-element:

5.1.2 condition element
=======================

-  Child element of ``conditionset``
-  Between the ``minimum`` and ``maximum`` this rule is ``True``.
-  If ``minimum`` is not available, assume it is ``axis.minimum``.
-  If ``maximum`` is not available, assume it is ``axis.maximum``.
-  The condition must contain at least a minimum or maximum or both.

.. attributes-12:

Attributes
----------

-  ``name``: string, required. Must match one of the defined ``axis``
   name attributes.
-  ``minimum``: number, required*. The low value.
-  ``maximum``: number, required*. The high value.

.. 513-sub-element:

5.1.3 sub element
=================

-  Child element of ``rule``.
-  Defines which glyph to replace when the rule evaluates to **True**.

.. attributes-13:

Attributes
----------

-  ``name``: string, required. The name of the glyph this rule looks
   for.
-  ``with``: string, required. The name of the glyph it is replaced
   with.

.. example-7:

Example
-------

Example with an implied ``conditionset``. Here the conditions are not
contained in a conditionset. 

.. code:: xml

    <rules>
        <rule name="named.rule.1">
            <condition minimum="250" maximum="750" name="weight" />
            <condition minimum="50" maximum="100" name="width" />
            <sub name="dollar" with="dollar.alt"/>
        </rule>
    </rules>

Example with ``conditionsets``. All conditions in a conditionset must be true.

.. code:: xml

    <rules>
        <rule name="named.rule.2">
            <conditionset>
                <condition minimum="250" maximum="750" name="weight" />
                <condition minimum="50" maximum="100" name="width" />
            </conditionset>
            <conditionset>
                <condition ... />
                <condition ... />
            </conditionset>
            <sub name="dollar" with="dollar.alt"/>
        </rule>
    </rules>

.. 6-notes:

6 Notes
=======

Paths and filenames
-------------------

A designspace file needs to store many references to UFO files.

-  designspace files can be part of versioning systems and appear on
   different computers. This means it is not possible to store absolute
   paths.
-  So, all paths are relative to the designspace document path.
-  Using relative paths allows designspace files and UFO files to be
   **near** each other, and that they can be **found** without enforcing
   one particular structure.
-  The **filename** attribute in the ``SourceDescriptor`` and
   ``InstanceDescriptor`` classes stores the preferred relative path.
-  The **path** attribute in these objects stores the absolute path. It
   is calculated from the document path and the relative path in the
   filename attribute when the object is created.
-  Only the **filename** attribute is written to file.
-  Both **filename** and **path** must use forward slashes (``/``) as
   path separators, even on Windows.

Right before we save we need to identify and respond to the following
situations:

In each descriptor, we have to do the right thing for the filename
attribute. Before writing to file, the ``documentObject.updatePaths()``
method prepares the paths as follows:

**Case 1**

::

    descriptor.filename == None
    descriptor.path == None

**Action**

-  write as is, descriptors will not have a filename attr. Useless, but
   no reason to interfere.

**Case 2**

::

    descriptor.filename == "../something"
    descriptor.path == None

**Action**

-  write as is. The filename attr should not be touched.

**Case 3**

::

    descriptor.filename == None
    descriptor.path == "~/absolute/path/there"

**Action**

-  calculate the relative path for filename. We're not overwriting some
   other value for filename, it should be fine.

**Case 4**

::

    descriptor.filename == '../somewhere'
    descriptor.path == "~/absolute/path/there"

**Action**

-  There is a conflict between the given filename, and the path. The
   difference could have happened for any number of reasons. Assuming
   the values were not in conflict when the object was created, either
   could have changed. We can't guess.
-  Assume the path attribute is more up to date. Calculate a new value
   for filename based on the path and the document path.

Recommendation for editors
--------------------------

-  If you want to explicitly set the **filename** attribute, leave the
   path attribute empty.
-  If you want to explicitly set the **path** attribute, leave the
   filename attribute empty. It will be recalculated.
-  Use ``documentObject.updateFilenameFromPath()`` to explicitly set the
   **filename** attributes for all instance and source descriptors.

.. 7-common-lib-key-registry:

7 Common Lib Key Registry
=========================

public.skipExportGlyphs
-----------------------

This lib key works the same as the UFO lib key with the same name. The
difference is that applications using a Designspace as the corner stone of the
font compilation process should use the lib key in that Designspace instead of
any of the UFOs. If the lib key is empty or not present in the Designspace, all
glyphs should be exported, regardless of what the same lib key in any of the
UFOs says.

.. 8-this-document:

8 This document
===============

-  The package is rather new and changes are to be expected.
