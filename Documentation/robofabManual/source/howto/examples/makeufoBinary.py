# robofab manual
# 	Makeufo howto
#	Makeufo from a font binary examples


from robofab.tools.toolsAll import fontToUFO
from robofab.interface.all.dialogs import GetFile, PutFile

srcPath = GetFile('Select the source')
dstPath = PutFile('Save as...')

fontToUFO(srcPath, dstPath)
