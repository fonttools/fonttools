#FLM: Select accents

from robofab.world import CurrentFont

myFont = CurrentFont()

myFont.selection = ['grave', 'acute', 'dieresis', 'circumflex', 'tilde', 'macron', 'breve', 'dotaccent', 'ring', 'cedilla', 'hungarumlaut', 'ogonek', 'caron', 'commaaccent']