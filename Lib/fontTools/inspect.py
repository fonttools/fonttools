# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod

"""GUI font inspector.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import misc, ttLib, cffLib
try:
    from gi import pygtkcompat
except ImportError:
    pygtkcompat = None

if pygtkcompat is not None:
    pygtkcompat.enable()
    pygtkcompat.enable_gtk(version='3.0')
import gtk
import sys


class Row(object):
	def __init__(self, parent, index, key, value, font):
		self._parent = parent
		self._index = index
		self._key = key
		self._value = value
		self._font = font

		if isinstance(value, ttLib.TTFont):
			self._add_font(value)
			return

		if not isinstance(value, basestring):
			# Try sequences
			is_sequence = True
			try:
				len(value)
				iter(value)
				# It's hard to differentiate list-type sequences
				# from dict-type ones.  Try fetching item 0.
				value[0]
			except (TypeError, AttributeError, KeyError, IndexError):
				is_sequence = False
			if is_sequence:
				self._add_list(key, value)
				return
		if hasattr(value, '__dict__'):
			self._add_object(key, value)
			return
		if hasattr(value, 'items'):
			self._add_dict(key, value)
			return

		if isinstance(value, basestring):
			self._value_str = '"'+value+'"'
			self._children = []
			return

		# Everything else
		self._children = []

	def _filter_items(self):
		items = []
		for k,v in self._items:
			if isinstance(v, ttLib.TTFont):
				continue
			if k in ['reader', 'file', 'tableTag', 'compileStatus', 'recurse']:
				continue
			if isinstance(k, basestring) and k[0] == '_':
				continue
			items.append((k,v))
		self._items = items

	def _add_font(self, font):
		self._items = [(tag,font[tag]) for tag in font.keys()]

	def _add_object(self, key, value):
		# Make sure item is decompiled
		try:
			value.asdf # Any better way?!
		except (AttributeError, KeyError, TypeError, ttLib.TTLibError):
			pass
		if isinstance(value, ttLib.getTableModule('glyf').Glyph):
			# Glyph type needs explicit expanding to be useful
			value.expand(self._font['glyf'])
		if isinstance(value, misc.psCharStrings.T2CharString):
			try:
				value.decompile()
			except TypeError:  # Subroutines can't be decompiled
				pass
		if isinstance(value, cffLib.BaseDict):
			for k in value.rawDict.keys():
				getattr(value, k)
		if isinstance(value, cffLib.Index):
			# Load all items
			for i in range(len(value)):
				value[i]
			# Discard offsets as should not be needed anymore
			if hasattr(value, 'offsets'):
				del value.offsets

		self._value_str = value.__class__.__name__
		if isinstance(value, ttLib.tables.DefaultTable.DefaultTable):
			self._value_str += ' (%d Bytes)' % self._font.reader.tables[key].length
		self._items = sorted(value.__dict__.items())
		self._filter_items()

	def _add_dict(self, key, value):
		self._value_str = '%s of %d items' % (value.__class__.__name__, len(value))
		self._items = sorted(value.items())

	def _add_list(self, key, value):
		if len(value) and len(value) <= 32:
			self._value_str = str(value)
		else:
			self._value_str = '%s of %d items' % (value.__class__.__name__, len(value))
		self._items = list(enumerate(value))

	def __len__(self):
		if hasattr(self, '_children'):
			return len(self._children)
		if hasattr(self, '_items'):
			return len(self._items)
		assert False

	def _ensure_children(self):
		if hasattr(self, '_children'):
			return
		children = []
		for i,(k,v) in enumerate(self._items):
			children.append(Row(self, i, k, v, self._font))
		self._children = children
		del self._items

	def __getitem__(self, n):
		if n >= len(self):
			return None
		if not hasattr(self, '_children'):
			self._children = [None] * len(self)
		c = self._children[n]
		if c is None:
			k,v = self._items[n]
			c = self._children[n] = Row(self, n, k, v, self._font)
			self._items[n] = None
		return c

	def get_parent(self):
		return self._parent

	def get_index(self):
		return self._index

	def get_key(self):
		return self._key

	def get_value(self):
		return self._value

	def get_value_str(self):
		if hasattr(self,'_value_str'):
			return self._value_str
		return str(self._value)

class FontTreeModel(gtk.GenericTreeModel):

	__gtype_name__ = 'FontTreeModel'

	def __init__(self, font):
		super(FontTreeModel, self).__init__()
		self._columns = (str, str)
		self.font = font
		self._root = Row(None, 0, "font", font, font)

	def on_get_flags(self):
		return 0

	def on_get_n_columns(self):
		return len(self._columns)

	def on_get_column_type(self, index):
		return self._columns[index]

	def on_get_iter(self, path):
		rowref = self._root
		while path:
			rowref = rowref[path[0]]
			path = path[1:]
		return rowref

	def on_get_path(self, rowref):
		path = []
		while rowref != self._root:
			path.append(rowref.get_index())
			rowref = rowref.get_parent()
		path.reverse()
		return tuple(path)

	def on_get_value(self, rowref, column):
		if column == 0:
			return rowref.get_key()
		else:
			return rowref.get_value_str()

	def on_iter_next(self, rowref):
		return rowref.get_parent()[rowref.get_index() + 1]

	def on_iter_children(self, rowref):
		return rowref[0]

	def on_iter_has_child(self, rowref):
		return bool(len(rowref))

	def on_iter_n_children(self, rowref):
		return len(rowref)

	def on_iter_nth_child(self, rowref, n):
		if not rowref: rowref = self._root
		return rowref[n]

	def on_iter_parent(self, rowref):
		return rowref.get_parent()

class Inspect(object):

	def _delete_event(self, widget, event, data=None):
		gtk.main_quit()
		return False

	def __init__(self, fontfile):

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("%s - pyftinspect" % fontfile)
		self.window.connect("delete_event", self._delete_event)
		self.window.set_size_request(400, 600)

		self.scrolled_window = gtk.ScrolledWindow()
		self.window.add(self.scrolled_window)

		self.font = ttLib.TTFont(fontfile, lazy=True)
		self.treemodel = FontTreeModel(self.font)
		self.treeview = gtk.TreeView(self.treemodel)
		#self.treeview.set_reorderable(True)

		for i in range(2):
			col_name = ('Key', 'Value')[i]
			col = gtk.TreeViewColumn(col_name)
			col.set_sort_column_id(-1)
			self.treeview.append_column(col)

			cell = gtk.CellRendererText()
			col.pack_start(cell, True)
			col.add_attribute(cell, 'text', i)

		self.treeview.set_search_column(1)
		self.scrolled_window.add(self.treeview)
		self.window.show_all()

def main(args=None):
	if args is None:
		args = sys.argv[1:]
	if len(args) < 1:
		print("usage: pyftinspect font...", file=sys.stderr)
		return 1
	for arg in args:
		Inspect(arg)
	gtk.main()

if __name__ == "__main__":
	sys.exit(main())
