TTX 1.0 alpha 6 -- Mac notes


U S E R   I N T E R F A C E

To decompile a TrueType font and dump it in XML format:

- Drop a TrueType file (a Windows TTF, or a Mac suitcase) onto TTX. It
will decompile the font and write it out as an XML text file. If you
dropped a Mac suitcase containing multiple TT fonts onto TTX, it will
generate an XML file for each font. The default destination for XML
files is the folder "XML output" inside the TTX folder. Files will be
silently overwritten.

*** to change the default locations for converted files, you have to
edit the "TTX preferences" file ***

To convert a XML file into a TrueType font:

- Drop an XML file onto TTX, it will parse the source, compile it and
write it into the "TrueType output" folder. By default, a Mac suitcase
will ge generated. ***This will fail if the font does not contain 'name'
table entries for the Macintosh platform.*** You can change the output
format to "flat" by setting the "makesuitcases" field in the "TTX
preferences" file to "0".


S Y S T E M   R E Q U I R E M E N T S

This version of TTX only works on PowerMacs, running MacOS 7.5 or
higher. Preferably a fairly fast machine.


T A B L E   S U P P O R T

TTX currently fully supports these tables:

cvt, gasp, head, hhea, hmtx, loca, name, maxp, OS/2, LTSH and the VTT
private tables TSI0, TSI1, TSI2, TSI3 and TSI5

The glyf table is fully supported, but it will not disassemble the
instructions; it dumps them as hex.

The following tables are partially supported: post (format 1.0 and 2.0
only, other formats *may* cause TTX to choke) cmap (format 0, 4 and 6,
other formats dumped as hex) kern (format 0 only, other formats dumped
as hex)

Tables (or subtables) that TTX does not (yet) know about will be written
out in hexadecimal form, so they won't get lost during the conversion.


N O T E   A B O U T   G L Y P H   N A M E S   A N D   I N D I C E S

TrueType fonts use glyph indices to refer to glyphs in most places.
While this is fine in binary form, it is really hard to work with for
humans. Therefore we use names instead.

The names are derived from what is found in the 'post' table. It is
possible that different glyphs use the same PS name. If this happens, we
force the names to be unique by appending "#n" to the name (n being an
integer number). The original PS names will still be maintained by the
'post' table, so even though we use a different name internally, we are
still able to write the 'post' table back in original form.

Because the order in which glyphs are stored inside the TT font is
important, the 'glyf' table keeps a list of glyph names.


I C O N   D E S I G N

Hannes Famira
