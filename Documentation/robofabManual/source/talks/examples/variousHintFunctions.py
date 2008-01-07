#FLM: Various hint functions

# Paul van der Laan, 2005-05-31


from robofab.world import CurrentFont, CurrentGlyph


#  H I N T S  P E R  G L Y P H


# get vertical hints as collection of tuples
def getVHints(g):
	vh = g.naked().vhints
	lh = ()
	for n in range(0, len(vh)):
		hintPos = vh[n].position
		hintWidth = vh[n].width
		lh += (hintPos, hintWidth),
	return lh
	

# get horizontal hints as collection of tuples
def getHHints(g):
	hh = g.naked().hhints
	lh = ()
	for n in range(0, len(hh)):
		hintPos = hh[n].position
		hintWidth = hh[n].width
		lh += (hintPos, hintWidth),
	return lh


# clear all vertical hints
def clearVHints(g):
	vh = g.naked().vhints
	for n in range(0, len(vh)):
		del vh[0]
	g.update()


# clear all horizontal hints
def clearHHints(g):
	hh = g.naked().hhints
	for n in range(0, len(hh)):
		del hh[0]
	g.update()


# set vertical hints
def setVHints(g,lh):
	for n in range(0, len(lh)):
		hintPos = lh[n][0]
		hintWidth = lh[n][1]
		g.naked().vhints.append(Hint(hintPos,hintWidth))
	g.update()


# set horizontal hints
def setHHints(g,lh):
	for n in range(0, len(lh)):
		hintPos = lh[n][0]
		hintWidth = lh[n][1]
		g.naked().hhints.append(Hint(hintPos,hintWidth))
	g.update()



#  B L U E  Z O N E S


# get all blue zones as collection of tuples
def getBluezones(f):
	blueNum = f.naked().blue_values_num
	otherNum = f.naked().other_blues_num
	bl = ()
	for n in range(0, otherNum, 2):
		bl += (f.naked().other_blues[0][n], f.naked().other_blues[0][n+1]),
	for n in range(0, blueNum, 2):
		bl += (f.naked().blue_values[0][n], f.naked().blue_values[0][n+1]),
	return bl


# clear all blue zones
def clearBluezones(f):
	f.naked().blue_values_num = 0
	f.naked().other_blues_num = 0
	f.update()


# set blue zones
def setBluezones(f, l):
	# collect original blue zones
	blueNum = f.naked().blue_values_num
	otherNum = f.naked().other_blues_num
	bl = []
	for n in range(0, otherNum, 2):
		bl += (f.naked().other_blues[0][n], f.naked().other_blues[0][n+1]),
	for n in range(0, blueNum, 2):
		bl += (f.naked().blue_values[0][n], f.naked().blue_values[0][n+1]),
	# add new zones and sort
	bl += l
	bl.sort()
	# split into primary and secondary zones
	pz = []
	sz = []
	for z in bl:
		if z[1] < 0:
			sz += z,
		else:
			pz += z,
	# write to font
	f.naked().other_blues_num = len(sz)*2
	for n in range(0, len(sz)):
		f.naked().other_blues[0][n*2] = sz[n][0]
		f.naked().other_blues[0][n*2+1] = sz[n][1]
	f.naked().blue_values_num = len(pz)*2
	for n in range(0, len(pz)):
		f.naked().blue_values[0][n*2] = pz[n][0]
		f.naked().blue_values[0][n*2+1] = pz[n][1]
	f.update()



#  C O M M O N  S T E M S


# get vertical stems as collection of tuples
def getVStems(f):
	vNum = f.naked().stem_snap_v_num
	ls = ()
	for n in range(0, vNum):
		ls += f.naked().stem_snap_v[0][n],
	return ls


# get horizontal stems as collection of tuples
def getHStems(f):
	hNum = f.naked().stem_snap_h_num
	ls = ()
	for n in range(0, hNum):
		ls += f.naked().stem_snap_h[0][n],
	return ls


# clear all vertical stems
def clearVStems(f):
	f.naked().stem_snap_v_num = 0
	f.update()


# clear all horizontal stems
def clearHStems(f):
	f.naked().stem_snap_h_num = 0
	f.update()


# set vertical stems
def setVStems(f, l):
	# collect original vertical stems
	vNum = f.naked().stem_snap_v_num
	ls = []
	for n in range(0, vNum):
		ls += f.naked().stem_snap_v[0][n],
	# add new stems and sort
	ls += l
	ls.sort()
	# write to font
	f.naked().stem_snap_v_num = len(ls)
	for n in range(0, len(ls)):
		f.naked().stem_snap_v[0][n] = ls[n]
	f.update()


# set horizontal stems
def setHStems(f, l):
	# collect original horizontal stems
	hNum = f.naked().stem_snap_h_num
	ls = []
	for n in range(0, hNum):
		ls += f.naked().stem_snap_h[0][n],
	# add new stems and sort
	ls += l
	ls.sort()
	# write to font
	f.naked().stem_snap_h_num = len(ls)
	for n in range(0, len(ls)):
		f.naked().stem_snap_h[0][n] = ls[n]
	f.update()




g = CurrentGlyph()
f = CurrentFont()

if g:
	print ""
	print "Original vertical hints for glyph", g.name, ":", getVHints(g)
	clearVHints(g)
	setVHints(g,((100,40),(420,80)))
	print "New vertical hints for glyph", g.name, ":", getVHints(g)
	print ""
	print "Original horizontal hints for glyph", g.name, ":", getHHints(g)
	clearHHints(g)
	setHHints(g,((-280,40),(140,65),(660,-21)))
	print "New horizontal hints for glyph", g.name, ":", getHHints(g)
if f:
	print ""
	print "Original blue zones for font", f.info.fullName, ":", getBluezones(f)
	clearBluezones(f)
	setBluezones(f, ((-120,-100),(-16,0),(500,520),(660,680)))
	print "New blue zones for font", f.info.fullName, ":", getBluezones(f)
	print ""
	print "Original vertical stems for font", f.info.fullName, ":", getVStems(f)
	clearVStems(f)
	setVStems(f, (24,60,88))
	print "New vertical stems for font", f.info.fullName, ":", getVStems(f)
	print ""
	print "Original horizontal stems for font", f.info.fullName, ":", getHStems(f)
	clearHStems(f)
	setHStems(f, (50,75))
	print "New horizontal stems for font", f.info.fullName, ":", getHStems(f)

