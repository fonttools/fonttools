# Scripting a designspace

It can be useful to build a designspace with a script rather than construct one with an interface like [Superpolator](http://superpolator.com) or [DesignSpaceEditor](https://github.com/LettError/designSpaceRoboFontExtension). The [designSpaceDocument](https://github.com/LettError/designSpaceDocument) offers a some tools of building designspaces in Python. This document shows an example on how to do that.

So, suppose you installed the [designSpaceDocument](https://github.com/LettError/designSpaceDocument) package through your favorite `git` client.

The `DesignSpaceDocument` object represents the document, whether it already exists or not. Make a new one:

```python
import os
from designSpaceDocument import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
doc = DesignSpaceDocument()
```

We want to create definitions for axes, sources and instances. That means there are a lot of attributes to set. The **DesignSpaceDocument object** uses objects to descibe the axes, sources and instances. These are relatively simple objects, think of these as collections of attributes.

* [Attributes of the Source descriptor](https://github.com/LettError/designSpaceDocument#source-descriptor-object-attributes)
* [Attributes of the Instance descriptor](https://github.com/LettError/designSpaceDocument#instance-descriptor-object)
* [Attributes of the Axis descriptor](https://github.com/LettError/designSpaceDocument#axis-descriptor-object)
* Read about [subclassing descriptors](https://github.com/LettError/designSpaceDocument#subclassing-descriptors)

## Making some axes

Make a descriptor object and add it to the document.

```python
a1 = AxisDescriptor()
a1.initial = 0
a1.maximum = 1000
a1.minimum = 0
a1.default = 0
a1.name = "weight"
a1.tag = "wght"
doc.addAxis(a1)
```
* You can add as many axes as you need. OpenType has a maximum of around 64K. DesignSpaceEditor has a maximum of 5.
* The `name` attribute is the name you'll be using as the axis name in the locations.

## Make a source object

A **source** is an object that points to a UFO file. It provides the outline geometry, kerning and font.info that we want to work with.

```python
s0 = SourceDescriptor()
s0.path = "my/path/to/thin.ufo"
s0.name = "master.thin"
s0.location = dict(weight=0)
doc.addSource(s0)
```

* You'll need to have at least 2 sources in your document, so go ahead and add another one. 
* The **location** attribute is a dictionary with the designspace location for this master. 
* The axis names in the location have to match one of the `axis.name` values you defined before.
* The **path** attribute is the absolute path to an existing UFO.

So go ahead and add another master:

```python
s1 = SourceDescriptor()
s1.path = "my/path/to/bold.ufo"
s1.name = "master.bold"
s1.location = dict(weight=1000)
doc.addSource(s1)
```

## Make an instance object

An **instance** is description of a UFO that you want to generate with the designspace. For an instance you can define more things. If you want to generate UFO instances with MutatorMath then you can define different names and set flags for if you want to generate kerning and font info and so on. You can also set a path where to generate the instance.

```python
i0 = InstanceDescriptor()
i0.familyName = "MyVariableFontPrototype"
i0.styleName = "Medium"
i0.postScriptFontName = "MyVariableFontPrototype-Medium"
i0.path = os.path.join(root, "instances","MyVariableFontPrototype-Medium.ufo")
i0.location = dict(weight=500)
i0.kerning = True
i0.info = True
doc.addInstance(i0)
```
* The `path` attribute needs to be the absolute (real or intended) path for the instance. When the document is saved this path will written as relative to the path of the document.
* instance paths should be on the same level as the document, or in a level below.

# Saving

```python
path = "myprototype.designspace"
doc.write(path)
```

# Generating?

You can generate the UFO's with MutatorMath:

```python
from mutatorMath.ufo import build
build("whatevs/myprototype.designspace")
```
* Assuming the outline data in the masters is compatible. 

Or you can use the file in making a **variable font** with varlib.

