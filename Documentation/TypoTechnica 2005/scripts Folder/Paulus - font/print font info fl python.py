#FLM: Print all font info FL Python


f = fl.font

if f.file_name:
	print "File: " + str(f.file_name)
print "Number of glyphs: " + str(len(f))
	
print ""
if f.family_name:
	print "Family Name: " + str(f.family_name)
if f.weight:
	print "Weight: " + str(f.weight)	
if f.weight_code:
	print "Weight Code: " + str(f.weight_code)	
if f.width:
	print "Width: " + str(f.width)
if f.font_style:
	print "Style: " + str(f.font_style)
	# 1=italic, 32=bold, 64=regular
if f.style_name:
	print "Style Name: " + str(f.style_name)	
if f.font_name:
	print "Font Name: " + str(f.font_name)
if f.full_name:
	print "Full Name: " + str(f.full_name)
if f.menu_name:
	print "Menu Name: " + str(f.menu_name)
if f.apple_name:
	print "FOND Name: " + str(f.apple_name)
	
print ""
if f.pref_family_name:
	print "OT Family Name: " + str(f.pref_family_name)
if f.pref_style_name:
	print "OT Style Name: " + str(f.pref_style_name)
if f.mac_compatible:
	print "OT Mac Name: " + str(f.mac_compatible)
	
print ""
if f.year:
	print "Year: " + str(f.year)
if f.copyright:
	print "Copyright: " + str(f.copyright)
if f.trademark:
	print "Trademark: " + str(f.trademark)
if f.notice:
	print "Notice: " + str(f.notice)
	
print ""
if f.designer:
	print "Designer: " + str(f.designer)
if f.designer_url:
	print "Designer URL: " + str(f.designer_url)
if f.vendor_url:
	print "Vendor URL: " + str(f.vendor_url)

print ""
if f.version_major:
	print "Version: " + str(f.version_major)
if f.version_minor:
	print "Revision: " + str(f.version_minor)
if f.version:
	print "Version: " + str(f.version)
if f.tt_version:
	print "TrueType Version: " + str(f.tt_version)

print ""
if f.tt_u_id:
	print "TrueType Unique ID: " + str(f.tt_u_id)
if f.unique_id:
	print "Type 1 Unique ID: " + str(f.unique_id)
if f.vendor:
	print "TrueType Vendor Code: " + str(f.vendor)
	
print ""
if f.panose:
	print "PANOSE: " + str(f.panose)
	
print ""
if f.pcl_id:
	print "PCL ID: " + str(f.pcl_id)
if f.vp_id:
	print "VP ID: " + str(f.vp_id)
if f.ms_id:
	print "MS ID: " + str(f.ms_id)
	
print ""
if f.upm:
	print "UPM: " + str(f.upm)

print ""
if f.ascender:
	print "Ascender: " + str(f.ascender[0])
if f.descender:
	print "Descender: " + str(f.descender[0])
if f.cap_height:
	print "Cap Height: " + str(f.cap_height[0])
if f.x_height:
	print "X Height: " + str(f.x_height[0])
if f.italic_angle:
	print "Italic Angle: " + str(f.italic_angle)
if f.slant_angle:
	print "Slant Angle: " + str(f.slant_angle)
if f.underline_position:
	print "Underline: " + str(f.underline_position)
if f.underline_thickness:
	print "Thickness: " + str(f.underline_thickness)
print "Monospaced: " + str(f.is_fixed_pitch)

print ""
print "Microsoft Character Set: " + str(f.ms_charset)
if f.default_character:
	print "PFM Default Character: " + str(f.default_character)
if f.fond_id:
	print "Mac FOND ID: " + str(f.fond_id)


# if f.fontnames:
#	print "f.fontnames " + str(f.fontnames)
# if f.note:
#	print "f.note " + str(f.note)
# if f.pcl_chars_set:
#	print "f.pcl_chars_set " + str(f.pcl_chars_set)
# if f.default_width:
#	print "f.default_width " + str(f.default_width[0])

# if f.x_u_id_num:
#	print "f.x_u_id_num " + str(f.x_u_id_num)
# if f.x_u_id:
#	print "f.x_u_id " + str(f.x_u_id)


print "--- Done"
print ""
print ""
