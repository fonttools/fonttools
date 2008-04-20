#FLM: Import all UFOs in a folder

"""
	
	Import all UFOs in a folder
	
	Note this is a relatively dumb import script.
	
"""
from robofab.world import NewFont
from robofab.interface.mac.getFileOrFolder import GetFileOrFolder

from robofab.interface.all.dialogs import GetFolder
import os


def globUFO(dir, filter=None):
	"""Collect paths for all ufos in dir.
	Check for nested dirs.
	Optionally, select only ufos which match a filter string.
	"""
	ufo = []
	names = os.listdir(dir)
	for n in names:
		p = os.path.join(dir, n)
		if n[-4:] == ".ufo":
			if filter is not None:
				if dir.find(filter) <> -1:
					ufo.append(p)
			else:
				ufo.append(p)
			continue
		if os.path.isdir(p):
			ufo += globUFO(p, filter)
	return ufo

dir = GetFolder()
ufo = globUFO(dir)

for path in ufo:
	font = NewFont()
	font.readUFO(path, doProgress=True)
	font.update()
	vfbPath = path[:-4] + ".vfb"
	font.save(vfbPath)
print 'DONE!'
