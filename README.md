[![Travis Build Status](https://travis-ci.org/behdad/fonttools.svg)](https://travis-ci.org/behdad/fonttools)
[![Appveyor Build Status](https://ci.appveyor.com/api/projects/status/k0sa9nfhkeqc0s3c/branch/master?svg=true)](https://ci.appveyor.com/project/behdad/fonttools/branch/master)
[![Health](https://landscape.io/github/behdad/fonttools/master/landscape.svg?style=flat)](https://landscape.io/github/behdad/fonttools/master)
[![Coverage Status](https://img.shields.io/coveralls/behdad/fonttools.svg)](https://coveralls.io/r/behdad/fonttools)

### What is this?

fontTools is a library for manipulating fonts, written in Python. 
The project includes the TTX tool, that can convert TrueType and OpenType fonts to and from an XML text format, which is also called TTX.
It supports TrueType, OpenType, AFM and to an extent Type 1 and some Mac-specific formats.
The project has a [BSD-style open-source licence](LICENSE.txt).  
Among other things this means you can use it free of charge. 

### Installation

FontTools requires Python 2.7, or Python 3.3 or later.
The fresh versions as well as older versions can be downloaded from <http://www.python.org/download/>
  
- Windows: grab the Windows installer, run the full install.
- Un\*x: follow the build instructions.
- MacOS: grab the installer, run "Easy Install"

A package is available in pypi from <https://pypi.python.org/pypi/FontTools>

```
easy_install pip ;
pip install fonttools ;
```

For people who want to download and install fontools on your system from source code, run the following commands:

```sh
git clone https://github.com/behdad/fonttools.git ;
cd fonttools ;
python setup.py install ;
```

This will install all the modules and command line tools in the right places.

### TTX – From OpenType and TrueType to XML and Back

Once installed you can use the `ttx` command to convert binary font files (`.otf`, `.ttf`, etc) to the TTX xml format, edit them, and convert them back to binary format. 
TTX files have a .ttx file extension.

```sh
ttx /path/to/font.otf ;
ttx /path/to/font.ttx ;
```

The TTX application works can be used in two ways, depending on what platform you run it on:

* As a command line tool (Windows/DOS, Unix, MacOSX)
* By dropping files onto the application (Windows, MacOS)

TTX detects what kind of files it is fed: it will output a `.ttx` file when it sees a `.ttf` or `.otf`, and it will compile a `.ttf` or `.otf` when the input file is a `.ttx` file. 
By default, the output file is created in the same folder as the input file, and will have the same name as the input file but with a different extension. 
TTX will _never_ overwrite existing files, but if necessary will append a unique number to the output filename (before the extension) such as `Arial#1.ttf`

When using TTX from the command line there are a bunch of extra options, these are explained in the help text, as displayed when typing `ttx -h` at the command prompt. 
These additional options include:

* specifying the folder where the output files are created
* specifying which tables to dump or which tables to exclude
* merging partial `.ttx` files with existing `.ttf` or `.otf` files
* listing brief table info instead of dumping to `.ttx`
* splitting tables to separate `.ttx` files
* disabling TrueType instruction disassembly

#### The TTX file format

The following tables are currently supported:
<!-- begin table list -->
    BASE, CBDT, CBLC, CFF, COLR, CPAL, DSIG, EBDT, EBLC, FFTM, GDEF,
    GMAP, GPKG, GPOS, GSUB, JSTF, LTSH, MATH, META, OS/2, SING, SVG,
    TSI0, TSI1, TSI2, TSI3, TSI5, TSIB, TSID, TSIJ, TSIP, TSIS, TSIV,
    VDMX, VORG, avar, cmap, cvt, feat, fpgm, fvar, gasp, glyf, gvar,
    hdmx, head, hhea, hmtx, kern, loca, ltag, maxp, meta, name, post,
    prep, sbix, trak, vhea and vmtx
<!-- end table list -->
Other tables are dumped as hexadecimal data.

TrueType fonts use glyph indices (GlyphIDs) to refer to glyphs in most places.
While this is fine in binary form, it is really hard to work with for humans. 
Therefore we use names instead.

The glyph names are either extracted from the `CFF ` table or the `post` table, or are derived from a Unicode `cmap` table. 
In the latter case the Adobe Glyph List is used to calculate names based on Unicode values. 
If all of these methods fail, names are invented based on GlyphID (eg `glyph00142`)

It is possible that different glyphs use the same name. 
If this happens, we force the names to be unique by appending `#n` to the name (`n` being an integer number.)
The original names are being kept, so this has no influence on a "round tripped" font.

Because the order in which glyphs are stored inside the binary font is important, we maintain an ordered list of glyph names in the font.

### Other Tools

Commands for inspecting, merging and subsetting fonts are also available:

```sh
pyftinspect ;
pyftmerge ;
pyftsubset ;
```

### fontTools Python Module

The fontTools python module provides a convenient way to programmatically edit font files.

```py
>>> from fontTools.ttLib import TTFont
>>> font = TTFont('/path/to/font.ttf')
>>> font
<fontTools.ttLib.TTFont object at 0x10c34ed50>
>>>
```

A selection of sample python programs is in the [Snippets](https://github.com/behdad/fonttools/blob/master/Snippets/) directory. 

### Development Community

TTX/FontTools development is ongoing in an active community of developers, that includes professional developers employed at major software corporations and type foundries as well as hobbyists. 

Feature requests and bug reports are always welcome at <https://github.com/behdad/fonttools/issues/>

The best place for discussions about TTX from an end-user perspective as well as TTX/FontTools development is the <https://groups.google.com/d/forum/fonttools> mailing list.
You can also email Behdad privately at <behdad@behdad.org>

### History

The fontTools project was started by Just van Rossum in 1999, and was maintained as an open source project at <http://sourceforge.net/projects/fonttools/>.
In 2008, Paul Wise (pabs3) began helping Just with stability maintenance.
In 2013 Behdad Esfahbod began a friendly fork, thoroughly reviewing the codebase and making changes at <https://github.com/behdad/fonttools> to add new features and support for new font formats.

### Acknowledgements

In alphabetical order:

Olivier Berten,
Samyak Bhuta,
Erik van Blokland, 
Petr van Blokland, 
Jelle Bosma, 
Sascha Brawer,
Tom Byrer,
Frédéric Coiffier,
Vincent Connare, 
Dave Crossland,
Simon Daniels, 
Behdad Esfahbod,
Behnam Esfahbod,
Hannes Famira, 
Sam Fishman,
Matt Fontaine,
Yannis Haralambous, 
Greg Hitchcock, 
Jeremie Hornus,
Khaled Hosny,
John Hudson,
Denis Jacquerye,
Jack Jansen, 
Tom Kacvinsky, 
Jens Kutilek,
Antoine Leca, 
Werner Lemberg, 
Tal Leming,
Peter Lofting, 
Cosimo Lupo,
Project Mashabow,
Dave Opstad, 
Laurence Penney, 
Roozbeh Pournader,
Garret Rieger,
Read Roberts, 
Guido van Rossum, 
Just van Rossum, 
Andreas Seidel, 
Georg Seifert,
Miguel Sousa,
Adam Twardoch,
Adrien Tétar,
Vitaly Volkov,
Paul Wise.

### Copyrights

Copyright (c) 1999-2004 Just van Rossum, LettError (just@letterror.com)  
See [LICENSE.txt](LICENSE.txt) for the full license.

Copyright (c) 2000 BeOpen.com. 
All Rights Reserved.

Copyright (c) 1995-2001 Corporation for National Research Initiatives. 
All Rights Reserved.

Copyright (c) 1991-1995 Stichting Mathematisch Centrum, Amsterdam. 
All Rights Reserved.

Have fun!
