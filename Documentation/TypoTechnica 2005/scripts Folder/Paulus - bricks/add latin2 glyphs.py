from robofab.world import CurrentFont

myFont = CurrentFont()

myGlyphs = ['Amacron', 'amacron', 'Aogonek', 'aogonek', 'Ccaron', 'ccaron', 'Cacute', 'cacute', 'Zacute', 'zacute', 'Dcaron', 'dcaron', 'Emacron', 'emacron', 'Edotaccent', 'edotaccent', 'Ecaron', 'ecaron', 'Eogonek', 'eogonek', 'gcommaaccent', 'Iogonek', 'iogonek', 'Imacron', 'imacron', 'Kcommaaccent', 'Lcommaaccent', 'lcommaaccent', 'Lcaron', 'lcaron', 'Lacute', 'lacute', 'Ncommaaccent', 'ncommaaccent', 'Nacute', 'nacute', 'Ncaron', 'ncaron', 'Ohungarumlaut', 'ohungarumlaut', 'Omacron', 'omacron', 'Racute', 'racute', 'Rcaron', 'rcaron', 'Rcommaaccent', 'rcommaaccent', 'Sacute', 'sacute', 'Tcaron', 'tcaron', 'Umacron', 'umacron', 'Uring', 'uring', 'Uhungarumlaut', 'uhungarumlaut', 'Uogonek', 'uogonek', 'kcommaaccent', 'Zdotaccent', 'zdotaccent', 'Gcommaaccent', 'commaaccent', 'Abreve', 'Scedilla', 'abreve', 'scedilla', 'Tcommaaccent', 'tcommaaccent', 'Gbreve', 'gbreve', 'Idotaccent', 'Dcroat', 'dcroat', 'Scommaaccent', 'scommaaccent', 'uni021A', 'uni021B']

for myGlyph in myGlyphs:
	if not myFont.has_key(myGlyph):
		myFont.newGlyph(myGlyph)
myFont.update()
print "done"