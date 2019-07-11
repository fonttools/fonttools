from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.DefaultTable import DefaultTable

font_path = "myfont.ttf"
output_path = "myfont_patched.ttf"

table_tag = "DSIG"


# Get raw table data from the source font

font = TTFont(font_path)
raw_data = font.getTableData(table_tag)


# Do something with the raw table data
# This example just sets an empty DSIG table.

raw_data = b"\0\0\0\1\0\0\0\0"


# Write the data back to the font

# We could re-use the existing table when the source and target font are
# identical, but let's make a new empty table to be more universal.
table = DefaultTable(table_tag)
table.data = raw_data

# Add the new table back into the source font and save under a new name.
font[table_tag] = table
font.save(output_path)
