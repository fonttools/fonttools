#FLM: Export Current Font to UFO Format

"""
	Export the current font to UFO format. 

"""

from robofab.world import CurrentFont

f = CurrentFont()
if f.path is None:
	from robofab.interface.all.dialogs import PutFile
	path = PutFile("Please choose a name for the .ufo")
	if path is None:
		path = -1  # signal the code below the user has cancelled
else:
	# writeUFO() will firgure out the destination .ufo path
	path = None
if path != -1:
	f.writeUFO(path, doProgress=True)
	print 'DONE!'
