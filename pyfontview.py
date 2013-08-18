#!/usr/bin/python

import pygtk
pygtk.require('2.0')
import gtk
import sys

import fontTools.ttx
import fontTools.ttLib
import fontTools.cffLib

class FontTreeStoreBuilder:

	def __init__(self, treestore):
		self.ts = treestore


class Row(object):
	def __init__(self, parent, index, key, value):
		self._parent = parent
		self._index = index
		self._key = key
		self._value = value

		if isinstance(value, fontTools.ttx.TTFont):
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
			except TypeError:
				is_sequence = False
			except AttributeError:
				is_sequence = False
			except KeyError:
				is_sequence = False
			except IndexError:
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
			if isinstance(v, fontTools.ttx.TTFont):
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
			getattr(value, "asdf")
		except AttributeError:
			pass
		if isinstance(value, fontTools.ttLib.getTableModule('glyf').Glyph):
			# Glyph type needs explicit expanding to be useful
			value.expand(self.font['glyf'])
		if isinstance(value, fontTools.cffLib.Index):
			# Load all items
			for i in range(len(value)):
				value[i]
			# Discard offsets as should not be needed anymore
			if hasattr(value, 'offsets'):
				del value.offsets

		self._value_str = value.__class__.__name__
		self._items = sorted(value.__dict__.items())
		self._filter_items()

	def _add_dict(self, key, value):
		self._value_str = '%s of %d items' % (value.__class__.__name__, len(value))
		self._items = sorted(value.items())
		self._filter_items()

	def _add_list(self, key, value):
		if len(value) and len(value) <= 32:
			self._value_str = str(value)
		else:
			self._value_str = '%s of %d items' % (value.__class__.__name__,
							      len(value))
		self._items = enumerate(value)
		self._filter_items()

	def __len__(self):
		self._ensure_children()
		return len(self._children)

	def get_parent(self):
		return self._parent

	def _ensure_children(self):
		if hasattr(self, '_children'):
			return
		children = []
		for i,(k,v) in enumerate(self._items):
			children.append(Row(self, i, k, v))
		self._children = children
		del self._items

	def get_children(self):
		self._ensure_children()
		return self._children

	def get_children(self):
		self._ensure_children()
		return self._children

	def get_nth_child(self, n):
		self._ensure_children()
		if n < len(self._children):
			return self._children[n]
		else:
			return None

	def get_key(self):
		return self._key

	def get_value(self):
		return self._value

	def get_value_str(self):
		if hasattr(self, '_value_str'):
			return self._value_str
		return str(self._value)

	def get_iter(self, path):
		if not path:
			return self
		return self.get_nth_child(path[0]).get_iter(path[1:])

	def iter_next(self):
		if not self._parent:
			return None
		return self._parent.get_nth_child(self._index + 1)

	def get_path(self):
		if not self._parent: return ()
		return self._parent.get_path() + (self._index,)

class FontTreeModel(gtk.GenericTreeModel):

	__gtype_name__ = 'FontTreeModel'

	def __init__(self, font):
		super(FontTreeModel, self).__init__()
		self._columns = (str, str)
		self.font = font
		self._root = Row(None, 0, "font", font)

	def on_get_flags(self):
		return 0

	def on_get_n_columns(self):
		return len(self._columns)

	def on_get_column_type(self, index):
		return self._columns[index]

	def on_get_iter(self, path):
		return self._root.get_iter(path)

	def on_get_path(self, rowref):
		return rowref.get_path()

	def on_get_value(self, rowref, column):
		if column == 0:
			return rowref.get_key()
		else:
			return rowref.get_value_str()

	def on_iter_next(self, rowref):
		return rowref.iter_next()

	def on_iter_children(self, rowref):
		return rowref.get_nth_child(0)

	def on_iter_has_child(self, rowref):
		return bool(len(rowref))

	def on_iter_n_children(self, rowref):
		return len(rowref)

	def on_iter_nth_child(self, rowref, n):
		if not rowref: rowref = self._root
		return rowref.get_nth_child(n)

	def on_iter_parent(self, rowref):
		return rowref.get_parent()

class PyFontView:

	def delete_event(self, widget, event, data=None):
		gtk.main_quit()
		return False

	def __init__(self, fontfile):

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("%s - PyFontView" % fontfile)
		self.window.connect("delete_event", self.delete_event)
		self.window.set_size_request(400, 600)

		self.scrolled_window = gtk.ScrolledWindow()
		self.window.add(self.scrolled_window)

		self.font = fontTools.ttx.TTFont(fontfile)
		self.treemodel = FontTreeModel(self.font)
		self.treeview = gtk.TreeView(self.treemodel)
		#self.treeview.set_reorderable(True)

		for i in range(2):

			col = gtk.TreeViewColumn('Column %d' % i)

			self.treeview.append_column(col)

			cell = gtk.CellRendererText()
			col.pack_start(cell, True)

			col.add_attribute(cell, 'text', i)

			col.set_sort_column_id(i)

		self.treeview.set_search_column(1)
		self.scrolled_window.add(self.treeview)
		self.window.show_all()

def main(args=None):
	if args == None: args = sys.argv
	if len(args) < 2:
		print >>sys.stderr, "usage: %s font..." % args[0]
		sys.exit(1)
	for arg in args[1:]:
		viewer = PyFontView(arg)
	gtk.main()

if __name__ == "__main__":
	main()
