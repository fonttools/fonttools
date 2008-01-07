# Een functie om een map met files door te zoeken op vfb files

def collectSources(root):
	files = []
	ext = ['.vfb']
	names = os.listdir(root)
	for n in names:
		if os.path.splitext(n)[1] in ext:
			files.append(os.path.join(root, n))
	return files
	
# dialog voor het selecteren van een folder
f = GetFolder()

if f is not None:
	paths = collectSources(f)
	
	for f in paths:
		font = None
		try:
			font = OpenFont(f)